import asyncio
import websockets

async def echo(websocket):
    async for message in websocket:
        await websocket.send(message)

async def main():
    async with websockets.serve(echo, "192.168.101.64", 8080):
        await asyncio.Future()  # run forever

asyncio.run(main())