#!/usr/bin/env python

# pyclmc - listenmoe_websocket.py
# Slightly modified version of https://docs.listen.moe/ws/usage.html#python
#
# Released under GNU GPLv3 https://www.gnu.org/licenses/gpl-3.0.en.html
# Maintained by Jonas Jaguar <jonasjaguar@jagudev.net>, 2020

import json
import asyncio
from math import floor

import websockets

# cancel = False  # When this gets set to true, send_ws, _send_pings and mainloop will exit at the next possible point.

async def send_ws(ws, data):  # Sends json data over websocket ws
    json_data = json.dumps(data)
    await ws.send(json_data)

async def _send_pings(ws, interval=45):  # Sends a heartbeat every interval seconds via ws
    while True:
        await asyncio.sleep(interval)
        msg = { 'op': 9 }
        await send_ws(ws, msg)

async def mainloop(loop, on_meta_update, second_arg_for_on_meta_update):
    url = 'wss://listen.moe/gateway_v2'  # Inits websocket
    ws = await websockets.connect(url)

    while True:
        ws_recv = None  # Waits for websocket data
        while ws_recv is None:
            try:
                ws_recv = await asyncio.wait_for(ws.recv(), timeout=0.5)
            except asyncio.TimeoutError:
                ws_recv = None

        data = json.loads(ws_recv)

        if data['op'] == 0:  # Welcome message -> extract heartbeat interval and start heartbeat sender
            heartbeat = data['d']['heartbeat'] / 1000
            loop.create_task(_send_pings(ws, heartbeat))
        elif data['op'] == 1:  # If we receive data, call the on_meta_update function
            on_meta_update(data, second_arg_for_on_meta_update)

def run_mainloop(loop, on_meta_update, second_arg_for_on_meta_update):  # Runs the mainloop() function in the provided asyncio loop
    # global cancel
    # cancel = False
    future = mainloop(loop, on_meta_update, second_arg_for_on_meta_update)
    loop.run_until_complete(future)
