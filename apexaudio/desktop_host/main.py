"""ApexAudio Host Server v1.0.0-PROD — entry point e orquestrador.

Uso:
    python -m desktop_host.main            (modo automático: ADB ou LAN)
    python -m desktop_host.main --lan      (força escuta LAN 0.0.0.0)

Dashboard CLI ANSI conforme PRD §8.2. Encerrar com Ctrl+C.
"""
from __future__ import annotations

import argparse
import shutil
import sys
import threading
import time

from . import adb_manager, config, protocol
from .audio_capture import LoopbackCapture, open_loopback_capture
from .audio_sink import UplinkSink
from .network_server import AudioServer, HostStats

BANNER = "=" * 60


def _fmt_kb(num_bytes: int, window: float) -> str:
    return f"{num_bytes / window / 1024:.1f} KB/s"


def render_dashboard(stats: HostStats, capture: LoopbackCapture, sink: UplinkSink,
                     adb: adb_manager.AdbStatus, bind: str) -> str:
    snap = stats.snapshot()
    device_line = (
        f"Device detected ({adb.device_serial}) -> Ports "
        f"{config.PORT_DOWNLINK}/{config.PORT_UPLINK} Routed."
        if adb.available and adb.downlink_reverse_ok and adb.reverse_ok
        else f"LAN mode listening on {bind} "
             f"(IP: {adb_manager.local_ip() or 'desconhecido'})")
    rtt = snap["rtt_ms"]
    return (
        BANNER + "\n"
        f" [ApexAudio Host Server v{config.PROTOCOL_VERSION}] - STATUS: RUNNING\n"
        + BANNER + "\n"
        f" [ADB Engine]    : {device_line}\n"
        f" [Capture]       : {'WASAPI Loopback Active (default speakers) [48kHz Stereo]' if not capture.silent_mode else 'WASAPI indisponível — modo silencioso (túnel ativo)'}\n"
        f" [Mic Sink]      : {'Virtual Cable Found (CABLE Input - VB-Audio Cable)' if sink.device_index is not None else 'VB-Cable NÃO encontrado — áudio do mic descartado'}\n"
        f" [Downlink TX]   : pkts={snap['down_packets']} clients={snap['downlink_clients']}\n"
        f" [Uplink RX]     : pkts={snap['up_packets']} drops={snap['drops']} "
        f"Latency: {rtt if rtt is not None else '--'}ms\n"
        + BANNER + "\n [Ctrl+C] Encerrar o servidor\n"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ApexAudio Host Server")
    parser.add_argument("--lan", action="store_true",
                        help="força escuta em 0.0.0.0 (padrão: automático)")
    args = parser.parse_args(argv)

    stats = HostStats()
    capture = open_loopback_capture()
    sink = UplinkSink()
    sink.start()
    capture.start()

    adb = adb_manager.detect_device()
    bind_lan = args.lan or not (adb.available and adb.device_serial)
    server = AudioServer(capture.read_chunk, sink, bind_lan=bind_lan, stats=stats)
    server.start()
    print(render_dashboard(stats, capture, sink, adb,
                           "0.0.0.0" if bind_lan else "127.0.0.1"))
    try:
        while True:
            time.sleep(4.0)
            print(render_dashboard(stats, capture, sink, adb,
                                   "0.0.0.0" if bind_lan else "127.0.0.1"),
                  end="\r", flush=True)
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
        capture.stop()
        sink.stop()
        print("\n[ApexAudio] servidor encerrado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
