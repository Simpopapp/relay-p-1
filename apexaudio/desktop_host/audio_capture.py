"""ApexAudio — captura WASAPI Loopback (downlink: PC ➔ celular).

Requisito do PRD §4.1: capturar o som de saída padrão do Windows em chunks de
10ms (1920B stereo 48kHz), com reamostragem quando o dispositivo nativo não é
48kHz e prioridade de thread time-critical.

Em máquinas sem WASAPI (Linux/sandbox ou sem áudio), `open_loopback_capture`
levanta `CaptureUnavailable` — o servidor continua de pé em modo silencioso
(quadros de silêncio) para não derrubar o túnel.
"""
from __future__ import annotations

import queue
from collections.abc import Callable
import threading
import time

import numpy as np

from . import config

FRAME_BYTES = config.DOWNLINK_FRAME_BYTES  # 1920


class CaptureUnavailable(RuntimeError):
    """Nenhum dispositivo de loopback utilizável nesta máquina."""


def _resample_to_48k(chunk: np.ndarray, native_rate: int) -> np.ndarray:
    """Reamostragem linear rápida para 48kHz (PRD §4.1)."""
    if native_rate == config.SAMPLE_RATE:
        return chunk
    n_out = int(round(chunk.shape[0] * config.SAMPLE_RATE / native_rate))
    x_out = np.linspace(0.0, chunk.shape[0] - 1, num=n_out)
    x_in = np.arange(chunk.shape[0], dtype=np.float64)
    out = np.empty((n_out, chunk.shape[1]), dtype=np.float64)
    for ch in range(chunk.shape[1]):
        out[:, ch] = np.interp(x_out, x_in, chunk[:, ch].astype(np.float64))
    return out


def _wasapi_frames():
    """Gerador interno usando pyaudiowpatch (WASAPI loopback exclusivo do Windows)."""
    import pyaudiowpatch as pw

    with pw.PyAudio() as pa:
        try:
            wasapi_info = pa.get_host_api_info_by_type(pw.paWASAPI)
            default_speakers = pa.get_device_info_by_index(
                wasapi_info["defaultOutputDevice"])
        except OSError as exc:
            raise CaptureUnavailable(str(exc)) from exc
        if not default_speakers.get("isLoopbackDevice"):
            for loopback in pa.get_loopback_device_info_generator():
                if default_speakers["name"] in loopback["name"]:
                    default_speakers = loopback
                    break
            else:
                raise CaptureUnavailable("nenhum dispositivo loopback encontrado")
        native_rate = int(default_speakers["defaultSampleRate"])
        channels = int(default_speakers["maxInputChannels"])
        frames_per_chunk = int(native_rate * config.FRAME_MS / 1000)
        stream = pa.open(
            format=pw.paInt16,
            channels=channels,
            rate=native_rate,
            frames_per_buffer=frames_per_chunk,
            input=True,
            input_device_index=int(default_speakers["index"]),
        )
        try:
            while True:
                raw = stream.read(frames_per_chunk, exception_on_overflow=False)
                block = np.frombuffer(raw, dtype=np.int16).reshape(-1, channels)
                block = _resample_to_48k(block, native_rate)
                yield block.reshape(-1).tobytes()[:FRAME_BYTES].ljust(FRAME_BYTES, b"\0")
        finally:
            stream.stop_stream()
            stream.close()


class LoopbackCapture:
    """Thread produtora: alimenta uma fila com chunks de 1920B a cada 10ms."""

    def __init__(self, max_queue: int = 64,
                 thread_initializer: Callable[[], None] | None = None):
        self._queue: "queue.Queue[bytes]" = queue.Queue(maxsize=max_queue)
        self._thread: threading.Thread | None = None
        self._running = threading.Event()
        self._silent = False
        self._thread_initializer = thread_initializer

    @property
    def silent_mode(self) -> bool:
        return self._silent

    def _run(self) -> None:
        # Best-effort setup (e.g. Windows thread priority) runs on the capture thread.
        if self._thread_initializer is not None:
            try:
                self._thread_initializer()
            except Exception:
                pass
        try:
            for chunk in _wasapi_frames():
                if not self._running.is_set():
                    break
                self._put(chunk)
        except (CaptureUnavailable, ImportError, OSError):
            # Missing devices/packages or a disconnected device must not kill the tunnel.
            self._silent = True
            self._silent_loop()

    def _silent_loop(self) -> None:
        """Modo silencioso: mantém o túnel vivo com quadros de silêncio."""
        zeros = b"\0" * FRAME_BYTES
        while self._running.is_set():
            self._put(zeros)
            time.sleep(config.FRAME_MS / 1000.0)

    def _put(self, chunk: bytes) -> None:
        # Política de overrun do host: descarta o mais antigo, nunca acumula atraso.
        if self._queue.full():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                pass
        self._queue.put_nowait(chunk)

    def start(self) -> None:
        self._running.set()
        self._thread = threading.Thread(
            target=self._run, name="apex-audio-capture", daemon=True)
        self._thread.start()

    def read_chunk(self, timeout: float = 0.1) -> bytes | None:
        try:
            return self._queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def stop(self) -> None:
        self._running.clear()
        if self._thread:
            self._thread.join(timeout=1.0)


def open_loopback_capture() -> LoopbackCapture:
    """Fábrica: prioridade best-effort sem monkey-patch do worker."""
    try:
        import win32process
    except ImportError:
        return LoopbackCapture(thread_initializer=None)

    def _raise_priority() -> None:
        try:
            import win32api
            import win32process
            handle = win32api.GetCurrentThread()
            win32process.SetThreadPriority(
                handle, win32process.THREAD_PRIORITY_TIME_CRITICAL)
        except Exception:
            pass

    return LoopbackCapture(thread_initializer=_raise_priority)
