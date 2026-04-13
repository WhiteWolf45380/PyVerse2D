# ======================================== IMPORTS ========================================
from __future__ import annotations

import pyglet.gl as gl

# ======================================== FBO ========================================
class Framebuffer:
    """
    Wrapper FBO OpenGL avec texture RGBA8 attachée.
    Utilisé comme cible de rendu intermédiaire dans le pipeline.
    """
    __slots__ = ("_fbo", "_texture", "_width", "_height")

    def __init__(self, width: int, height: int):
        self._width = width
        self._height = height

        # Texture RGBA8
        self._texture = (gl.GLuint * 1)()
        gl.glGenTextures(1, self._texture)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self._texture[0])
        gl.glTexImage2D(
            gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8,
            width, height, 0,
            gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None
        )
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)

        # FBO
        self._fbo = (gl.GLuint * 1)()
        gl.glGenFramebuffers(1, self._fbo)
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self._fbo[0])
        gl.glFramebufferTexture2D(
            gl.GL_FRAMEBUFFER, gl.GL_COLOR_ATTACHMENT0,
            gl.GL_TEXTURE_2D, self._texture[0], 0
        )

        assert gl.glCheckFramebufferStatus(gl.GL_FRAMEBUFFER) == gl.GL_FRAMEBUFFER_COMPLETE, \
            "Framebuffer incomplet"

        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

    # ======================================== PROPERTIES ========================================
    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def texture_id(self) -> int:
        return self._texture[0]

    # ======================================== INTERFACE ========================================
    def bind(self) -> None:
        """Rend dans ce FBO"""
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, self._fbo[0])

    def unbind(self) -> None:
        """Revient au framebuffer principal"""
        gl.glBindFramebuffer(gl.GL_FRAMEBUFFER, 0)

    def clear(self) -> None:
        """Efface le contenu du FBO (doit être bindé)"""
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

    def resize(self, width: int, height: int) -> None:
        """Redimensionne la texture — à appeler sur resize fenêtre"""
        self._width = width
        self._height = height
        gl.glBindTexture(gl.GL_TEXTURE_2D, self._texture[0])
        gl.glTexImage2D(
            gl.GL_TEXTURE_2D, 0, gl.GL_RGBA8,
            width, height, 0,
            gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, None
        )
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

    def delete(self) -> None:
        """Libère les ressources GPU"""
        gl.glDeleteFramebuffers(1, self._fbo)
        gl.glDeleteTextures(1, self._texture)