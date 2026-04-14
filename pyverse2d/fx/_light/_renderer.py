# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._rendering import Pipeline
from ...abc import LightSource
from ._point import PointLight

import ctypes
import pyglet.gl as gl
from pyglet.graphics.shader import Shader, ShaderProgram

# ======================================== BUCKETS ========================================
_BUCKETS = (8, 16, 32, 64, 128)
_LUT_SIZE = 256

def _get_bucket(count: int) -> int:
    for bucket in _BUCKETS:
        if count <= bucket:
            return bucket
    return count

# ======================================== SHADERS ========================================
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

def _build_frag_ambient_points(max_lights: int) -> str:
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

    vec3 lit = pixel.rgb * max(vec3(u_ambient), light_accum);
    out_color = vec4(lit, pixel.a);
}}
"""

# ======================================== RENDERER ========================================
class LightRenderer:
    """Renderer de lumière"""
    __slots__ = ()

    _tint_program: ShaderProgram = None
    _ambient_point_programs: dict[int, ShaderProgram] = {}

    # ======================================== PROGRAMS ========================================
    @classmethod
    def _get_tint_program(cls) -> ShaderProgram:
        if cls._tint_program is None:
            cls._tint_program = ShaderProgram(
                Shader(_VERT, 'vertex'),
                Shader(_FRAG_TINT, 'fragment'),
            )
        return cls._tint_program

    @classmethod
    def _get_ambient_point_program(cls, max_lights: int) -> ShaderProgram:
        if max_lights not in cls._ambient_point_programs:
            cls._ambient_point_programs[max_lights] = ShaderProgram(
                Shader(_VERT, 'vertex'),
                Shader(_build_frag_ambient_points(max_lights), 'fragment'),
            )
        return cls._ambient_point_programs[max_lights]

    # ======================================== LUT ATLAS ========================================
    @staticmethod
    def _build_lut_atlas(lights: list[PointLight], bucket: int) -> gl.GLuint:
        """Construit une texture 2D atlas : une ligne par lumière, paddé jusqu'au bucket"""
        atlas = (ctypes.c_float * (_LUT_SIZE * bucket))()
        for i, light in enumerate(lights):
            for j in range(_LUT_SIZE):
                atlas[i * _LUT_SIZE + j] = 1.0 if light.falloff is None else light.falloff(j / (_LUT_SIZE - 1))

        tex = gl.GLuint()
        gl.glGenTextures(1, ctypes.byref(tex))
        gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
        gl.glTexImage2D(
            gl.GL_TEXTURE_2D, 0, gl.GL_R32F,
            _LUT_SIZE, bucket, 0,
            gl.GL_RED, gl.GL_FLOAT, atlas,
        )
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
        return tex

    # ======================================== AMBIENT + POINTS ========================================
    def render_ambient(self, pipeline: Pipeline, ambient: float, sources: set[LightSource]) -> None:
        """Applique la luminosité ambiante et les sources lumineuses

        Args:
            pipeline: pipeline de rendu
            ambient: luminosité ambiante [0, 1]
            sources: ensemble des sources de lumière
        """
        point_lights = [s for s in sources if isinstance(s, PointLight) and s.is_enabled()]
        bucket = _get_bucket(len(point_lights)) if point_lights else 1
        program = self._get_ambient_point_program(bucket)

        # Atlas LUT
        atlas_tex = self._build_lut_atlas(point_lights, bucket)
        gl.glActiveTexture(gl.GL_TEXTURE1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, atlas_tex)

        # Données par lumière (paddées jusqu'au bucket)
        fb_scale = pipeline.window.framebuffer_scale_x
        positions   = [(0.0, 0.0)] * bucket
        radii       = [1.0]        * bucket
        colors      = [(1.0, 1.0, 1.0)] * bucket
        intensities = [0.0]        * bucket

        for i, light in enumerate(point_lights):
            fx, fy = pipeline.world_to_framebuffer(light.x, light.y)
            positions[i]   = (float(fx), float(fy))
            radii[i]       = light.radius * pipeline.ppu * fb_scale
            colors[i]      = light.color.rgb
            intensities[i] = light.intensity

        pipeline.apply_shader(program,
            u_ambient     = ambient,
            u_count       = len(point_lights),
            u_positions   = positions,
            u_radii       = radii,
            u_colors      = colors,
            u_intensities = intensities,
            u_lut_atlas   = 1,
        )

        # Cleanup atlas
        gl.glDeleteTextures(1, ctypes.byref(atlas_tex))

    # ======================================== TINT ========================================
    def render_tint(self, pipeline: Pipeline, tint: tuple[float, float, float], strength: float) -> None:
        """Applique une teinte colorée

        Args:
            pipeline: pipeline de rendu
            tint: couleur RGB normalisée [0.0, 1.0]
            strength: force de la teinte [0, 1]
        """
        pipeline.apply_shader(self._get_tint_program(), u_tint=tint, u_strength=strength)