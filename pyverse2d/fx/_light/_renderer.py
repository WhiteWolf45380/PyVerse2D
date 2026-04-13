# ======================================== IMPORTS ========================================
from __future__ import annotations

from ..._rendering import Pipeline
from ..._rendering._fbo import Framebuffer

import pyglet.gl as gl
from pyglet.graphics.shader import Shader, ShaderProgram

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

_FRAG_AMBIENT = """
#version 330 core
uniform sampler2D u_texture;
uniform vec3 u_tint;
uniform float u_ambient;
in vec2 v_uv;
out vec4 out_color;
void main() {
    vec4 pixel = texture(u_texture, v_uv);
    out_color = vec4(pixel.rgb * u_tint * u_ambient, pixel.a);
}
"""

# ======================================== RENDERER ========================================
class LightRenderer:
    """Renderer de lumière

    Gère les effets lumineux via ping-pong FBO.
    """
    __slots__ = ("_temp_fbo",)

    _ambient_program: ShaderProgram = None

    def __init__(self):
        self._temp_fbo: Framebuffer = None   # ping-pong, lazy

    # ======================================== PROGRAMS ========================================
    @classmethod
    def _get_ambient_program(cls) -> ShaderProgram:
        if cls._ambient_program is None:
            cls._ambient_program = ShaderProgram(
                Shader(_VERT, 'vertex'),
                Shader(_FRAG_AMBIENT, 'fragment'),
            )
        return cls._ambient_program

    # ======================================== FBO ========================================
    def _get_temp_fbo(self, fbo: Framebuffer) -> Framebuffer:
        """Retourne un FBO temporaire aux bonnes dimensions (lazy + resize)"""
        if self._temp_fbo is None:
            self._temp_fbo = Framebuffer(fbo.width, fbo.height)
        elif self._temp_fbo.width != fbo.width or self._temp_fbo.height != fbo.height:
            self._temp_fbo.resize(fbo.width, fbo.height)
        return self._temp_fbo

    # ======================================== AMBIENT ========================================
    def render_ambient(self, pipeline: Pipeline, tint: tuple[int, int, int], ambient: float) -> None:
        """Applique la lumière ambiante multiplicative sur le FBO courant


        Args:
            pipeline: pipeline de rendu
            tint: couleur de teinte (r, g, b) en [0.0, 1.0]
            ambient: luminosité ambiante [0, 1]
        """
        scene_fbo = pipeline.fbo
        temp_fbo = self._get_temp_fbo(scene_fbo)

        # Rendu dans le temp_fbo
        temp_fbo.bind()
        temp_fbo.clear()

        program = self._get_ambient_program()
        program.use()
        program['u_tint'] = tint
        program['u_ambient'] = ambient
        program['u_texture'] = 0

        gl.glActiveTexture(gl.GL_TEXTURE0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, scene_fbo.texture_id)
        pipeline.quad.blit(scene_fbo.texture_id)

        # Recopie temp_fbo dans scene_fbo
        scene_fbo.bind()
        scene_fbo.clear()
        pipeline.quad.blit(temp_fbo.texture_id)

        # Rebind scene_fbo pour la suite
        scene_fbo.bind()