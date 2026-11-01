"""Capture queue/thread behavior; no physical audio device required."""
import threading
import time
import unittest
from unittest.mock import MagicMock, patch

# unittest discover -s importa módulos sem executar o __init__ do pacote.
if not __package__:
    import runpy
    from pathlib import Path
    runpy.run_path(str(Path(__file__).resolve().with_name('__init__.py')))

from apexaudio.desktop_host.audio_capture import (
    CaptureUnavailable, LoopbackCapture, FRAME_BYTES, _wasapi_frames,
)


class TestLoopbackCapture(unittest.TestCase):
    def test_thread_initializer_runs_inside_capture_thread(self):
        names = []
        capture = LoopbackCapture(thread_initializer=lambda: names.append(
            threading.current_thread().name))
        # Never touch real WASAPI hardware in tests (CI has no sound card).
        with patch("apexaudio.desktop_host.audio_capture._wasapi_frames",
                   side_effect=CaptureUnavailable("no test device")):
            try:
                capture.start()
                deadline = time.monotonic() + 5
                while not names and time.monotonic() < deadline:
                    time.sleep(0.01)
                self.assertEqual(names, ["apex-audio-capture"])
            finally:
                capture.stop()

    def test_initializer_exception_is_swallowed(self):
        def fail():
            raise RuntimeError("priority setup failed")
        capture = LoopbackCapture(thread_initializer=fail)
        with patch("apexaudio.desktop_host.audio_capture._wasapi_frames",
                   side_effect=CaptureUnavailable("no test device")):
            try:
                capture.start()
                chunk = capture.read_chunk(timeout=2)
                self.assertTrue(capture.silent_mode)
                self.assertEqual(chunk, b"\0" * FRAME_BYTES)
            finally:
                capture.stop()

    def test_missing_windows_output_device_keeps_capture_alive(self):
        pw = MagicMock()
        pa = pw.PyAudio.return_value.__enter__.return_value
        pa.get_host_api_info_by_type.return_value = {"defaultOutputDevice": -1}
        pa.get_device_info_by_index.side_effect = OSError(-9996, "Invalid device info")
        with patch.dict("sys.modules", {"pyaudiowpatch": pw}):
            with self.assertRaises(CaptureUnavailable):
                next(_wasapi_frames())
            capture = LoopbackCapture()
            try:
                capture.start()
                self.assertEqual(capture.read_chunk(timeout=2), b"\0" * FRAME_BYTES)
                self.assertTrue(capture.silent_mode)
                self.assertEqual(capture.read_chunk(timeout=2), b"\0" * FRAME_BYTES)
            finally:
                capture.stop()

    def test_audio_oserror_falls_back_to_silence(self):
        capture = LoopbackCapture()
        with patch("apexaudio.desktop_host.audio_capture._wasapi_frames",
                   side_effect=OSError(-9996, "Invalid device info")):
            try:
                capture.start()
                self.assertEqual(capture.read_chunk(timeout=2), b"\0" * FRAME_BYTES)
                self.assertTrue(capture.silent_mode)
            finally:
                capture.stop()

    def test_overrun_drops_oldest(self):
        capture = LoopbackCapture(max_queue=2)
        capture._put(b"first")
        capture._put(b"second")
        capture._put(b"third")
        self.assertEqual(capture.read_chunk(), b"second")
        self.assertEqual(capture.read_chunk(), b"third")


if __name__ == "__main__":
    unittest.main()
