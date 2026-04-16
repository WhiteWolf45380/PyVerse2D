from __future__ import annotations

from ..._rendering import Pipeline
from ._point import PointLight
from ._cone import ConeLight

import ctypes
import math
import pyglet.gl as gl
from pyglet.graphics.shader import Shader, ShaderProgram

_BUCKETS = (8, 16, 32, 64, 128)
_LUT_SIZE = 256

def _get_bucket(count: int) -> int:
    for bucket in _BUCKETS:
        if count <= bucket:
            return bucket
    return count

_VERT = """
#version 330 core
layout(location = 0) in vec2 in_position;
layout(location = 1) in vec2 in_uv;
out vec2 v_uv;
void main() {
    gl_Position = vec4(in_position, 0.0, 1.0);
    v_uv = in_uv;
}
"""

_FRAG_AMBIENT = """
#version 330 core
uniform sampler2D u_texture;
uniform float u_ambient;
in vec2 v_uv;
out vec4 out_color;
void main() {
    vec4 pixel = texture(u_texture, v_uv);
    out_color = vec4(pixel.rgb * u_ambient, pixel.a);
}
"""

_FRAG_TINT = """
#version 330 core
uniform sampler2D u_texture;
uniform vec3 u_tint;
uniform float u_strength;
in vec2 v_uv;
out vec4 out_color;
void main() {
    vec4 pixel = texture(u_texture, v_uv);
    out_color = vec4(mix(pixel.rgb, pixel.rgb * u_tint, u_strength), pixel.a);
}
"""

def _build_frag_points(max_lights: int) -> str:
    return f"""
#version 330 core
uniform sampler2D u_texture;
uniform float u_ambient;
uniform int u_count;
uniform vec2 u_positions[{max_lights}];
uniform float u_radii[{max_lights}];
uniform vec3 u_colors[{max_lights}];
uniform float u_intensities[{max_lights}];
uniform sampler2D u_lut_atlas;

in vec2 v_uv;
out vec4 out_color;

void main() {{
    vec4 pixel = texture(u_texture, v_uv);
    vec2 frag = gl_FragCoord.xy;
    vec3 light_accum = vec3(0.0);

    for (int i = 0; i < u_count; i++) {{
        float dist = distance(frag, u_positions[i]);
        float normalized = clamp(dist / u_radii[i], 0.0, 1.0);
        float row = (float(i) + 0.5) / float({max_lights});
        float falloff = texture(u_lut_atlas, vec2(1.0 - normalized, row)).r;
        light_accum += u_colors[i] * u_intensities[i] * falloff;
    }}

    light_accum = 1.0 - exp(-light_accum * u_light_scale);
    vec3 lit = pixel.rgb * max(vec3(u_ambient), light_accum);
    out_color = vec4(lit, pixel.a);
}}
"""

def _build_frag_cones(max_lights: int) -> str:
    return f"""
#version 330 core
uniform sampler2D u_texture;
uniform float u_ambient;
uniform int u_count;
uniform vec2 u_positions[{max_lights}];
uniform vec2 u_directions[{max_lights}];
uniform float u_radii[{max_lights}];
uniform float u_inner_angles[{max_lights}];
uniform float u_outer_angles[{max_lights}];
uniform vec3 u_colors[{max_lights}];
uniform float u_intensities[{max_lights}];
uniform sampler2D u_lut_atlas;

in vec2 v_uv;
out vec4 out_color;

void main() {{
    vec4 pixel = texture(u_texture, v_uv);
    vec2 frag = gl_FragCoord.xy;
    vec3 light_accum = vec3(0.0);

    for (int i = 0; i < u_count; i++) {{
        vec2 to_frag = frag - u_positions[i];
        float dist = length(to_frag);

        float t = clamp(dist / u_radii[i], 0.0, 1.0);
        float row = (float(i) + 0.5) / float({max_lights});
        float radial_falloff;

        if (u_cone_radii[i] <= 0.0001) {{
            radial_falloff = 1.0;
        }} else {{
            float t = clamp(dist / u_cone_radii[i], 0.0, 1.0);
            radial_falloff = texture(u_cone_lut, vec2(1.0 - t, row)).r;
        }}

        float angle = acos(clamp(dot(normalize(to_frag), u_directions[i]), -1.0, 1.0));
        float inner = min(u_cone_inner_angles[i], u_cone_outer_angles[i]);
        float outer = max(u_cone_inner_angles[i], u_cone_outer_angles[i]);

        float angular_falloff = 1.0 - smoothstep(inner, outer, angle);

        light_accum += u_colors[i] * u_intensities[i] * radial_falloff * angular_falloff;
    }}

    light_accum = 1.0 - exp(-light_accum * u_light_scale);
    vec3 lit = pixel.rgb * max(vec3(u_ambient), light_accum);
    out_color = vec4(lit, pixel.a);
}}
"""

def _build_frag_points_cones(max_points: int, max_cones: int) -> str:
    return f"""
#version 330 core
uniform sampler2D u_texture;
uniform float u_ambient;

uniform int u_point_count;
uniform vec2 u_point_positions[{max_points}];
uniform float u_point_radii[{max_points}];
uniform vec3 u_point_colors[{max_points}];
uniform float u_point_intensities[{max_points}];
uniform sampler2D u_point_lut;

uniform int u_cone_count;
uniform vec2 u_cone_positions[{max_cones}];
uniform vec2 u_cone_directions[{max_cones}];
uniform float u_cone_radii[{max_cones}];
uniform float u_cone_inner_angles[{max_cones}];
uniform float u_cone_outer_angles[{max_cones}];
uniform vec3 u_cone_colors[{max_cones}];
uniform float u_cone_intensities[{max_cones}];
uniform sampler2D u_cone_lut;

in vec2 v_uv;
out vec4 out_color;

void main() {{
    vec4 pixel = texture(u_texture, v_uv);
    vec2 frag = gl_FragCoord.xy;
    vec3 light_accum = vec3(0.0);

    for (int i = 0; i < u_point_count; i++) {{
        float dist = distance(frag, u_point_positions[i]);
        float normalized = clamp(dist / u_point_radii[i], 0.0, 1.0);
        float row = (float(i) + 0.5) / float({max_points});
        float falloff = texture(u_point_lut, vec2(1.0 - normalized, row)).r;
        light_accum += u_point_colors[i] * u_point_intensities[i] * falloff;
    }}

    for (int i = 0; i < u_cone_count; i++) {{
        vec2 to_frag = frag - u_cone_positions[i];
        float dist = length(to_frag);
        float t = clamp(dist / u_cone_radii[i], 0.0, 1.0);
        float row = (float(i) + 0.5) / float({max_cones});
        float radial_falloff;

        if (u_cone_radii[i] <= 0.0001) {{
            radial_falloff = 1.0;
        }} else {{
            float t = clamp(dist / u_cone_radii[i], 0.0, 1.0);
            radial_falloff = texture(u_cone_lut, vec2(1.0 - t, row)).r;
        }}

        float angle = acos(clamp(dot(normalize(to_frag), u_cone_directions[i]), -1.0, 1.0));
        float inner = min(u_cone_inner_angles[i], u_cone_outer_angles[i]);
        float outer = max(u_cone_inner_angles[i], u_cone_outer_angles[i]);

        float angular_falloff = 1.0 - smoothstep(inner, outer, angle);

        light_accum += u_cone_colors[i] * u_cone_intensities[i] * radial_falloff * angular_falloff;
    }}

    light_accum = 1.0 - exp(-light_accum * u_light_scale);
    vec3 lit = pixel.rgb * max(vec3(u_ambient), light_accum);
    out_color = vec4(lit, pixel.a);
}}
"""

# ======================================== RENDERER ========================================

class LightRenderer:
    """Renderer de lumière"""
    __slots__ = ("_active_points", "_active_cones")

    _tint_program: ShaderProgram = None
    _ambient_only_program: ShaderProgram = None
    _point_programs: dict[int, ShaderProgram] = {}
    _cone_programs: dict[int, ShaderProgram] = {}
    _point_cone_programs: dict[tuple[int, int], ShaderProgram] = {}

    def __init__(self):
        self._active_points: list[PointLight] = []
        self._active_cones: list[ConeLight] = []

    @classmethod
    def _get_tint_program(cls) -> ShaderProgram:
        if cls._tint_program is None:
            cls._tint_program = ShaderProgram(Shader(_VERT, 'vertex'), Shader(_FRAG_TINT, 'fragment'))
        return cls._tint_program

    @classmethod
    def _get_ambient_only_program(cls) -> ShaderProgram:
        if cls._ambient_only_program is None:
            cls._ambient_only_program = ShaderProgram(Shader(_VERT, 'vertex'), Shader(_FRAG_AMBIENT, 'fragment'))
        return cls._ambient_only_program

    @classmethod
    def _get_point_program(cls, max_lights: int) -> ShaderProgram:
        if max_lights not in cls._point_programs:
            cls._point_programs[max_lights] = ShaderProgram(Shader(_VERT, 'vertex'), Shader(_build_frag_points(max_lights), 'fragment'))
        return cls._point_programs[max_lights]

    @classmethod
    def _get_cone_program(cls, max_lights: int) -> ShaderProgram:
        if max_lights not in cls._cone_programs:
            cls._cone_programs[max_lights] = ShaderProgram(Shader(_VERT, 'vertex'), Shader(_build_frag_cones(max_lights), 'fragment'))
        return cls._cone_programs[max_lights]

    @classmethod
    def _get_point_cone_program(cls, max_points: int, max_cones: int) -> ShaderProgram:
        key = (max_points, max_cones)
        if key not in cls._point_cone_programs:
            cls._point_cone_programs[key] = ShaderProgram(Shader(_VERT, 'vertex'), Shader(_build_frag_points_cones(max_points, max_cones), 'fragment'))
        return cls._point_cone_programs[key]

    @classmethod
    def clear_shader_cache(cls) -> None:
        cls._tint_program = None
        cls._ambient_only_program = None
        cls._point_programs.clear()
        cls._cone_programs.clear()
        cls._point_cone_programs.clear()

    @staticmethod
    def _build_lut_atlas(lights: list, bucket: int) -> gl.GLuint:
        atlas = (ctypes.c_float * (_LUT_SIZE * bucket))()
        for i, light in enumerate(lights):
            for j in range(_LUT_SIZE):
                t = j / (_LUT_SIZE - 1)
                if light.falloff is None:                   
                    atlas[i * _LUT_SIZE + j] = 1.0 - t
                else:
                    atlas[i * _LUT_SIZE + j] = light.falloff(t)
        tex = gl.GLuint()
        gl.glGenTextures(1, ctypes.byref(tex))
        gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_R32F, _LUT_SIZE, bucket, 0, gl.GL_RED, gl.GL_FLOAT, atlas)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
        return tex

    # ======================================== RENDER AMBIENT ========================================
    def render_ambient(self, pipeline: Pipeline, ambient: float, light_scale: float, points: list[PointLight], cones: list[ConeLight]) -> None:
        has_points = bool(points)
        has_cones = bool(cones)

        if not has_points and not has_cones:
            if ambient < 1.0:
                pipeline.apply_shader(self._get_ambient_only_program(), u_ambient=ambient)
            return

        if has_points and has_cones:
            self._render_points_cones(pipeline, ambient, light_scale, points, cones)
        elif has_points:
            self._render_points(pipeline, ambient, light_scale, points)
        else:
            self._render_cones(pipeline, ambient, light_scale, cones)

    # ======================================== POINTS ONLY ========================================
    def _render_points(self, pipeline: Pipeline, ambient: float, light_scale: float, points: list[PointLight]) -> None:
        bucket = _get_bucket(len(points))
        program = self._get_point_program(bucket)
        fb_scale = pipeline.window.framebuffer_scale

        atlas_tex = self._build_lut_atlas(points, bucket)

        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, atlas_tex)

        positions = [(0.0, 0.0)] * bucket
        radii = [1.0] * bucket
        colors = [(1.0, 1.0, 1.0)] * bucket
        intensities = [0.0] * bucket

        for i, light in enumerate(points):
            fx, fy = pipeline.world_to_framebuffer(light.x, light.y)
            positions[i] = (float(fx), float(fy))
            radii[i] = light.radius * pipeline.ppu * fb_scale
            colors[i] = light.color.rgb
            intensities[i] = light.intensity

        pipeline.apply_shader(program,
            u_ambient=ambient,
            u_light_scale=light_scale,
            u_count=len(points),
            u_positions=positions,
            u_radii=radii,
            u_colors=colors,
            u_intensities=intensities,
            u_lut_atlas=1,
        )

        gl.glDeleteTextures(1, ctypes.byref(atlas_tex))

    # ======================================== CONES ONLY ========================================
    def _render_cones(self, pipeline: Pipeline, ambient: float, light_scale: float, cones: list[ConeLight]) -> None:
        bucket = _get_bucket(len(cones))
        program = self._get_cone_program(bucket)
        fb_scale = pipeline.window.framebuffer_scale

        atlas_tex = self._build_lut_atlas(cones, bucket)
    
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, atlas_tex)

        positions = [(0.0, 0.0)] * bucket
        directions = [(1.0, 0.0)] * bucket
        radii = [1.0] * bucket
        inner_angles = [0.0] * bucket
        outer_angles = [0.0] * bucket
        colors = [(1.0, 1.0, 1.0)] * bucket
        intensities = [0.0] * bucket

        for i, light in enumerate(cones):
            fx, fy = pipeline.world_to_framebuffer(light.x, light.y)
            dir_fb = pipeline.world_to_framebuffer_dir_normalized(light.direction.x, light.direction.y)
            positions[i] = (float(fx), float(fy))
            directions[i] = dir_fb
            radii[i] = light.radius * pipeline.ppu * fb_scale
            inner_angles[i] = math.radians(light.get_inner_angle())
            outer_angles[i] = math.radians(light.get_outer_angle())
            colors[i] = light.color.rgb
            intensities[i] = light.intensity

        pipeline.apply_shader(program,
            u_ambient=ambient,
            u_light_scale=light_scale,
            u_count=len(cones),
            u_positions=positions,
            u_directions=directions,
            u_radii=radii,
            u_inner_angles=inner_angles,
            u_outer_angles=outer_angles,
            u_colors=colors,
            u_intensities=intensities,
            u_lut_atlas=1,
        )

        gl.glDeleteTextures(1, ctypes.byref(atlas_tex))

    # ======================================== POINTS + CONES ========================================
    def _render_points_cones(self, pipeline: Pipeline, ambient: float, light_scale: float, points: list[PointLight], cones: list[ConeLight]) -> None:
        bp = _get_bucket(len(points))
        bc = _get_bucket(len(cones))
        program = self._get_point_cone_program(bp, bc)
        fb_scale = pipeline.window.framebuffer_scale

        point_atlas = self._build_lut_atlas(points, bp)
        cone_atlas = self._build_lut_atlas(cones, bc)

        # Points
        p_positions = [(0.0, 0.0)] * bp
        p_radii = [1.0] * bp
        p_colors = [(1.0, 1.0, 1.0)] * bp
        p_intensities = [0.0] * bp

        for i, light in enumerate(points):
            fx, fy = pipeline.world_to_framebuffer(light.x, light.y)
            p_positions[i] = (float(fx), float(fy))
            p_radii[i] = light.radius * pipeline.ppu * fb_scale
            p_colors[i] = light.color.rgb
            p_intensities[i] = light.intensity

        # Cones
        c_positions = [(0.0, 0.0)] * bc
        c_directions = [(1.0, 0.0)] * bc
        c_radii = [1.0] * bc
        c_inner_angles = [0.0] * bc
        c_outer_angles = [0.0] * bc
        c_colors = [(1.0, 1.0, 1.0)] * bc
        c_intensities = [0.0] * bc

        for i, light in enumerate(cones):
            fx, fy = pipeline.world_to_framebuffer(light.x, light.y)
            dir_fb = pipeline.world_to_framebuffer_dir_normalized(light.direction.x, light.direction.y)
            c_positions[i] = (float(fx), float(fy))
            c_directions[i] = dir_fb
            c_radii[i] = light.radius * pipeline.ppu * fb_scale
            c_inner_angles[i] = math.radians(light.get_inner_angle())
            c_outer_angles[i] = math.radians(light.get_outer_angle())
            c_colors[i] = light.color.rgb
            c_intensities[i] = light.intensity

        scene_fbo = pipeline.fbo
        temp_fbo = pipeline._get_temp_fbo(scene_fbo)

        temp_fbo.bind()
        temp_fbo.clear()
        program.use()

        # Uniforms scalaires
        program['u_ambient'] = ambient
        program['u_light_scale'] = light_scale
        program['u_point_count'] = len(points)
        program['u_cone_count'] = len(cones)
        program['u_point_positions'] = p_positions
        program['u_point_radii'] = p_radii
        program['u_point_colors'] = p_colors
        program['u_point_intensities'] = p_intensities
        program['u_cone_positions'] = c_positions
        program['u_cone_directions'] = c_directions
        program['u_cone_radii'] = c_radii
        program['u_cone_inner_angles'] = c_inner_angles
        program['u_cone_outer_angles'] = c_outer_angles
        program['u_cone_colors'] = c_colors
        program['u_cone_intensities'] = c_intensities

        # Texture 0 : scene FBO
        program['u_texture'] = 0
        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, scene_fbo.texture_id)

        # Texture 1 : point LUT
        program['u_point_lut'] = 1
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, point_atlas)

        # Texture 2 : cone LUT
        program['u_cone_lut'] = 2
        gl.glActiveTexture(gl.GL_TEXTURE2)
        gl.glBindTexture(gl.GL_TEXTURE_2D, cone_atlas)

        pipeline.quad.draw_raw()

        # Blit final
        scene_fbo.bind()
        scene_fbo.clear()
        pipeline.quad.blit(temp_fbo.texture_id)
        scene_fbo.bind()

        gl.glDeleteTextures(1, ctypes.byref(point_atlas))
        gl.glDeleteTextures(1, ctypes.byref(cone_atlas))

    # ======================================== TINT ========================================
    def render_tint(self, pipeline: Pipeline, tint: tuple[float, float, float], strength: float) -> None:
        pipeline.apply_shader(self._get_tint_program(), u_tint=tint, u_strength=strength)