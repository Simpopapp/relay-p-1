"""ApexAudio — constantes globais do sistema (fonte única de verdade).

Derivadas do PRD (prd-project1.md §3, §6). Qualquer módulo que precisar de
portas, taxas ou tamanhos de buffer importa daqui — nunca hardcode local.
"""
from __future__ import annotations

# --- Identidade do protocolo -------------------------------------------------
MAGIC: int = 0xAA55
PROTOCOL_VERSION: str = "1.0.0-PROD"

# --- Rede --------------------------------------------------------------------
PORT_DOWNLINK: int = 59900  # PC -> Celular (stream de áudio TX do host)
PORT_UPLINK: int = 59901    # Celular -> PC (microfone reverso RX do host)
HEARTBEAT_INTERVAL_MS: int = 1000   # ping a cada 1000ms sem tráfego ativo
DEAD_SOCKET_TIMEOUT_MS: int = 3000  # sem pacote algum por 3s => socket morto
CONNECT_TIMEOUT_S: float = 5.0
RECONNECT_BACKOFF_MS: tuple[int, ...] = (500, 1000, 2000)  # teto 5000ms
RECONNECT_BACKOFF_CAP_MS: int = 5000

# --- Áudio -------------------------------------------------------------------
SAMPLE_RATE: int = 48_000
SAMPLE_WIDTH_BYTES: int = 2        # 16-bit signed little-endian
FRAME_MS: int = 10
SAMPLES_PER_FRAME: int = SAMPLE_RATE * FRAME_MS // 1000  # 480 amostras/canal

DOWNLINK_CHANNELS: int = 2
DOWNLINK_FRAME_BYTES: int = SAMPLES_PER_FRAME * DOWNLINK_CHANNELS * SAMPLE_WIDTH_BYTES  # 1920

UPLINK_CHANNELS: int = 1
UPLINK_FRAME_BYTES: int = SAMPLES_PER_FRAME * UPLINK_CHANNELS * SAMPLE_WIDTH_BYTES      # 960

# --- Jitter buffer do Android (PRD §3.2) --------------------------------------
RING_BUFFER_MAX_FRAMES: int = 4            # 40 ms
RING_BUFFER_WATERMARK_FRAMES: int = 2      # começa a reproduzir com 20 ms
MIC_GAIN_MIN: float = 0.0
MIC_GAIN_MAX: float = 2.0

# --- Opcodes do protocolo (ABP) -----------------------------------------------
PACKET_AUDIO: int = 0x01
PACKET_PING: int = 0x02
PACKET_PONG: int = 0x03
PACKET_CONFIG_SYNC: int = 0x04

CHANNEL_DOWNLINK: int = 0x00
CHANNEL_UPLINK: int = 0x01

# --- Virtual cable -------------------------------------------------------------
CABLE_DEVICE_NAMES: tuple[str, ...] = ("CABLE Input", "VB-Audio Virtual Cable")
