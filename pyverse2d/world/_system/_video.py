# ======================================== IMPORTS ========================================
from __future__ import annotations

import av
import queue
import threading
import time
import pyglet.image as _image
import pyglet.media as _media
import pyglet.media.codecs as _codecs

from ..._internal import expect, HasPosition, profile_section
from ..._rendering import PygletTextureRenderer, Pipeline
from ...abc import System
from .._world import World
from .._component import Transform, VideoPlayer

# ======================================== CONSTANTS ========================================
# Capacité maximale de la queue de frames vidéo
_VIDEO_BUFFER: int = 16

# Format audio de sortie
_AUDIO_RATE: int = 44100
_AUDIO_CH: int = 2

# Taille maximale du buffer audio interne, en octets.
# Correspond à 2 secondes de PCM s16 stéréo à 44 100 Hz.
# Au-delà, push() droppe silencieusement : le decode attend OpenAL.
_AUDIO_BUFFER_MAX: int = 2 * _AUDIO_RATE * _AUDIO_CH * 2  # ≈ 352 Ko

# ======================================== AUDIO FEED ========================================
class _AudioFeed(_media.StreamingSource):
    """Source audio streaming thread-safe pour pyglet/OpenAL

    Reçoit du PCM brut depuis le thread de décodage via ``push()``, et le fournit à OpenAL via ``get_audio_data()``.

    Le buffer interne est borné à ``_AUDIO_BUFFER_MAX`` octets (≈ 2 s de PCM).
    Si le buffer est plein, ``push()`` droppe silencieusement les données excédentaires.

    Args:
        sample_rate: fréquence d'échantillonnage (défaut : ``_AUDIO_RATE``)
        channels: nombre de canaux audio (défaut : ``_AUDIO_CH``)
    """

    def __init__(self, sample_rate: int = _AUDIO_RATE, channels: int = _AUDIO_CH) -> None:
        self.audio_format = _codecs.AudioFormat(
            channels=channels,
            sample_size=16,
            sample_rate=sample_rate,
        )
        self._buf: bytearray = bytearray()
        self._lock: threading.Lock = threading.Lock()
        self._done: bool = False
        self._underruns: int = 0
        self._drops: int = 0

    def push(self, data: bytes) -> None:
        """Pousse du PCM brut dans le buffer interne

        Si le buffer atteint ``_AUDIO_BUFFER_MAX``, les données sont droppées
        et ``_drops`` est incrémenté — évite toute croissance mémoire non bornée.

        Args:
            data: octets PCM s16 stéréo à bufferiser
        """
        with self._lock:
            if len(self._buf) + len(data) > _AUDIO_BUFFER_MAX:
                self._drops += 1
                return
            self._buf.extend(data)

    def mark_done(self) -> None:
        """Signale la fin définitive du flux

        Doit être appelé APRÈS ``join()`` du thread de décodage pour garantir
        qu'aucune donnée n'arrive plus après le signal.
        """
        with self._lock:
            self._done = True

    @property
    def underruns(self) -> int:
        """Nombre d'underruns détectés depuis la création du feed"""
        return self._underruns

    @property
    def drops(self) -> int:
        """Nombre de chunks audio droppés pour cause de buffer saturé"""
        return self._drops

    def get_audio_data(self, num_bytes: int, compensation_time: float = 0.0):
        """Fournit ``num_bytes`` octets PCM à OpenAL

        En cas de buffer vide :

        * si le flux est terminé : retourne ``None`` (fin de source)
        * sinon : retourne du silence et incrémente le compteur d'underruns

        Args:
            num_bytes: quantité d'octets demandée
            compensation_time: ignoré (API pyglet)

        Returns:
            ``AudioData`` prêt pour OpenAL, ou ``None`` en fin de flux
        """
        with self._lock:
            available = len(self._buf)
            if available == 0:
                if self._done:
                    return None
                self._underruns += 1
                data = bytes(num_bytes)
            else:
                n = min(num_bytes, available)
                data = bytes(self._buf[:n])
                del self._buf[:n]
                if n < num_bytes:
                    data += bytes(num_bytes - n)

        sr = self.audio_format.sample_rate
        ch = self.audio_format.channels
        duration = num_bytes / (sr * ch * 2)
        return _codecs.AudioData(data, len(data), 0.0, duration, [])

# ======================================== SYSTEM ========================================
class VideoSystem(System):
    """Système gérant les composants ``VideoPlayer``

    Args:
        origin: référentiel de position pour le calcul d'atténuation spatiale *(typiquement la caméra)*
    """
    __slots__ = (
        "_origin",
        "_threads", "_sprites",
    )

    order = 95
    exclusive = True
    renderable = True

    def __init__(self, origin: HasPosition):
        # Vérifications
        if __debug__:
            expect(origin, HasPosition)

        # Attributs publiques
        self._origin: HasPosition = origin

        # Attributs internes
        self._threads: dict[int, threading.Thread] = {}
        self._sprites: dict[int, PygletTextureRenderer] = {}

    # ======================================== CONTRACT ========================================
    def __repr__(self) -> str:
        return (
            f"VideoSystem(origin={(self._origin.x, self._origin.y)}, "
            f"active={len(self._threads)})"
        )

    # ======================================== PROPERTIES ========================================
    @property
    def origin(self) -> HasPosition:
        """Référentiel d'écoute des sons

        Cette propriété définie le point de référence spatial pour l'atténuation du volume sonore.
        """
        return self._origin

    @origin.setter
    def origin(self, value: HasPosition) -> None:
        if __debug__:
            expect(value, HasPosition)
        self._origin = value

    # ======================================== LIFE CYCLE ========================================
    @profile_section("world.video.update")
    def update(self, world: World, dt: float) -> None:
        """Met à jour tous les ``VideoPlayer`` actifs du monde

        Args:
            world: monde ECS courant
            dt: delta-temps depuis la dernière mise à jour
        """
        active_eids: set[int] = set()

        for entity in world.query(VideoPlayer):
            vp: VideoPlayer = entity.video_player
            tr: Transform   = entity.transform
            eid = entity.id
            active_eids.add(eid)

            # Initialisation si une vidéo vient d'être chargée
            if vp._video and not vp._initialized:
                self._load_player(eid, vp)

            # Pas en lecture active
            if not vp.is_playing() or vp.is_paused():
                continue

            # Volume spatial basé sur la distance à l'origine
            distance = ((tr.x - self._origin.x) ** 2 + (tr.y - self._origin.y) ** 2) ** 0.5
            spatial_volume = self._compute_volume(vp, distance)

            self._update_audio(vp, spatial_volume)
            self._consume_frames(vp)
            self._check_signals(eid, vp)

        # Nettoyage des threads dont l'entité n'existe plus dans le monde
        for eid in list(self._threads):
            if eid not in active_eids:
                thread = self._threads.pop(eid)
                thread.join(timeout=1.0)

    @profile_section("world.video.draw")
    def draw(self, world: World, pipeline: Pipeline) -> None:
        """Dessine la texture courante de chaque ``VideoPlayer``

        Crée le renderer au premier appel, puis le met à jour à chaque frame.

        Args:
            world: monde ECS courant
            pipeline: pipeline de rendu cible
        """
        for entity in world.query(VideoPlayer):
            eid = entity.id
            vp  = entity.video_player
            tr  = entity.transform

            renderer = self._sprites.get(eid)
            if renderer is None:
                self._sprites[eid] = PygletTextureRenderer(
                    texture=vp.texture, transform=tr, offset=vp.offset,
                    width=vp.width, height=vp.height,
                    opacity=vp.opacity, z=vp.z, pipeline=pipeline,
                )
            else:
                renderer.update(
                    texture=vp.texture, transform=tr, offset=vp.offset,
                    width=vp.width, height=vp.height,
                    opacity=vp.opacity, z=vp.z,
                )

    # ======================================== PLAYER LIFECYCLE ========================================
    def _load_player(self, eid: int, vp: VideoPlayer) -> None:
        """Initialise toutes les ressources de décodage pour une entité

        Args:
            eid: identifiant de l'entité
            vp: composant ``VideoPlayer`` de l'entité
        """
        was_playing = vp._playing
        self._stop_player(eid, vp)

        # Durée totale
        try:
            with av.open(vp._video.path) as c:
                vs = next((s for s in c.streams if s.type == "video"), None)
                vp._duration = float(vs.duration * vs.time_base) if (vs and vs.duration) else None
        except Exception:
            vp._duration = None

        # Queue vidéo
        vp._frame_queue  = queue.Queue(maxsize=_VIDEO_BUFFER)
        vp._pending_frame = None

        # Events de contrôle du thread
        vp._stop_event   = threading.Event()
        vp._pause_event  = threading.Event()
        vp._pause_event.set()

        # Signaux de fin et de boucle
        vp._end_event    = threading.Event()
        vp._loop_event   = threading.Event()

        # Feed audio et player OpenAL
        vp._audio_feed   = _AudioFeed(_AUDIO_RATE, _AUDIO_CH)
        vp._audio_player = _media.Player()
        vp._audio_player.queue(vp._audio_feed)

        # Horloge : armée à 0.0 ici, réglée sur perf_counter() dans _update_audio()
        # au moment exact de player.play() — voir VideoPlayer.time.
        vp._play_start_wall = 0.0
        vp._pts_origin      = 0.0

        # Thread de décodage
        thread = threading.Thread(
            target=self._decode_loop,
            args=(
                vp._video.path,
                vp._frame_queue,
                vp._audio_feed,
                vp._stop_event,
                vp._pause_event,
                vp._end_event,
                vp._loop_event,
                vp._loop,
            ),
            daemon=True,
        )
        thread.start()
        vp._decode_thread = thread
        self._threads[eid] = thread

        vp._initialized   = True
        vp._playing       = was_playing
        vp._audio_started = False

    def _stop_player(self, eid: int, vp: VideoPlayer) -> None:
        """Arrête proprement la lecture et libère toutes les ressources

        Args:
            eid: identifiant de l'entité
            vp: composant ``VideoPlayer`` de l'entité
        """
        vp.stop()

        if vp._decode_thread is not None:
            vp._decode_thread.join(timeout=1.0)

        # mark_done APRÈS join : garantit qu'aucune donnée n'arrive plus dans le feed.
        if vp._audio_feed is not None:
            vp._audio_feed.mark_done()

        if vp._audio_player is not None:
            try:
                vp._audio_player.pause()
                vp._audio_player.delete()
            except Exception:
                pass
            vp._audio_player = None

        vp._audio_feed    = None
        vp._decode_thread = None
        vp._frame_queue   = None
        vp._pending_frame = None
        vp._stop_event    = None
        vp._pause_event   = None
        vp._end_event     = None
        vp._loop_event    = None
        vp._audio_started = False
        self._threads.pop(eid, None)

    # ======================================== SIGNALS ========================================
    def _check_signals(self, eid: int, vp: VideoPlayer) -> None:
        """Vérifie les signaux de fin et de boucle émis par le thread de décodage

        Args:
            eid: identifiant de l'entité
            vp: composant ``VideoPlayer`` de l'entité
        """
        if vp._loop_event is not None and vp._loop_event.is_set():
            vp._loop_event.clear()
            # Réinitialise l'horloge : les PTS repartent à 0 côté décodeur.
            vp._play_start_wall = time.perf_counter()
            vp._pts_origin      = 0.0
            vp._pending_frame   = None

        if vp._end_event is not None and vp._end_event.is_set():
            vp._end_event.clear()
            if vp._on_end:
                vp._on_end.trigger(vp, vp._video)
            self._stop_player(eid, vp)

    # ======================================== FRAMES ========================================
    def _consume_frames(self, vp: VideoPlayer) -> None:
        """Dépile et affiche les frames dont le PTS est échu

        Args:
            vp: composant ``VideoPlayer`` à mettre à jour
        """
        if vp._frame_queue is None:
            return

        now = vp.time
        if vp._pending_frame is not None:
            pts, w, h, data = vp._pending_frame
            if pts > now:
                return
            self._blit_frame(vp, w, h, data)
            vp._pending_frame = None

        last_eligible: tuple | None = None

        while True:
            try:
                item = vp._frame_queue.get_nowait()
            except queue.Empty:
                break

            pts, w, h, data = item

            if pts <= now:
                last_eligible = (pts, w, h, data)
            else:
                vp._pending_frame = item
                break

        if last_eligible is not None:
            _, w, h, data = last_eligible
            self._blit_frame(vp, w, h, data)

    @staticmethod
    def _blit_frame(vp: VideoPlayer, w: int, h: int, data: bytes) -> None:
        """Met à jour la texture GPU à partir des données d'une frame

        Réutilise la texture existante si les dimensions sont inchangées (``blit_into``).
        Crée une nouvelle texture uniquement à la première frame ou si la résolution change.

        Args:
            vp: composant ``VideoPlayer`` cible
            w: largeur de la frame en pixels
            h: hauteur de la frame en pixels
            data: données RGB brutes (24 bits par pixel, ligne de haut en bas)
        """
        img = _image.ImageData(w, h, "RGB", data, pitch=-w * 3)

        if vp._texture is not None and vp._texture.width == w and vp._texture.height == h:
            vp._texture.blit_into(img, 0, 0, 0)
        else:
            vp._texture = img.get_texture()

    # ======================================== AUDIO ========================================
    def _update_audio(self, vp: VideoPlayer, spatial_volume: float) -> None:
        """Met à jour le volume OpenAL et arme l'horloge au démarrage réel de l'audio

        Args:
            vp: composant ``VideoPlayer`` cible
            spatial_volume: volume final après atténuation spatiale
        """
        player = vp._audio_player
        if player is None:
            return

        if player.volume != spatial_volume:
            player.volume = spatial_volume

        if not vp._audio_started:
            try:
                player.play()
                # HORLOGE ARMÉE ICI — même instant que le démarrage OpenAL.
                vp._play_start_wall = time.perf_counter()
                vp._audio_started = True
            except Exception:
                pass

    # ======================================== SPATIAL VOLUME ========================================
    @staticmethod
    def _compute_volume(vp: VideoPlayer, distance: float) -> float:
        """Calcule le volume final après atténuation spatiale

        Args:
            vp: composant ``VideoPlayer``
            distance: distance en unités monde entre le ``Transform`` et l'``origin``

        Returns:
            Volume final dans l'intervalle *[0, base_volume]*
        """
        base = vp.volume * vp._video.volume
        if vp.outer_radius == 0.0 or distance <= vp.inner_radius:
            return base
        if distance > vp.outer_radius:
            return 0.0
        t = (distance - vp.inner_radius) / (vp.outer_radius - vp.inner_radius)
        return base * (1.0 - vp.falloff(t))

    # ======================================== DECODE ========================================
    @staticmethod
    def _decode_loop(
        path: str,
        frame_queue: queue.Queue,
        audio_feed: _AudioFeed,
        stop_event: threading.Event,
        pause_event: threading.Event,
        end_event: threading.Event,
        loop_event: threading.Event,
        loop: bool,
    ) -> None:
        """Thread de décodage AV

        Args:
            path: chemin vers le fichier vidéo
            frame_queue: queue de frames vidéo ``(pts, w, h, bytes)``
            audio_feed: feed PCM pour le player OpenAL
            stop_event: levé pour interrompre le thread immédiatement
            pause_event: effacé pendant la pause, levé à la reprise
            end_event: levé à la fin définitive de la lecture
            loop_event: levé avant chaque rebouclage
            loop: si ``True``, reboucle indéfiniment jusqu'à ``stop_event``
        """
        audio_resampler = av.AudioResampler(
            format="s16",
            layout="stereo",
            rate=_AUDIO_RATE,
        )

        while not stop_event.is_set():
            try:
                with av.open(path) as container:
                    video_stream = next((s for s in container.streams if s.type == "video"), None)
                    audio_stream = next((s for s in container.streams if s.type == "audio"), None)

                    if video_stream is None:
                        break

                    video_stream.thread_type = "AUTO"
                    streams = [video_stream]
                    if audio_stream is not None:
                        streams.append(audio_stream)

                    for packet in container.demux(*streams):
                        if stop_event.is_set():
                            return
                        pause_event.wait()
                        if stop_event.is_set():
                            return

                        for frame in packet.decode():
                            if stop_event.is_set():
                                return

                            if isinstance(frame, av.VideoFrame):
                                if frame.pts is None:
                                    continue
                                pts  = float(frame.pts * frame.time_base)
                                rgb  = frame.to_ndarray(format="rgb24")
                                h, w, _ = rgb.shape
                                data = rgb.tobytes()
                                while not stop_event.is_set():
                                    try:
                                        frame_queue.put((pts, w, h, data), timeout=0.05)
                                        break
                                    except queue.Full:
                                        continue

                            elif isinstance(frame, av.AudioFrame):
                                if frame.pts is None:
                                    continue
                                for rf in audio_resampler.resample(frame):
                                    if rf.pts is None:
                                        continue
                                    audio_feed.push(bytes(rf.planes[0]))

            except Exception as e:
                print(f"[decode_loop] crash: {type(e).__name__}: {e}")
                break

            if stop_event.is_set():
                return

            if loop:
                loop_event.set()
                audio_resampler = av.AudioResampler(
                    format="s16",
                    layout="stereo",
                    rate=_AUDIO_RATE,
                )
            else:
                end_event.set()
                break