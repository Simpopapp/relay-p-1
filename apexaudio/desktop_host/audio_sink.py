"""ApexAudio — injeção do microfone reverso (uplink: celular ➔ PC).

Recebe quadros mono de 960B (48kHz/16-bit) decodificados pelo network_server e
escreve em um dispositivo de saída selecionado como "CABLE Input" / "VB-Audio
Virtual Cable" (PRD §4.2). Se o driver não existir, avisa claramente e mantém
a escuta ativa (os quadros são descartados até o driver aparecer).
"""
from __future__ import annotations

import threading

import numpy as np

from . import config

try:
    import sounddevice as sd
except Exception:  # pragma: no cover - sem portaudio no ambiente
    sd = None  # type: ignore[assignment]


def find_cable_device() -> int | None:
    """Índice do dispositivo 'CABLE Input' (VB-Audio), ou None se ausente."""
    if sd is None:
        return None
    try:
        devices = sd.query_devices()
    except Exception:
        return None
    for idx, dev in enumerate(devices):
        if dev.get("max_output_channels", 0) > 0 and any(
                name in str(dev.get("name", ""))
                for name in config.CABLE_DEVICE_NAMES):
            return idx
    return None


class UplinkSink:
    """Escreve o uplink mono 48kHz no dispositivo virtual (ou descarta)."""

    def __init__(self) -> None:
        self._stream = None
        self._lock = threading.Lock()
        self.device_index: int | None = None
        self.warnings: list[str] = []

    def start(self) -> None:
        self.device_index = find_cable_device()
        if sd is None:
            self.warnings.append(
                "sounddevice indisponível: uplink recebido será descartado")
            return
        if self.device_index is None:
            self.warnings.append(
                "VB-Audio Virtual Cable NÃO detectado — instale o driver "
                "(https://vb-audio.com/Cable/) e selecione 'CABLE Input' como "
                "microfone no Discord. A escuta permanece ativa.")
            return
        self._stream = sd.OutputStream(
            samplerate=config.SAMPLE_RATE,
            channels=config.UPLINK_CHANNELS,
            dtype="int16",
            device=self.device_index,
            blocksize=config.SAMPLES_PER_FRAME,
        )
        self._stream.start()

    def write_frame(self, mono_bytes: bytes) -> bool:
        """Escreve um quadro mono de 960B. False se não há destino de áudio."""
        if self._stream is None:
            return False
        with self._lock:
            self._stream.write(np.frombuffer(mono_bytes, dtype=np.int16))
        return True

    def stop(self) -> None:
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            finally:
                self._stream = None


def offer_cable_install(device_index, install=False, opener=None):
    """Offer official download without installing privileged drivers automatically."""
    if device_index is not None:
        return ''
    message = ('VB-Cable ausente; downlink continua ativo. Para instalar, use '
               '--install-cable ou https://vb-audio.com/Cable/')
    if install:
        import webbrowser
        (opener or webbrowser.open)('https://vb-audio.com/Cable/')
    return message
