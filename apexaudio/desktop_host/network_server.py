"""ApexAudio — servidor de rede do host (downlink TX 59900 / uplink RX 59901).

PRD §4 + §6: TCP puro sobre ADB reverse nas duas portas ou LAN; handshake CONFIG_SYNC;
heartbeat ping/pong; RTT; tolerância a queda com reconexão no lado cliente.
"""
from __future__ import annotations

import select
import socket
import struct
import threading
import time

from . import config, protocol


class HostStats:
    """Telemetria compartilhada exibida no dashboard do main.py."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.down_packets = 0
        self.up_packets = 0
        self.down_bytes = 0
        self.up_bytes = 0
        self.drops = 0
        self.rtt_ms: float | None = None
        self.downlink_clients = 0
        self.uplink_clients = 0

    def snapshot(self) -> dict:
        with self.lock:
            return {
                "down_packets": self.down_packets,
                "up_packets": self.up_packets,
                "down_bytes": self.down_bytes,
                "up_bytes": self.up_bytes,
                "drops": self.drops,
                "rtt_ms": self.rtt_ms,
                "downlink_clients": self.downlink_clients,
                "uplink_clients": self.uplink_clients,
            }

    def _bump(self, **delta) -> None:
        with self.lock:
            for key, value in delta.items():
                setattr(self, key, getattr(self, key) + value)


class AudioServer:
    """Orquestra as duas portas TCP do host.

    Parameters
    ----------
    chunk_source:
        callable que retorna o próximo chunk stereo 1920B (ou None).
    sink:
        objeto com `write_frame(mono_bytes) -> bool` (audio_sink.UplinkSink).
    bind_lan:
        se True, escuta em 0.0.0.0 (modo LAN); senão, apenas 127.0.0.1.
    """

    def __init__(self, chunk_source, sink, bind_lan: bool, stats: HostStats):
        self.chunk_source = chunk_source
        self.sink = sink
        self.bind_lan = bind_lan
        self.stats = stats
        self._stop = threading.Event()
        self._listeners: list[socket.socket] = []
        self._threads: list[threading.Thread] = []
        self._seq = 0
        self._seq_lock = threading.Lock()
        self._ping_pending: dict[int, float] = {}  # seq -> ts de envio
        self._ping_lock = threading.Lock()

    # ---------------- ciclo de vida ----------------
    def start(self) -> None:
        bind = "0.0.0.0" if self.bind_lan else "127.0.0.1"
        for port, handler in (
            (config.PORT_DOWNLINK, self._downlink_thread),
            (config.PORT_UPLINK, self._uplink_thread),
        ):
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind((bind, port))
            srv.listen(2)
            self._listeners.append(srv)
            t = threading.Thread(target=handler, args=(srv,),
                                 name=f"apex-{port}", daemon=True)
            self._threads.append(t)
            t.start()

    def stop(self) -> None:
        self._stop.set()
        for srv in self._listeners:
            try:
                srv.close()
            except OSError:
                pass

    # ---------------- downlink (PC ➔ celular) ----------------
    def _downlink_thread(self, srv: socket.socket) -> None:
        while not self._stop.is_set():
            try:
                srv.settimeout(0.5)
                conn, addr = srv.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            self.stats._bump(downlink_clients=1)
            try:
                self._serve_downlink(conn, addr)
            finally:
                self.stats._bump(downlink_clients=-1)
                try:
                    conn.close()
                except OSError:
                    pass

    def _serve_downlink(self, conn: socket.socket, addr) -> None:
        # Socket fica em modo bloqueante: leitura é via select() com timeout 0,
        # escrita (sendall) nunca sofre o timeout de 0.05s.
        conn.settimeout(None)
        conn.sendall(protocol.make_config_sync(
            config.SAMPLE_RATE, config.DOWNLINK_CHANNELS, config.DOWNLINK_FRAME_BYTES,
            sequence_num=self._next_seq()))
        last_traffic = last_ping_sent = last_received = time.monotonic()
        interval = config.FRAME_MS / 1000.0
        base = last_traffic
        tick = 0
        last_audio_sent = None
        buf = b""
        while not self._stop.is_set():
            # 1) lê possíveis pongs/pings do cliente (não bloqueia o fluxo de áudio)
            readable, _, _ = select.select([conn], [], [], 0.0)
            if readable:
                try:
                    data = conn.recv(65536)
                except (OSError, ConnectionError):
                    return
                if not data:
                    return
                last_traffic = time.monotonic()
                buf += data
                frames, buf = protocol.feed_stream(buf)
                if frames:
                    last_received = time.monotonic()
                for frame in frames:
                    try:
                        self._handle_control(frame, conn)
                    except OSError:
                        return
            if time.monotonic() - last_received >= config.DEAD_SOCKET_TIMEOUT_MS / 1000.0:
                return
            # 2) envia áudio (desconexão do cliente encerra a sessão em silêncio)
            chunk = self.chunk_source()
            if chunk is None:
                chunk = b"\0" * config.DOWNLINK_FRAME_BYTES
            # Primeiro frame imediato. Ticks vencidos não viram rajada:
            # atraso <= 3 ticks consome os slots vencidos; atraso maior
            # ressincroniza a base. Mantemos um intervalo entre envios reais.
            now = time.monotonic()
            deadline = base + tick * interval
            if last_audio_sent is not None:
                deadline = max(deadline, last_audio_sent + interval)
            if now < deadline:
                time.sleep(deadline - now)
            now = time.monotonic()
            if now - (base + tick * interval) > 3 * interval:
                base, tick = now, 0
            else:
                tick = max(tick, int((now - base) / interval))
            if now - last_received >= config.DEAD_SOCKET_TIMEOUT_MS / 1000.0:
                return
            try:
                conn.sendall(protocol.encode(
                    config.PACKET_AUDIO, config.CHANNEL_DOWNLINK,
                    self._next_seq(), chunk))
            except (ConnectionError, OSError):
                return
            last_audio_sent = time.monotonic()
            tick += 1
            self.stats._bump(down_packets=1, down_bytes=len(chunk))
            last_traffic = time.monotonic()
            # 3) PRD §2: cadência independente do áudio/silêncio enviado.
            if last_traffic - last_ping_sent >= config.HEARTBEAT_INTERVAL_MS / 1000.0:
                try:
                    self._send_ping(conn, config.CHANNEL_DOWNLINK)
                except OSError:
                    return
                last_ping_sent = time.monotonic()

    def _send_ping(self, conn: socket.socket, channel: int) -> None:
        seq = self._next_seq()
        now = time.monotonic()
        with self._ping_lock:
            # Limita pendências mesmo quando clientes somem sem responder.
            cutoff = now - config.DEAD_SOCKET_TIMEOUT_MS / 1000.0
            self._ping_pending = {key: sent for key, sent in self._ping_pending.items()
                                  if sent >= cutoff}
            self._ping_pending[seq] = now
        try:
            conn.sendall(protocol.encode(config.PACKET_PING, channel, seq, b""))
        except OSError:
            with self._ping_lock:
                self._ping_pending.pop(seq, None)
            raise

    def _handle_control(self, frame: protocol.ABPFrame, conn: socket.socket) -> None:
        if frame.packet_type == config.PACKET_PING:
            conn.sendall(protocol.encode(config.PACKET_PONG, frame.channel_id,
                                         frame.sequence_num, b"", frame.timestamp_us))
        elif frame.packet_type == config.PACKET_PONG:
            with self._ping_lock:
                sent = self._ping_pending.pop(frame.sequence_num, None)
            if sent is not None:
                rtt = (time.monotonic() - sent) * 1000.0
                with self.stats.lock:
                    self.stats.rtt_ms = round(rtt, 1)

    # ---------------- uplink (celular ➔ PC) ----------------
    def _uplink_thread(self, srv: socket.socket) -> None:
        while not self._stop.is_set():
            try:
                srv.settimeout(0.5)
                conn, addr = srv.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            self.stats._bump(uplink_clients=1)
            try:
                self._serve_uplink(conn)
            finally:
                self.stats._bump(uplink_clients=-1)
                try:
                    conn.close()
                except OSError:
                    pass

    def _serve_uplink(self, conn: socket.socket) -> None:
        buf = b""
        # Bloqueante para sendall (pong); leitura via select() com timeout p/ sair limpo.
        conn.settimeout(None)
        last_received = last_ping_sent = time.monotonic()
        while not self._stop.is_set():
            now = time.monotonic()
            if now - last_received >= config.DEAD_SOCKET_TIMEOUT_MS / 1000.0:
                return
            if now - max(last_received, last_ping_sent) >= config.HEARTBEAT_INTERVAL_MS / 1000.0:
                try:
                    self._send_ping(conn, config.CHANNEL_UPLINK)
                except OSError:
                    return
                last_ping_sent = time.monotonic()
            readable, _, _ = select.select([conn], [], [], 0.05)
            if not readable:
                continue
            try:
                data = conn.recv(65536)
            except socket.timeout:
                continue
            except (OSError, ConnectionError):
                return
            if not data:
                return
            buf += data
            frames, buf = protocol.feed_stream(buf)
            if frames:
                last_received = time.monotonic()
            for frame in frames:
                if frame.packet_type == config.PACKET_AUDIO:
                    if len(frame.payload) != config.UPLINK_FRAME_BYTES:
                        # frame inválido: descarta (política de tolerância a drift)
                        self.stats._bump(drops=1)
                        continue
                    self.sink.write_frame(frame.payload)
                    self.stats._bump(up_packets=1, up_bytes=len(frame.payload))
                else:
                    try:
                        self._handle_control(frame, conn)
                    except OSError:
                        return

    def _next_seq(self) -> int:
        with self._seq_lock:
            self._seq = (self._seq + 1) & 0xFFFFFFFF
            return self._seq
