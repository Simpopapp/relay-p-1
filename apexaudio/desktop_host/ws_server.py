"""Single-port HTTP/ABP WebSocket bridge. Audio callbacks run in workers."""
from __future__ import annotations
import asyncio
from pathlib import Path
import time
from aiohttp import web, WSMsgType
from . import config, protocol
from .network_server import HostStats


class WsBridgeServer:
    def __init__(self, port=59900, web_dir=None, chunk_source=None, sink=None,
                 host='127.0.0.1', stats=None):
        self.port, self.host = port, host
        self.web_dir = Path(web_dir) if web_dir is not None else Path(__file__).resolve().parents[1] / 'web_client'
        self.chunk_source, self.sink = chunk_source, sink
        self.stats = stats or HostStats()
        self._clients = []
        self._runner = None

    async def start(self):
        app = web.Application()
        app.router.add_get('/ws', self._ws)
        app.router.add_get('/{path:.*}', self._http)
        self._runner = web.AppRunner(app)
        await self._runner.setup()
        site = web.TCPSite(self._runner, self.host, self.port)
        await site.start()
        self.port = site._server.sockets[0].getsockname()[1]

    async def stop(self):
        for ws in list(self._clients):
            await ws.close()
        if self._runner:
            await self._runner.cleanup()
            self._runner = None

    async def _http(self, request):
        root = self.web_dir.resolve()
        path = (root / (request.match_info['path'] or 'index.html')).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise web.HTTPNotFound()
        return web.FileResponse(path)

    async def _ws(self, request):
        ws = web.WebSocketResponse(max_msg_size=4096, autoping=True)
        await ws.prepare(request)
        self._clients.append(ws)
        self.stats._bump(downlink_clients=1, uplink_clients=1)
        state = {'received': time.monotonic(), 'pending': {}}
        await ws.send_bytes(protocol.make_config_sync(48000, 2, 1920, 0))
        sender = asyncio.create_task(self._send(ws, state))
        try:
            async for msg in ws:
                if msg.type != WSMsgType.BINARY:
                    await ws.close(code=1003, message=b'ABP binary required')
                    break
                try:
                    frame, used = protocol.decode(msg.data)
                    if used != len(msg.data):
                        raise protocol.ProtocolError('one ABP frame per message')
                    if frame.packet_type in (config.PACKET_PING, config.PACKET_PONG):
                        if frame.payload or frame.channel_id not in (0, 1):
                            raise protocol.ProtocolError('invalid control')
                    elif not (frame.packet_type == config.PACKET_AUDIO and frame.channel_id == 1 and len(frame.payload) == 960):
                        raise protocol.ProtocolError('invalid uplink')
                except protocol.ProtocolError:
                    await ws.close(code=1002, message=b'invalid ABP')
                    break
                state['received'] = time.monotonic()
                if frame.packet_type == config.PACKET_PING:
                    await ws.send_bytes(protocol.encode(3, frame.channel_id, frame.sequence_num, b'', frame.timestamp_us))
                elif frame.packet_type == config.PACKET_PONG:
                    sent = state['pending'].pop((frame.sequence_num, frame.timestamp_us), None)
                    if sent is not None:
                        with self.stats.lock:
                            self.stats.rtt_ms = (time.monotonic() - sent) * 1000
                elif self.sink:
                    ok = await asyncio.to_thread(self.sink.write_frame, frame.payload)
                    self.stats._bump(up_packets=1, up_bytes=960, drops=int(not ok))
        finally:
            sender.cancel()
            await asyncio.gather(sender, return_exceptions=True)
            self._clients.remove(ws)
            self.stats._bump(downlink_clients=-1, uplink_clients=-1)
        return ws

    async def _send(self, ws, state):
        seq = 1
        tick = time.monotonic()
        ping_at = tick + 1
        try:
            while not ws.closed:
                now = time.monotonic()
                if now - state['received'] >= 3:
                    await ws.close(code=1000, message=b'dead socket')
                    return
                if now >= ping_at:
                    ts = (time.monotonic_ns() // 1000) & 0xffffffff
                    state['pending'][(seq, ts)] = now
                    await ws.send_bytes(protocol.make_ping(seq, ts))
                    seq = (seq + 1) & 0xffffffff
                    ping_at = now + 1
                chunk = None
                if self._clients and self._clients[0] is ws and self.chunk_source:
                    chunk = await asyncio.to_thread(self.chunk_source)
                payload = chunk if chunk is not None and len(chunk) == 1920 else bytes(1920)
                await ws.send_bytes(protocol.encode(1, 0, seq, payload))
                self.stats._bump(down_packets=1, down_bytes=1920)
                seq = (seq + 1) & 0xffffffff
                now = time.monotonic()
                tick += .01
                if now - tick > .03:
                    tick = now + .01
                while tick < now:
                    tick += .01
                await asyncio.sleep(max(0, tick - now))
        except (ConnectionError, RuntimeError):
            await ws.close()
