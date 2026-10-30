"""ApexAudio — Apex Binary Protocol (ABP).

Framing binário determinístico (PRD §2). Toda leitura/escrita de rede passa
por aqui: 16 bytes de cabeçalho little-endian + payload PCM bruto.

Layout do cabeçalho (16 bytes):

    offset 0   uint16  MAGIC         0xAA55
    offset 2   uint8   PACKET_TYPE   0x01 audio | 0x02 ping | 0x03 pong | 0x04 config
    offset 3   uint8   CHANNEL_ID    0x00 downlink (stereo) | 0x01 uplink (mono)
    offset 4   uint32  SEQUENCE_NUM  contador incremental
    offset 8   uint32  TIMESTAMP_US  microssegundos local (RTT)
    offset 12  uint32  PAYLOAD_SIZE  bytes exatos do payload
"""
from __future__ import annotations

import struct
import time

from . import config

_HEADER_STRUCT = struct.Struct("<HBBIII")  # magic, type, channel, seq, ts_us, size
assert _HEADER_STRUCT.size == 16


class ProtocolError(ValueError):
    """Frame inválido: magic errado, payload incompleto ou tamanho ilógico."""


class ABPFrame:
    __slots__ = ("packet_type", "channel_id", "sequence_num", "timestamp_us", "payload")

    def __init__(self, packet_type: int, channel_id: int,
                 sequence_num: int, timestamp_us: int, payload: bytes):
        self.packet_type = packet_type
        self.channel_id = channel_id
        self.sequence_num = sequence_num
        self.timestamp_us = timestamp_us
        self.payload = payload

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return (f"ABPFrame(type=0x{self.packet_type:02X}, channel=0x{self.channel_id:02X}, "
                f"seq={self.sequence_num}, ts={self.timestamp_us}us, "
                f"payload={len(self.payload)}B)")


def encode(packet_type: int, channel_id: int, sequence_num: int,
           payload: bytes, timestamp_us: int | None = None) -> bytes:
    """Serializa um frame ABP completo (cabeçalho + payload)."""
    if timestamp_us is None:
        timestamp_us = time.monotonic_ns() // 1_000
    return _HEADER_STRUCT.pack(
        config.MAGIC, packet_type, channel_id, sequence_num,
        timestamp_us & 0xFFFFFFFF, len(payload),
    ) + payload


def decode(buf: bytes) -> tuple[ABPFrame, int]:
    """Decodifica o primeiro frame contido em `buf`.

    Retorna (frame, bytes_consumidos). Levanta ProtocolError se o buffer
    não contém um frame completo ou se o magic/tamanho são inválidos.
    """
    if len(buf) < _HEADER_STRUCT.size:
        raise ProtocolError(f"buffer incompleto: {len(buf)} < 16 bytes de cabeçalho")
    magic, packet_type, channel_id, seq, ts_us, size = _HEADER_STRUCT.unpack_from(buf)
    if magic != config.MAGIC:
        raise ProtocolError(f"magic inválido: 0x{magic:04X} (esperado 0xAA55)")
    total = _HEADER_STRUCT.size + size
    if len(buf) < total:
        raise ProtocolError(f"payload incompleto: {len(buf) - _HEADER_STRUCT.size} de {size} bytes")
    payload = bytes(buf[_HEADER_STRUCT.size:total])
    return ABPFrame(packet_type, channel_id, seq, ts_us, payload), total


def feed_stream(buf: bytes) -> tuple[list[ABPFrame], bytes]:
    """Extrai todos os frames completos de um buffer de stream TCP.

    Retorna (frames, resto_incompleto). O resto deve ser prefixado aos
    próximos bytes recebidos — é a defesa contra fragmentação de TCP.
    """
    frames: list[ABPFrame] = []
    offset = 0
    while True:
        if len(buf) - offset < _HEADER_STRUCT.size:
            break
        size = _HEADER_STRUCT.unpack_from(buf, offset)[5]
        total = _HEADER_STRUCT.size + size
        if len(buf) - offset < total:
            break
        frame, consumed = decode(buf[offset:])
        frames.append(frame)
        offset += consumed
    return frames, buf[offset:]


def make_config_sync(sample_rate: int, channels: int, frame_bytes: int,
                     sequence_num: int) -> bytes:
    """Handshake CONFIG_SYNC: sample_rate (u32) + canais (u8) + frame_bytes (u16)."""
    return encode(config.PACKET_CONFIG_SYNC, config.CHANNEL_DOWNLINK, sequence_num,
                  struct.pack("<IBH", sample_rate, channels, frame_bytes))


def parse_config_sync(frame: ABPFrame) -> tuple[int, int, int]:
    if frame.packet_type != config.PACKET_CONFIG_SYNC or len(frame.payload) != 7:
        raise ProtocolError("CONFIG_SYNC inválido")
    return struct.unpack("<IBH", frame.payload)


def make_ping(sequence_num: int, timestamp_us: int) -> bytes:
    return encode(config.PACKET_PING, config.CHANNEL_DOWNLINK, sequence_num,
                  b"", timestamp_us)


def make_pong(sequence_num: int, timestamp_us: int) -> bytes:
    return encode(config.PACKET_PONG, config.CHANNEL_DOWNLINK, sequence_num,
                  b"", timestamp_us)
