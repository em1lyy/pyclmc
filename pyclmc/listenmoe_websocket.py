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

cancel = False

async def send_ws(ws, data):
    if not cancel:
        json_data = json.dumps(data)
        await ws.send(json_data)

async def _send_pings(ws, interval=45):
    while not cancel:
        for _ in range(floor(interval * 2)):
            if not cancel:
                await asyncio.sleep(0.5)  # 0.5secs heartbeat/quit delay is not too bad
            else:
                break
        await asyncio.sleep(interval % 1)
        if cancel:
            break
        msg = { 'op': 9 }
        await send_ws(ws, msg)

async def mainloop(loop, on_meta_update, second_arg_for_on_meta_update):
    url = 'wss://listen.moe/gateway_v2'
    ws = await websockets.connect(url)

    while not cancel:
        ws_recv = None
        while ws_recv is None and not cancel:
            try:
                ws_recv = await asyncio.wait_for(ws.recv(), timeout=0.5)
            except asyncio.TimeoutError:
                ws_recv = None
        if cancel:
            break
        data = json.loads(ws_recv)

        if data['op'] == 0:
            heartbeat = data['d']['heartbeat'] / 1000
            loop.create_task(_send_pings(ws, heartbeat))
        elif data['op'] == 1:
            on_meta_update(data, second_arg_for_on_meta_update)

def run_mainloop(loop, on_meta_update, second_arg_for_on_meta_update):
    global cancel
    cancel = False
    future = mainloop(loop, on_meta_update, second_arg_for_on_meta_update)
    loop.run_until_complete(future)
