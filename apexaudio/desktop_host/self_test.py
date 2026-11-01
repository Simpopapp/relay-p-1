"""Offline packaged-host check: real HTTP/WS and bundled assets, no USB required."""
from aiohttp import ClientSession, WSMsgType

from . import protocol
from .ws_server import WsBridgeServer


async def run_self_test():
    class Sink:
        def __init__(self):
            self.frames = []

        def write_frame(self, payload):
            self.frames.append(payload)
            return True

    sink = Sink()
    server = WsBridgeServer(port=0, sink=sink)
    try:
        await server.start()
        url = f"http://127.0.0.1:{server.port}"
        async with ClientSession() as client:
            for asset in ("index.html", "app.js", "abp.js", "player-worklet.js",
                          "capturer-worklet.js"):
                async with client.get(f"{url}/{asset}") as response:
                    if response.status != 200 or not await response.read():
                        raise RuntimeError(f"Bundled asset missing: {asset}")
                    if asset.endswith(".js") and not response.content_type.endswith("javascript"):
                        raise RuntimeError(f"Wrong MIME for {asset}: {response.content_type}")
            async with client.ws_connect(url + "/ws") as ws:
                msg = await ws.receive(timeout=5)
                if msg.type != WSMsgType.BINARY:
                    raise RuntimeError("No binary CONFIG_SYNC")
                frame, _ = protocol.decode(msg.data)
                if protocol.parse_config_sync(frame) != (48000, 2, 1920):
                    raise RuntimeError("Invalid CONFIG_SYNC")
                payload = bytes(960)
                await ws.send_bytes(protocol.encode(1, 1, 1, payload))
                # A PONG confirms the preceding uplink was fully processed.
                await ws.send_bytes(protocol.make_ping(123, 456))
                audio_received = False
                for _ in range(200):
                    msg = await ws.receive(timeout=5)
                    if msg.type != WSMsgType.BINARY:
                        raise RuntimeError("WebSocket closed during self-test")
                    frame, _ = protocol.decode(msg.data)
                    if frame.packet_type == 1:
                        if len(frame.payload) != 1920:
                            raise RuntimeError("Invalid downlink frame")
                        audio_received = True
                    if frame.packet_type == 3 and frame.sequence_num == 123:
                        if frame.timestamp_us != 456 or sink.frames != [payload]:
                            raise RuntimeError("Uplink/control check failed")
                        if audio_received:
                            break
                else:
                    raise RuntimeError("Self-test did not complete")
        print("SELF_TEST_OK: bundled web assets, HTTP, CONFIG_SYNC, downlink, uplink, PONG", flush=True)
    finally:
        await server.stop()