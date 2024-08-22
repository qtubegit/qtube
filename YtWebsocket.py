import asyncio
import collections
import websockets.server
import websockets.sync.client 
import json
import threading

# A websocket for receiving events.
class YtWebsocket:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.callbacks = collections.defaultdict(lambda: [])

        thread = threading.Thread(target=self.serve_loop)
        thread.start()

    async def on_event(self, websocket):
        async for message in websocket:
            event = json.loads(message)
            for callback in self.callbacks[event['event']]:
                callback(event['data'])
        self.future.set_result(True)

    async def serve(self):
        async with websockets.server.serve(self.on_event, self.host, self.port):
            self.future = asyncio.Future()
            await self.future

    def serve_loop(self):
        asyncio.run(self.serve())

    def add_callback(self, event, callback):
        self.callbacks[event].append(callback)