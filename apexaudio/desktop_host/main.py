"""ApexAudio Host Server v1.0.0-PROD — entry point e orquestrador.

Uso:
    python -m desktop_host.main            (modo automático: ADB ou LAN)
    python -m desktop_host.main --install-cable  (oferece a instalação do VB-Cable)

Dashboard CLI ANSI conforme PRD §8.2. Encerrar com Ctrl+C.
"""
from __future__ import annotations

import asyncio
import argparse
import shutil
import sys
import threading
import time

from . import adb_manager, config, protocol
from .audio_capture import LoopbackCapture, open_loopback_capture
from .audio_sink import UplinkSink, offer_cable_install
from .network_server import HostStats
from .ws_server import WsBridgeServer

BANNER = "=" * 60


def _fmt_kb(num_bytes: int, window: float) -> str:
    return f"{num_bytes / window / 1024:.1f} KB/s"


def render_dashboard(stats: HostStats, capture: LoopbackCapture, sink: UplinkSink,
                     adb: adb_manager.AdbStatus, bind: str) -> str:
    snap = stats.snapshot()
    device_line = (
        f"Device detected ({adb.device_serial}) -> Ports "
        f"{config.PORT_DOWNLINK} HTTP+WS Routed."
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


async def run(args):
    stats = HostStats()
    capture = open_loopback_capture()
    sink = UplinkSink()
    server = None
    try:
        sink.start()
        capture.start()
        print(offer_cable_install(sink.device_index, args.install_cable))
        try:
            executable = await asyncio.to_thread(adb_manager.locate)
        except RuntimeError as exc:
            print(exc)
            executable = 'adb'
        manager = adb_manager.AdbManager(executable)
        adb = await asyncio.to_thread(manager.poll)
        # Bind local (D2-6): o celular alcança o host via adb reverse para o
        # 127.0.0.1 do PC; replug re-aplica o reverse (manager.poll), sem rebind.
        bind = '127.0.0.1'
        server = WsBridgeServer(chunk_source=lambda: capture.read_chunk(timeout=0),
                                sink=sink, host=bind, stats=stats)
        await server.start()
        while True:
            print(render_dashboard(stats, capture, sink, adb, bind), flush=True)
            await asyncio.sleep(2)
            adb = await asyncio.to_thread(manager.poll)
    finally:
        if server:
            await server.stop()
        capture.stop()
        sink.stop()


def main(argv=None):
    parser = argparse.ArgumentParser(description='ApexAudio HTTP+WS :59900')
    parser.add_argument('--lan', action='store_true', help='escuta LAN (também padrão automático)')
    parser.add_argument('--install-cable', action='store_true', help='abre download oficial do VB-Cable')
    args = parser.parse_args(argv)
    try:
        asyncio.run(run(args))
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
