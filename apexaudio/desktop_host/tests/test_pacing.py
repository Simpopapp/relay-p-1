"""Sender timing is independent of OS timers and batched TCP delivery."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from apexaudio.desktop_host import config, protocol
from apexaudio.desktop_host.network_server import AudioServer, HostStats


class TestSenderPacing(unittest.TestCase):
    def run_sender(self, oversleep=0.0, stall_at=None):
        now = [0.0]
        sent = []
        sleeps = []
        server = AudioServer(lambda: None, None, False, HostStats())

        def sleep(delay):
            self.assertGreater(delay, 0)
            sleeps.append(delay)
            now[0] += delay + oversleep

        def sendall(raw):
            frame, _ = protocol.decode(raw)
            if frame.packet_type != config.PACKET_AUDIO:
                return
            self.assertEqual(len(frame.payload), 1920)
            sent.append(now[0])
            if len(sent) == stall_at:
                now[0] += 0.1
            if len(sent) == 100:
                server.stop()

        conn = SimpleNamespace(settimeout=lambda value: None, sendall=sendall)
        clock = SimpleNamespace(monotonic=lambda: now[0], sleep=sleep)
        with patch("apexaudio.desktop_host.network_server.time", clock), \
             patch("apexaudio.desktop_host.network_server.select.select",
                   return_value=([], [], [])):
            server._serve_downlink(conn, ("127.0.0.1", 0))
        self.assertEqual(len(sent), 100)
        self.assertEqual(len(sleeps), 99 if stall_at is None else 98)
        return sent

    def test_one_frame_every_ten_milliseconds(self):
        sent = self.run_sender()
        for index, timestamp in enumerate(sent):
            self.assertAlmostEqual(timestamp, index * 0.01, places=8)

    def test_windows_timer_oversleep_never_causes_catchup_burst(self):
        sent = self.run_sender(oversleep=0.015625)
        for a, b in zip(sent, sent[1:]):
            self.assertGreaterEqual(b - a, 0.01 - 1e-9)

    def test_hundred_millisecond_stall_never_causes_catchup_burst(self):
        sent = self.run_sender(stall_at=10)
        self.assertAlmostEqual(sent[10] - sent[9], 0.1, places=8)
        for a, b in zip(sent, sent[1:]):
            self.assertGreaterEqual(b - a, 0.01 - 1e-9)


if __name__ == "__main__":
    unittest.main()