# import asyncio
# import websanic
# from sanic.response import html
# from websockets.exceptions import ConnectionClosed
# import datetime
# import random
# import json
#
# app = websanic.Sanic()
#
# connections = set()
# async def time(websocket, path):
#     while True:
#         connections.add(websocket)
#         mesg = await websocket.recv()
#         data = json.loads(mesg)
#         if data.get('type') == 'name':
#             mesg = json.dumps({'data': '{} joined'.format(data.get('user'))})
#         for connection in connections.copy():
#             try:
#                 await connection.send(mesg)
#             except ConnectionClosed:
#                 connections.remove(connection)
#
#
# app.websocket(time, 'localhost', 3000)
#
# app.static('/', './')
#
# app.run(port=8000)