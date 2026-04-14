# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._rendering import Pipeline
from ...abc import LightSource
from ._point import PointLight

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
uniform float u_luts[{max_lights}][{_LUT_SIZE}];

in vec2 v_uv;
out vec4 out_color;

void main() {{
    vec4 pixel = texture(u_texture, v_uv);
    vec2 frag = gl_FragCoord.xy;

    vec3 light_accum = vec3(0.0);

    for (int i = 0; i < u_count; i++) {{
        float dist = distance(frag, u_positions[i]);
        float normalized = clamp(dist / u_radii[i], 0.0, 1.0);
        int lut_index = int(normalized * float({_LUT_SIZE - 1}));
        float falloff = u_luts[i][lut_index];
        light_accum += u_colors[i] * u_intensities[i] * falloff;
    }}

    float brightness = max(u_ambient, length(light_accum) / 1.732);
    vec3 tinted = pixel.rgb * max(vec3(u_ambient), light_accum);
    out_color = vec4(tinted, pixel.a);
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

    # ======================================== LUT ========================================
    @staticmethod
    def _build_lut(falloff) -> list[float]:
        return [falloff(i / (_LUT_SIZE - 1)) for i in range(_LUT_SIZE)]

    # ======================================== AMBIENT + POINTS ========================================
    def render_ambient(self, pipeline: Pipeline, ambient: float, sources: set[LightSource]) -> None:
        """Applique la luminosité ambiante et les sources lumineuses

        Args:
            pipeline: pipeline de rendu
            ambient: luminosité ambiante [0, 1]
            sources: ensemble des sources de lumière
        """
        # Filtrage des PointLights actives
        point_lights = [s for s in sources if isinstance(s, PointLight) and s.is_enabled()]

        if not point_lights:
            # Pas de lights, shader ambient simple
            program = self._get_ambient_point_program(1)
            pipeline.apply_shader(program,
                u_ambient=ambient,
                u_count=0,
                u_positions=[(0.0, 0.0)],
                u_radii=[1.0],
                u_colors=[(1.0, 1.0, 1.0)],
                u_intensities=[0.0],
                u_luts=[[0.0] * _LUT_SIZE],
            )
            return

        # Bucket
        bucket = _get_bucket(len(point_lights))
        program = self._get_ambient_point_program(bucket)

        # Conversion world to framebuffer + rayon en pixels
        fb_scale = pipeline.window.framebuffer_scale

        positions = []
        radii = []
        colors = []
        intensities = []
        luts = []

        # Points lumineux
        for light in point_lights:
            fx, fy = pipeline.world_to_framebuffer(light.x, light.y)
            positions.append((fx, fy))
            radii.append(light.radius * pipeline.ppu * fb_scale)
            colors.append(light.color.rgb)
            intensities.append(light.intensity)
            luts.append(self._build_lut(light.falloff))

        # Padding jusqu'au bucket
        while len(positions) < bucket:
            positions.append((0.0, 0.0))
            radii.append(1.0)
            colors.append((1.0, 1.0, 1.0))
            intensities.append(0.0)
            luts.append([0.0] * _LUT_SIZE)

        pipeline.apply_shader(program,
            u_ambient=ambient,
            u_count=len(point_lights),
            u_positions=positions,
            u_radii=radii,
            u_colors=colors,
            u_intensities=intensities,
            u_luts=luts,
        )

    # ======================================== TINT ========================================
    def render_tint(self, pipeline: Pipeline, tint: tuple[float, float, float], strength: float) -> None:
        """Applique une teinte colorée

        Args:
            pipeline: pipeline de rendu
            tint: couleur RGB normalisée [0.0, 1.0]
            strength: force de la teinte [0, 1]
        """
        pipeline.apply_shader(self._get_tint_program(), u_tint=tint, u_strength=strength)