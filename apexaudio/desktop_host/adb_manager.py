"""ADB discovery, single-port reverse and reconnect management."""
from __future__ import annotations

import re
import socket
import subprocess
import dataclasses

from . import config


@dataclasses.dataclass
class AdbStatus:
    available: bool
    device_serial: str | None
    downlink_reverse_ok: bool
    reverse_ok: bool
    message: str


def _run_adb(*args: str) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            ["adb", *args], capture_output=True, text=True, timeout=10)
        return proc.returncode, (proc.stdout + proc.stderr).strip()
    except FileNotFoundError:
        return -1, "adb não encontrado no PATH"
    except subprocess.TimeoutExpired:
        return -2, "adb não respondeu em 10s"


def local_ip() -> str | None:
    """IP LAN do host (trick de rota UDP — não envia nada de fato)."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return None
    finally:
        sock.close()

import shutil
import os
from pathlib import Path
import urllib.request
import zipfile
import tempfile

TOOLS_URL = 'https://dl.google.com/android/repository/platform-tools-latest-windows.zip'


def locate(local_dir=None, download=True, url=TOOLS_URL, downloader=None):
    """PATH -> local platform-tools -> official ZIP. Never silently ignore failure."""
    found = shutil.which('adb')
    if found:
        return found
    root = Path(local_dir) if local_dir else Path.home() / '.apexaudio'
    exe = root / 'platform-tools' / ('adb.exe' if os.name == 'nt' else 'adb')
    if exe.is_file():
        return str(exe)
    if not download:
        raise RuntimeError('ADB ausente no PATH e pasta local; habilite download com rede.')
    try:
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / 'tools.zip'
            if downloader:
                downloader(url, archive)
            else:
                with urllib.request.urlopen(url, timeout=30) as resp, open(archive, 'wb') as out:
                    shutil.copyfileobj(resp, out)
            with zipfile.ZipFile(archive) as z:
                # Extract only platform-tools files and reject path traversal.
                for info in z.infolist():
                    dest = (root / info.filename).resolve()
                    if not dest.is_relative_to(root.resolve()) or not info.filename.startswith('platform-tools/'):
                        raise ValueError('ZIP ADB inseguro')
                z.extractall(root)
        if not exe.is_file():
            raise ValueError('ZIP sem executável ADB para este sistema')
        exe.chmod(exe.stat().st_mode | 0o100)
        return str(exe)
    except Exception as exc:
        raise RuntimeError(f'Não foi possível instalar ADB; verifique rede: {exc}') from exc


class AdbManager:
    def __init__(self, executable='adb', runner=None):
        self.executable = executable
        self.runner = runner or self._run
        self._configured = None
        self.status = AdbStatus(False, None, False, False, 'Aguardando ADB')

    def _run(self, *args):
        try:
            p = subprocess.run([self.executable, *args], capture_output=True, text=True, timeout=10)
            return p.returncode, (p.stdout + p.stderr).strip()
        except (OSError, subprocess.TimeoutExpired) as exc:
            return -1, str(exc)

    def poll(self):
        code, out = self.runner('devices')
        serials = re.findall(r'^(\S+)\s+device\b', out, re.MULTILINE) if code == 0 else []
        serial = serials[0] if serials else None
        if not serial:
            self._configured = None
            self.status = AdbStatus(code == 0, None, False, False, out)
        elif serial != self._configured:
            code, out = self.runner('-s', serial, 'reverse', 'tcp:59900', 'tcp:59900')
            opened = False
            if code == 0:
                launch, message = self.runner('-s', serial, 'shell', 'am', 'start', '-a',
                    'android.intent.action.VIEW', '-d', 'http://localhost:59900')
                opened = launch == 0
                if not opened: out = message
            self._configured = serial if code == 0 and opened else None
            self.status = AdbStatus(True, serial, code == 0, code == 0,
                'Túnel :59900 ativo; página aberta' if opened else out)
        return self.status


def detect_device():
    return AdbManager().poll()
