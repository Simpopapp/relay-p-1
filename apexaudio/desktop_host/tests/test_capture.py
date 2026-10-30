"""Capture queue/thread behavior; no physical audio device required."""
import threading
import time
import unittest

# unittest discover -s importa módulos sem executar o __init__ do pacote.
if not __package__:
    import runpy
    from pathlib import Path
    runpy.run_path(str(Path(__file__).resolve().with_name('__init__.py')))

from apexaudio.desktop_host.audio_capture import LoopbackCapture, FRAME_BYTES


class TestLoopbackCapture(unittest.TestCase):
    def test_thread_initializer_runs_inside_capture_thread(self):
        names = []
        capture = LoopbackCapture(thread_initializer=lambda: names.append(
            threading.current_thread().name))
        try:
            capture.start()
            deadline = time.monotonic() + 2
            while not names and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertEqual(names, ["apex-audio-capture"])
        finally:
            capture.stop()

    def test_initializer_exception_is_swallowed(self):
        def fail():
            raise RuntimeError("priority setup failed")
        capture = LoopbackCapture(thread_initializer=fail)
        try:
            capture.start()
            deadline = time.monotonic() + 2
            chunk = None
            while time.monotonic() < deadline:
                chunk = capture.read_chunk(timeout=0.05)
                if capture.silent_mode and chunk is not None:
                    break
            self.assertTrue(capture.silent_mode)
            self.assertEqual(len(chunk), FRAME_BYTES)
            self.assertEqual(chunk, b"\0" * FRAME_BYTES)
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
