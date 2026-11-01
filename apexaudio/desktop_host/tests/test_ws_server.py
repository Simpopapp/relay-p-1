import asyncio
from pathlib import Path
import tempfile
import time
import unittest
if not __package__:
    import runpy
    runpy.run_path(str(Path(__file__).resolve().with_name('__init__.py')))
from aiohttp import ClientSession, WSMsgType
from apexaudio.desktop_host.ws_server import WsBridgeServer
from apexaudio.desktop_host import protocol

class Probe:
    def __init__(self): self.frames = []
    def write_frame(self, data): self.frames.append(data); return True

class TestWS(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Windows may briefly hold served files open; never fail on temp cleanup.
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.sink = Probe()
        self.server = WsBridgeServer(port=0, web_dir=self.tmp.name, sink=self.sink)
        await self.server.start()
        self.client = ClientSession()
        self.sockets = []
        self.url = f'http://127.0.0.1:{self.server.port}'
    async def asyncTearDown(self):
        for ws in self.sockets: await ws.close()
        await self.client.close(); await self.server.stop(); self.tmp.cleanup()
    async def connect(self):
        ws = await self.client.ws_connect(self.url + '/ws')
        self.sockets.append(ws)
        msg = await ws.receive(timeout=5)
        frame, _ = protocol.decode(msg.data)
        self.assertEqual(protocol.parse_config_sync(frame), (48000, 2, 1920))
        return ws
    async def test_config(self):
        await self.connect()
    async def test_pacing(self):
        ws = await self.connect(); start = time.monotonic(); n = 0
        while time.monotonic() - start < 1.2:
            msg = await ws.receive(timeout=5)
            frame, _ = protocol.decode(msg.data)
            if frame.packet_type == 1:
                self.assertEqual(len(msg.data), 1936); n += 1
        elapsed = time.monotonic()-start; rate = n/elapsed
        print(f'WS PACING frames={n} elapsed={elapsed:.4f}s rate={rate:.2f}/s', flush=True)
        # Coarse smoke check only: exact cadence is verified with a fake clock
        # in test_pacing.py; CI VMs can stall the receiver arbitrarily.
        self.assertTrue(40 <= rate <= 130, rate)
    async def test_uplink(self):
        ws = await self.connect()
        await ws.send_bytes(protocol.encode(1, 1, 1, bytes(960)))
        for _ in range(500):
            if self.sink.frames: break
            await asyncio.sleep(.01)
        self.assertEqual(self.sink.frames, [bytes(960)])
    async def test_ping_rtt(self):
        ws = await self.connect()
        while True:
            msg = await ws.receive(timeout=5)
            frame, _ = protocol.decode(msg.data)
            if frame.packet_type == 2:
                await ws.send_bytes(protocol.make_pong(frame.sequence_num, frame.timestamp_us)); break
        for _ in range(500):
            if self.server.stats.snapshot()['rtt_ms'] is not None: break
            await asyncio.sleep(.01)
        self.assertIsNotNone(self.server.stats.snapshot()['rtt_ms'])
    async def test_dead_socket(self):
        ws = await self.connect(); start = time.monotonic()
        while (await ws.receive(timeout=8)).type == WSMsgType.BINARY: pass
        elapsed = time.monotonic()-start
        print(f'WS DEAD_SOCKET elapsed={elapsed:.4f}s', flush=True)
        # Server timer starts before our clock; allow scheduler stalls on CI.
        self.assertTrue(2.5 <= elapsed <= 6.5, elapsed)
    async def test_http(self):
        async with self.client.get(self.url) as r: self.assertEqual(r.status, 404)
        Path(self.tmp.name, 'index.html').write_text('bridge')
        async with self.client.get(self.url) as r:
            self.assertEqual(r.status, 200); self.assertEqual(await r.text(), 'bridge')
        self.server.web_dir = Path(self.tmp.name) / 'missing'
        async with self.client.get(self.url) as r: self.assertEqual(r.status, 404)
    async def test_multiple_and_promotion(self):
        self.server.chunk_source = lambda: b'x'*1920
        first = await self.connect(); second = await self.connect()
        frame, _ = protocol.decode((await second.receive()).data)
        self.assertEqual(frame.payload, bytes(1920))
        await first.close(); await asyncio.sleep(.04)
        for _ in range(1000):
            frame, _ = protocol.decode((await second.receive(timeout=5)).data)
            if frame.payload == b'x'*1920: break
        self.assertEqual(frame.payload, b'x'*1920)
    async def test_invalid_frame(self):
        ws = await self.connect(); await ws.send_bytes(b'bad')
        while (await ws.receive(timeout=5)).type == WSMsgType.BINARY: pass
        self.assertTrue(ws.closed)
