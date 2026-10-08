# -*- coding: utf-8 -*-
"""
局域网/公网信令服务器
依赖：websockets
安装：py -m pip install websockets

本地运行：py signal_server.py
云平台运行：平台自动注入 PORT 环境变量，脚本自动读取
"""

import asyncio
import json
import os
import re
import websockets

# id -> 屏幕端连接
screens = {}
# id -> 遥控器端连接
remotes = {}

ID_PATTERN = re.compile(r"^\d{6}$")


async def send(ws, msg):
    """安全发送消息"""
    try:
        await ws.send(json.dumps(msg, ensure_ascii=False))
    except Exception:
        pass


async def handle_register(ws, msg):
    """屏幕端注册 ID"""
    sid = str(msg.get("id", ""))
    if not ID_PATTERN.match(sid):
        await send(ws, {"type": "error", "message": "ID 格式错误"})
        return
    if sid in screens:
        await send(ws, {"type": "error", "message": "ID 已被占用"})
        return
    screens[sid] = ws
    ws.screen_id = sid
    await send(ws, {"type": "registered", "id": sid})
    print(f"[注册] 屏幕 {sid}")


async def handle_join(ws, msg):
    """遥控器端加入某个 ID"""
    sid = str(msg.get("id", ""))
    if not ID_PATTERN.match(sid):
        await send(ws, {"type": "error", "message": "ID 格式错误"})
        return
    screen_ws = screens.get(sid)
    if not screen_ws:
        await send(ws, {"type": "error", "message": "ID 不存在"})
        return
    remotes[sid] = ws
    ws.remote_id = sid
    await send(ws, {"type": "joined", "id": sid})
    await send(screen_ws, {"type": "remote-joined", "id": sid})
    print(f"[加入] 遥控器 -> 屏幕 {sid}")


async def handle_signal(ws, msg):
    """转发 WebRTC 信令"""
    sid = str(msg.get("id", ""))
    target = None
    if getattr(ws, "screen_id", None) == sid:
        target = remotes.get(sid)
    elif getattr(ws, "remote_id", None) == sid:
        target = screens.get(sid)
    if target:
        await send(target, {
            "type": "signal",
            "id": sid,
            "from": "screen" if getattr(ws, "screen_id", None) else "remote",
            "data": msg.get("data"),
        })


async def handle_leave(ws, msg):
    """主动离开"""
    sid = str(msg.get("id", ""))
    if getattr(ws, "screen_id", None) == sid:
        screens.pop(sid, None)
        if sid in remotes:
            await send(remotes[sid], {"type": "screen-left", "id": sid})
    elif getattr(ws, "remote_id", None) == sid:
        remotes.pop(sid, None)
        if sid in screens:
            await send(screens[sid], {"type": "remote-left", "id": sid})


async def handler(ws):
    """每个 WebSocket 连接的处理入口"""
    ws.screen_id = None
    ws.remote_id = None
    try:
        async for raw in ws:
            try:
                msg = json.loads(raw)
            except Exception:
                continue
            t = msg.get("type")
            if t == "register":
                await handle_register(ws, msg)
            elif t == "join":
                await handle_join(ws, msg)
            elif t == "signal":
                await handle_signal(ws, msg)
            elif t == "leave":
                await handle_leave(ws, msg)
            elif t == "pong":
                pass
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        # 连接断开时清理映射
        sid = getattr(ws, "screen_id", None)
        if sid and screens.get(sid) is ws:
            screens.pop(sid, None)
            if sid in remotes:
                await send(remotes[sid], {"type": "screen-left", "id": sid})
        sid = getattr(ws, "remote_id", None)
        if sid and remotes.get(sid) is ws:
            remotes.pop(sid, None)
            if sid in screens:
                await send(screens[sid], {"type": "remote-left", "id": sid})


async def heartbeat():
    """每 20 秒发送一次心跳，保持连接"""
    while True:
        await asyncio.sleep(20)
        for ws in list(screens.values()) + list(remotes.values()):
            await send(ws, {"type": "ping"})


async def main():
    # 云平台会通过环境变量 PORT 注入端口，本地默认 8765
    port = int(os.environ.get("PORT", 8765))
    # 监听 0.0.0.0，局域网和云平台都需要
    async with websockets.serve(handler, "0.0.0.0", port):
        print(f"信令服务器已启动，监听 0.0.0.0:{port}")
        print("按 Ctrl+C 停止")
        await asyncio.Future()  # 保持运行


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n已停止")