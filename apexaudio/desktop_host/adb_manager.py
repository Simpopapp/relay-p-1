"""ApexAudio — gerenciamento automático do túnel ADB (PRD §4.3).

Se houver um dispositivo Android plugado em modo `device`, configura:
    adb reverse tcp:59900 tcp:59900   (o celular alcança o downlink do PC)
    # Decisão D1: o celular inicia conexões nas duas portas.
    adb reverse tcp:59901 tcp:59901   (o celular entrega o uplink no PC)
Sem ADB no PATH ou sem dispositivo, o host recai para LAN 0.0.0.0 e mostra o
IP local no console.
"""
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


def detect_device() -> AdbStatus:
    code, out = _run_adb("devices")
    if code != 0:
        return AdbStatus(False, None, False, False, out)
    serials = re.findall(r"^(\S+)\tdevice\b", out, flags=re.MULTILINE)
    if not serials:
        return AdbStatus(True, None, False, False,
                         "ADB presente, nenhum dispositivo em modo 'device'")
    serial = serials[0]
    # O celular é o cliente TCP das DUAS portas (PRD §6): `adb reverse` faz o
    # localhost do celular alcançar o host (Decisão D1 do PRD central).
    downlink_code, downlink_out = _run_adb("-s", serial, "reverse",
                                 f"tcp:{config.PORT_DOWNLINK}", f"tcp:{config.PORT_DOWNLINK}")
    rev_code, rev_out = _run_adb("-s", serial, "reverse",
                                 f"tcp:{config.PORT_UPLINK}", f"tcp:{config.PORT_UPLINK}")
    ok = downlink_code == 0 and rev_code == 0
    return AdbStatus(True, serial, downlink_code == 0, rev_code == 0,
                     f"device {serial}" if ok else f"reverse nas duas portas falhou: {downlink_out} {rev_out}")


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
