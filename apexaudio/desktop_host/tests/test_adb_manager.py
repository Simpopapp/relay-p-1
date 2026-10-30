from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
if not __package__:
    import runpy
    runpy.run_path(str(Path(__file__).resolve().with_name('__init__.py')))
from apexaudio.desktop_host import adb_manager as adb
from apexaudio.desktop_host.audio_sink import offer_cable_install

class TestAdb(unittest.TestCase):
    def test_replug_and_single_reverse(self):
        calls = []; plugged = [True]
        def runner(*args):
            calls.append(args)
            if args == ('devices',): return 0, 'abc\tdevice' if plugged[0] else ''
            return 0, 'ok'
        m = adb.AdbManager(runner=runner)
        self.assertTrue(m.poll().reverse_ok); m.poll()
        plugged[0] = False; self.assertIsNone(m.poll().device_serial)
        plugged[0] = True; m.poll()
        reverses = [c for c in calls if 'reverse' in c]
        self.assertEqual(len(reverses), 2)
        self.assertTrue(all(c[-2:] == ('tcp:59900', 'tcp:59900') for c in reverses))
        self.assertEqual(len([c for c in calls if 'http://localhost:59900' in c]), 2)
    def test_reverse_failure_retries(self):
        calls=[]
        def runner(*args):
            calls.append(args)
            return (0, 'abc\tdevice') if args == ('devices',) else (1, 'failure')
        m=adb.AdbManager(runner=runner)
        self.assertFalse(m.poll().reverse_ok); m.poll()
        self.assertEqual(len(calls),4)
    def test_path_priority(self):
        with patch.object(adb.shutil, 'which', return_value='/bin/adb'):
            self.assertEqual(adb.locate(download=False), '/bin/adb')
    def test_local_and_mock_download(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(adb.shutil, 'which', return_value=None):
            name = 'adb.exe' if adb.os.name == 'nt' else 'adb'
            def download(url, dest):
                self.assertEqual(url, 'mock://tools')
                with zipfile.ZipFile(dest, 'w') as z: z.writestr('platform-tools/'+name, b'adb')
            path=adb.locate(tmp, url='mock://tools', downloader=download)
            self.assertTrue(Path(path).is_file())
            self.assertEqual(adb.locate(tmp, download=False),path)
    def test_offline_error(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(adb.shutil, 'which', return_value=None):
            def offline(*args): raise OSError('offline')
            with self.assertRaisesRegex(RuntimeError, 'rede'):
                adb.locate(tmp, downloader=offline)
    def test_cable_offer_and_action(self):
        calls=[]
        self.assertIn('downlink continua', offer_cable_install(None))
        offer_cable_install(None, True, calls.append)
        self.assertEqual(calls,['https://vb-audio.com/Cable/'])
        self.assertEqual(offer_cable_install(1, True, calls.append),'')
