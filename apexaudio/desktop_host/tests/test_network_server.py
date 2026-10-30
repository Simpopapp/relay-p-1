"""Gate TCP real do host: PRD §2, §4 e §6, sem dispositivos de áudio."""
from __future__ import annotations

import socket
import threading
import time
import unittest
from collections import deque

# unittest discover -s importa módulos sem executar o __init__ do pacote.
if not __package__:
    import runpy
    from pathlib import Path
    runpy.run_path(str(Path(__file__).resolve().with_name('__init__.py')))

from apexaudio.desktop_host import config, protocol
from apexaudio.desktop_host.network_server import AudioServer, HostStats


class FakeSink:
    """Registra frames entregues pelo uplink, com sincronização entre threads."""

    def __init__(self) -> None:
        self.frames: list[bytes] = []
        self.lock = threading.Lock()

    def write_frame(self, payload: bytes) -> bool:
        with self.lock:
            self.frames.append(payload)
        return True

    def snapshot(self) -> list[bytes]:
        with self.lock:
            return list(self.frames)


class TestAudioServer(unittest.TestCase):
    """Usa portas dinâmicas e timeouts limitados (PRD §4)."""

    def setUp(self) -> None:
        original_ports = config.PORT_DOWNLINK, config.PORT_UPLINK
        self.addCleanup(self.restore_ports, original_ports)
        # Reserva as duas simultaneamente para impedir números iguais.
        with socket.socket() as down, socket.socket() as up:
            down.bind(('127.0.0.1', 0))
            up.bind(('127.0.0.1', 0))
            config.PORT_DOWNLINK = down.getsockname()[1]
            config.PORT_UPLINK = up.getsockname()[1]
        self.stats = HostStats()
        self.sink = FakeSink()
        self.clients: list[socket.socket] = []
        self.server = AudioServer(lambda: None, self.sink, False, self.stats)
        self.addCleanup(self.cleanup_server)
        self.server.start()

    @staticmethod
    def restore_ports(ports) -> None:
        config.PORT_DOWNLINK, config.PORT_UPLINK = ports

    def cleanup_server(self) -> None:
        for client in self.clients:
            client.close()
        self.server.stop()
        for thread in self.server._threads:
            thread.join(timeout=1)
            self.assertFalse(thread.is_alive(), 'Thread do servidor não encerrou')

    def connect(self, port: int) -> socket.socket:
        client = socket.create_connection(('127.0.0.1', port), timeout=5)
        self.clients.append(client)
        return client

    def wait_stat(self, name: str, expected: int) -> None:
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            if self.stats.snapshot()[name] == expected:
                return
            time.sleep(0.005)
        self.assertEqual(self.stats.snapshot()[name], expected)

    def reader(self, client: socket.socket):
        """Lê em blocos pequenos, obrigando a remontagem de frames TCP."""
        buf = b''
        frames = deque()

        def next_frame() -> protocol.ABPFrame:
            deadline = time.monotonic() + 5
            while not frames:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    self.fail('Timeout aguardando frame ABP')
                client.settimeout(remaining)
                data = client.recv(257)
                self.assertTrue(data, 'Conexão fechada antes do frame')
                nonlocal buf
                batch, buf = protocol.feed_stream(buf + data)
                frames.extend(batch)
            return frames.popleft()

        return next_frame

    def test_handshake_and_downlink_1920_bytes(self) -> None:
        read = self.reader(self.connect(config.PORT_DOWNLINK))
        handshake = read()
        self.assertEqual(handshake.packet_type, config.PACKET_CONFIG_SYNC)
        self.assertEqual(protocol.parse_config_sync(handshake), (48000, 2, 1920))
        audio = read()
        self.assertEqual((audio.packet_type, audio.channel_id),
                         (config.PACKET_AUDIO, config.CHANNEL_DOWNLINK))
        self.assertEqual(audio.payload, b'\0' * 1920)
        self.assertGreaterEqual(self.stats.snapshot()['down_packets'], 1)

    def test_client_ping_gets_matching_pong(self) -> None:
        client = self.connect(config.PORT_DOWNLINK)
        read = self.reader(client)
        read()
        # Pong desconhecido deve ser ignorado sem modificar RTT ou derrubar sessão.
        client.sendall(protocol.make_pong(0xFFFFFFFE, 42) +
                       protocol.make_ping(0xFFFFFFFF, 12345))
        while True:
            frame = read()
            if frame.packet_type == config.PACKET_PONG:
                self.assertEqual((frame.sequence_num, frame.timestamp_us),
                                 (0xFFFFFFFF, 12345))
                break
        self.assertIsNone(self.stats.snapshot()['rtt_ms'])

    def test_uplink_960_bytes_reaches_sink(self) -> None:
        client = self.connect(config.PORT_UPLINK)
        payload = b'x' * 960
        raw = protocol.encode(config.PACKET_AUDIO, config.CHANNEL_UPLINK, 1, payload)
        client.sendall(raw[:7])
        client.sendall(raw[7:])
        self.wait_stat('up_packets', 1)
        self.assertEqual(self.sink.snapshot(), [payload])
        self.assertEqual(self.stats.snapshot()['up_bytes'], 960)

    def test_invalid_uplink_is_dropped(self) -> None:
        client = self.connect(config.PORT_UPLINK)
        for seq, size in enumerate((0, 959, 961)):
            client.sendall(protocol.encode(config.PACKET_AUDIO,
                                          config.CHANNEL_UPLINK, seq, b'x' * size))
        self.wait_stat('drops', 3)
        self.assertEqual(self.sink.snapshot(), [])
        self.assertEqual(self.stats.snapshot()['up_packets'], 0)

    def test_dry_source_heartbeat_populates_rtt(self) -> None:
        client = self.connect(config.PORT_DOWNLINK)
        read = self.reader(client)
        start = time.monotonic()
        pings = 0
        while time.monotonic() - start < 2.2:
            frame = read()
            if frame.packet_type == config.PACKET_PING:
                pings += 1
                client.sendall(protocol.make_pong(frame.sequence_num, frame.timestamp_us))
        self.assertGreaterEqual(pings, 1)
        rtt = self.stats.snapshot()['rtt_ms']
        self.assertIsInstance(rtt, float)
        self.assertGreaterEqual(rtt, 0)

    def test_disconnect_mid_downlink_allows_new_session(self) -> None:
        client = self.connect(config.PORT_DOWNLINK)
        read = self.reader(client)
        read()
        read()
        client.shutdown(socket.SHUT_RDWR)
        client.close()
        self.wait_stat('downlink_clients', 0)
        read = self.reader(self.connect(config.PORT_DOWNLINK))
        self.assertEqual(read().packet_type, config.PACKET_CONFIG_SYNC)

    def test_pacing_dry_source_is_throttled(self) -> None:
        read = self.reader(self.connect(config.PORT_DOWNLINK))
        self.assertEqual(read().packet_type, config.PACKET_CONFIG_SYNC)
        start = time.monotonic()
        arrivals = []
        while time.monotonic() - start < 1.05:
            frame = read()
            if frame.packet_type == config.PACKET_AUDIO:
                arrivals.append(time.monotonic())
        elapsed = time.monotonic() - start
        print(f"\nPACING frames={len(arrivals)} elapsed={elapsed:.4f}s "
              f"rate={len(arrivals)/elapsed:.2f}/s")
        # Windows CI timers can oversleep; verify throttling by elapsed rate.
        rate = len(arrivals) / elapsed
        self.assertTrue(70 <= rate <= 125, rate)
        # TCP may deliver several correctly paced frames in one receive call.
        # Exact send spacing is verified with a fake clock in test_pacing.py.

    def assert_dead_session(self, port: int, stat: str, handshake=False) -> None:
        start = time.monotonic()
        client = self.connect(port)
        if handshake:
            self.assertEqual(self.reader(client)().packet_type, config.PACKET_CONFIG_SYNC)
        self.wait_stat(stat, 1)
        # Não responde nem PING. Drena o downlink para não testar backpressure.
        client.settimeout(0.05)
        deadline = start + 4.5
        while time.monotonic() < deadline and self.stats.snapshot()[stat] != 0:
            try:
                client.recv(65536)
            except socket.timeout:
                pass
        elapsed = time.monotonic() - start
        self.assertEqual(self.stats.snapshot()[stat], 0)
        self.assertGreaterEqual(elapsed, config.DEAD_SOCKET_TIMEOUT_MS / 1000.0 - 0.1)
        print(f"\nDEAD_SOCKET {stat} elapsed={elapsed:.4f}s")

    def test_dead_socket_downlink_closes_session(self) -> None:
        self.assert_dead_session(config.PORT_DOWNLINK, 'downlink_clients', True)

    def test_dead_socket_uplink_closes_session(self) -> None:
        self.assert_dead_session(config.PORT_UPLINK, 'uplink_clients')

    def test_idle_uplink_ping_pong_populates_rtt(self) -> None:
        client = self.connect(config.PORT_UPLINK)
        frame = self.reader(client)()
        self.assertEqual((frame.packet_type, frame.channel_id),
                         (config.PACKET_PING, config.CHANNEL_UPLINK))
        client.sendall(protocol.encode(config.PACKET_PONG, config.CHANNEL_UPLINK,
                                      frame.sequence_num, b'', frame.timestamp_us))
        deadline = time.monotonic() + 1
        while self.stats.snapshot()['rtt_ms'] is None and time.monotonic() < deadline:
            time.sleep(0.005)
        self.assertIsInstance(self.stats.snapshot()['rtt_ms'], float)


if __name__ == '__main__':
    unittest.main()
