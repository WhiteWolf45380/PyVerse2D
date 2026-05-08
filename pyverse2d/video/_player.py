# ======================================== IMPORTS ========================================
from __future__ import annotations

from .._internal import over, expect, positive, CallbackList
from ..math import Point
from ._video import Video

import av
import pyglet.image as _image
import threading
import queue
import time
from numbers import Real
from typing import Callable, Any

# ======================================== CONSTANTS ========================================
_BUFFER_SIZE = 8

# ======================================== PROPERTIES ========================================
class VideoPlayer:
    """Lecteur vidéo monde"""
    __slots__ = (
        "_position", "_width", "_height",
        "_video", "_player",
        "_play_volume", "_loop", "_on_end",
        "_texture", "_frame_queue",
        "_decode_thread", "_stop_event",
        "_pts_origin", "_clock_origin",
        "_duration", "_paused", "_pause_event",
    )

    def __init__(self, position: Point, width: int, height: int):
        # Transtypage et vérifications
        position = Point(position)
        width = int(width)
        height = int(height)

        if __debug__:
            over(width, 0, include=False)
            over(height, 0, include=False)

        # Attributs publiques
        self._position: Point = position
        self._width: int = width
        self._height: int = height

        # Attributs internes
        self._video: Video | None = None
        self._play_volume: float = 1.0
        self._loop: bool = False
        self._on_end: CallbackList | None = None

        # Décodage
        self._texture = None
        self._frame_queue: queue.Queue | None = None
        self._decode_thread: threading.Thread | None = None
        self._stop_event: threading.Event | None = None
        self._pause_event: threading.Event | None = None

        # Clock
        self._pts_origin: float = 0.0
        self._clock_origin: float = 0.0
        self._duration: float | None = None
        self._paused: bool = False

    # ======================================== PROPERTIES ========================================
    @property
    def position(self) -> Point:
        """Position
        
        La position peut être un objet ``Point`` ou n'importe quel tuple ``(x, y)``.
        """
        return self._position

    @position.setter
    def position(self, value: Point) -> None:
        self._position.x, self._position.y = value

    @property
    def x(self) -> float:
        """Position horizontale"""
        return self._position.x

    @x.setter
    def x(self, value: Real) -> None:
        self._position.x = float(value)

    @property
    def y(self) -> float:
        """Position verticale"""
        return self._position.y

    @y.setter
    def y(self, value: Real) -> None:
        self._position.y = float(value)

    @property
    def width(self) -> int:
        """Largeur du lecteur"""
        return self._width

    @width.setter
    def width(self, value: int) -> None:
        value = int(value)
        if __debug__:
            over(value, 0, include=False)
        self._width = value

    @property
    def height(self) -> int:
        """Hauteur du lecteur"""
        return self._height

    @height.setter
    def height(self, value: int) -> None:
        value = int(value)
        if __debug__:
            over(value, 0, include=False)
        self._height = value

    @property
    def volume(self) -> float:
        """Volume de lecture"""
        return self._play_volume

    @volume.setter
    def volume(self, value: Real) -> None:
        value = float(value)
        if __debug__:
            positive(value)
        self._play_volume = value

    @property
    def on_end(self) -> CallbackList:
        """Hook de fin de lecture"""
        if self._on_end is None:
            self._on_end = CallbackList()
        return self._on_end

    @on_end.setter
    def on_end(self, value: Callable | None) -> None:
        self._on_end = value

    @property
    def texture(self):
        """Frame courante comme texture pyglet (None si inactif)"""
        return self._texture

    @property
    def time(self) -> float:
        """Curseur temporelle de lecture"""
        if not self.is_playing():
            return 0.0
        if self._paused:
            return self._pts_origin
        return self._pts_origin + (time.perf_counter() - self._clock_origin)

    @property
    def duration(self) -> float | None:
        """Durée de la vidéo chargée"""
        return self._duration

    @property
    def time_remaining(self) -> float | None:
        """Temps restant de la vidéo chargée"""
        if self._duration is None:
            return None
        return max(0.0, self._duration - self.time)

    # ======================================== PREDICATES ========================================
    def is_playing(self) -> bool:
        """Vérifie qu'une vidéo soit en cours de lecture"""
        return self._decode_thread is not None and self._decode_thread.is_alive()

    def is_paused(self) -> bool:
        """Vérifie que la lecture soit en pause"""
        return self._paused

    def is_loaded(self) -> bool:
        """Vérifie qu'une vidéo soit chargée"""
        return self._video is not None

    # ======================================== INTERFACE ========================================
    def load(self, video: Video) -> None:
        """Charge une vidéo
        
        Args:
            video: ``Video`` à charger 
        """
        if __debug__:
            expect(video, Video)
        self.stop()
        self._video = video

    def play(
        self,
        video: Video | None = None,
        volume: Real = 1.0,
        loop: bool = False,
    ) -> None:
        """Lance la lecture
        
        Args:
            video: ``Video`` à lire *(par défaut celle chargée)*
            volume: volume de lecture
            loop: relancement automatique de la vidéo
        """
        if __debug__:
            expect(video, (Video, type(None)))
            positive(float(volume))

        if video is not None:
            self._video = video
        if self._video is None:
            return

        self.stop()

        self._play_volume = float(volume)
        self._loop = bool(loop)
        self._paused = False

        # Récupère la durée via PyAV sans garder le container ouvert
        with av.open(self._video.path) as _c:
            vs = next((s for s in _c.streams if s.type == "video"), None)
            self._duration = float(vs.duration * vs.time_base) if (vs and vs.duration) else None

        self._frame_queue = queue.Queue(maxsize=_BUFFER_SIZE)
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # non-bloquant au départ

        self._pts_origin = 0.0
        self._clock_origin = time.perf_counter()

        self._decode_thread = threading.Thread(
            target=self._decode_loop,
            args=(self._video.path, self._frame_queue, self._stop_event, self._pause_event, self._loop),
            daemon=True,
        )
        self._decode_thread.start()

    def pause(self) -> None:
        if not self.is_playing() or self._paused:
            return
        self._pts_origin = self.time   # sauvegarde le PTS courant
        self._pause_event.clear()      # bloque le thread de décodage
        self._paused = True

    def unpause(self) -> None:
        if not self._paused:
            return
        self._clock_origin = time.perf_counter()  # rebase l'horloge
        self._pause_event.set()
        self._paused = False

    def stop(self) -> None:
        if self._stop_event is not None:
            self._stop_event.set()
        if self._pause_event is not None:
            self._pause_event.set()  # débloque le thread pour qu'il puisse se terminer
        if self._decode_thread is not None:
            self._decode_thread.join(timeout=1.0)
            self._decode_thread = None
        self._frame_queue = None
        self._stop_event = None
        self._pause_event = None
        self._paused = False

    def clear(self) -> None:
        self.stop()
        self._video = None
        self._texture = None
        self._duration = None

    def tick(self, dt: float) -> None:
        """Actualisation — à appeler chaque frame depuis le thread principal

        Consomme les frames prêtes de la queue et met à jour la texture.
        Déclenche le callback ``on_end`` si la vidéo est terminée.

        Args:
            dt: delta-time
        """
        if self._frame_queue is None or self._paused:
            return

        now = self.time
        last_ready: bytes | None = None
        last_pts: float = 0.0
        last_size: tuple[int, int] = (0, 0)

        # Draine toutes les frames dont le PTS est dépassé,
        # ne garde que la plus récente pour éviter l'accumulation
        while True:
            try:
                pts, w, h, data = self._frame_queue.get_nowait()
            except queue.Empty:
                break

            if pts <= now:
                last_ready = data
                last_pts = pts
                last_size = (w, h)
            else:
                # Frame trop en avance : on la remet et on arrête
                self._frame_queue.put((pts, w, h, data))
                break

        if last_ready is not None:
            w, h = last_size
            img = _image.ImageData(w, h, "RGB", last_ready, pitch=-w * 3)
            self._texture = img.get_texture()
            self._pts_origin = last_pts
            self._clock_origin = time.perf_counter()

        # Fin de lecture : queue vide + thread mort
        if not self.is_playing() and (self._frame_queue is None or self._frame_queue.empty()):
            if self._on_end is not None:
                self._on_end(self)
            self.stop()

    # ======================================== INTERNALS ========================================
    @staticmethod
    def _decode_loop(
        path: str,
        frame_queue: queue.Queue,
        stop_event: threading.Event,
        pause_event: threading.Event,
        loop: bool,
    ) -> None:
        """Thread de décodage — ne touche jamais au thread principal

        Args:
            path: chemin vers le fichier vidéo
            frame_queue: queue de frames décodées
            stop_event: signal d'arrêt
            pause_event: signal de pause
            loop: boucle si True
        """
        while not stop_event.is_set():
            with av.open(path) as container:
                video_stream = next((s for s in container.streams if s.type == "video"), None)
                if video_stream is None:
                    break

                # Optimisation : décodage multi-thread côté FFmpeg
                video_stream.thread_type = "AUTO"

                for frame in container.decode(video=0):
                    if stop_event.is_set():
                        return

                    # Pause : attend que pause_event soit set
                    pause_event.wait()
                    if stop_event.is_set():
                        return

                    pts = float(frame.pts * frame.time_base)

                    # Conversion RGB24 — plus rapide que RGBA pour pyglet
                    rgb_frame = frame.to_ndarray(format="rgb24")
                    h, w, _ = rgb_frame.shape
                    data = rgb_frame.tobytes()

                    # Bloque si la queue est pleine (back-pressure naturelle)
                    while not stop_event.is_set():
                        try:
                            frame_queue.put((pts, w, h, data), timeout=0.05)
                            break
                        except queue.Full:
                            continue

            if not loop or stop_event.is_set():
                break