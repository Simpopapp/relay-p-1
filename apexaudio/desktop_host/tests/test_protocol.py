"""Testes de paridade e integridade do ABP (Fase 1 do roadmap).

Roda com `pytest` ou `python3 -m unittest` a partir de desktop_host/.
"""
from __future__ import annotations

import os
import struct
import sys
import unittest

_APEX_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _APEX_ROOT not in sys.path:
    sys.path.insert(0, _APEX_ROOT)

from desktop_host import config
from desktop_host.protocol import (ABPFrame, ProtocolError, decode, encode,
                                   feed_stream, make_config_sync, make_ping,
                                   make_pong, parse_config_sync)


class TestABPFrame(unittest.TestCase):
    def test_header_is_exactly_16_bytes(self):
        frame = encode(config.PACKET_AUDIO, config.CHANNEL_DOWNLINK, 1, b"x" * 1920)
        self.assertEqual(len(frame) - 1920, 16)
        self.assertEqual(len(frame), 16 + 1920)

    def test_frame_sizes_match_prd(self):
        down = encode(config.PACKET_AUDIO, config.CHANNEL_DOWNLINK, 0, b"\0" * config.DOWNLINK_FRAME_BYTES)
        up = encode(config.PACKET_AUDIO, config.CHANNEL_UPLINK, 0, b"\0" * config.UPLINK_FRAME_BYTES)
        self.assertEqual(len(down), 16 + 1920)
        self.assertEqual(len(up), 16 + 960)

    def test_round_trip_preserves_fields(self):
        payload = bytes(range(256)) * 8
        raw = encode(config.PACKET_AUDIO, config.CHANNEL_UPLINK, 777, payload, 42)
        frame, consumed = decode(raw)
        self.assertEqual(consumed, len(raw))
        self.assertEqual(frame.packet_type, 0x01)
        self.assertEqual(frame.channel_id, 0x01)
        self.assertEqual(frame.sequence_num, 777)
        self.assertEqual(frame.timestamp_us, 42)
        self.assertEqual(frame.payload, payload)

    def test_little_endian_layout(self):
        raw = encode(config.PACKET_AUDIO, config.CHANNEL_DOWNLINK, 0x0A0B0C0D, b"abcd", 0x01020304)
        self.assertEqual(raw[0:2], b"\x55\xaa")            # magic LE
        self.assertEqual(raw[2], 0x01)                      # type
        self.assertEqual(raw[3], 0x00)                      # channel
        self.assertEqual(raw[4:8], b"\x0d\x0c\x0b\x0a")     # seq LE
        self.assertEqual(raw[8:12], b"\x04\x03\x02\x01")    # ts LE
        self.assertEqual(raw[12:16], struct.pack("<I", 4))  # payload size

    def test_rejects_bad_magic_and_short_payload(self):
        with self.assertRaises(ProtocolError):
            decode(b"\x00\x00" + b"\0" * 30)
        good = encode(config.PACKET_AUDIO, config.CHANNEL_DOWNLINK, 1, b"\0" * 1920)
        with self.assertRaises(ProtocolError):
            decode(good[:20])           # payload cortado no meio
        with self.assertRaises(ProtocolError):
            decode(b"")                  # vazio

    def test_feed_stream_defragments_tcp(self):
        f1 = encode(config.PACKET_AUDIO, config.CHANNEL_DOWNLINK, 1, b"a" * 1920)
        f2 = encode(config.PACKET_PING, config.CHANNEL_DOWNLINK, 2, b"", 999)
        chunk = f1[:100] + f1[100:] + f2[:3]      # fragmentação agressiva
        frames, rest = feed_stream(chunk)
        self.assertEqual([fr.sequence_num for fr in frames], [1])
        self.assertEqual(rest, f2[:3])
        frames2, rest2 = feed_stream(rest + f2[3:])
        self.assertEqual(len(frames2), 1)
        self.assertEqual(frames2[0].packet_type, config.PACKET_PING)
        self.assertEqual(frames2[0].timestamp_us, 999)
        self.assertEqual(rest2, b"")

    def test_config_sync_round_trip(self):
        raw = make_config_sync(48000, 2, 1920, 9)
        frame, _ = decode(raw)
        self.assertEqual(parse_config_sync(frame), (48000, 2, 1920))

    def test_ping_pong_pair(self):
        ping = decode(make_ping(5, 123456))[0]
        pong = decode(make_pong(5, 123456))[0]
        self.assertEqual((ping.packet_type, pong.packet_type), (0x02, 0x03))
        self.assertEqual(ping.timestamp_us, pong.timestamp_us)


if __name__ == "__main__":
    unittest.main()
