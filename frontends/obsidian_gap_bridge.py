import asyncio
import json
from aiohttp import web


async def health(_request):
    return web.json_response({"ok": True})


async def gap(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    await ws.send_str(json.dumps({"type": "hello"}))

    async for msg in ws:
        if msg.type != web.WSMsgType.TEXT:
            continue
        data = json.loads(msg.data)
        text = data.get("text", "")

        if data.get("type") not in ("user", "slash_cmd"):
            await ws.send_str(
                json.dumps({"type": "error", "message": "Unsupported message type"})
            )
            continue
        await ws.send_str(json.dumps({"type": "chunk", "text": f"Echo: {text}"}))

        await asyncio.sleep(0.3)
        await ws.send_str(
            json.dumps({"type": "done", "text": f"Echo again: {text}"})
        )
    return ws


app = web.Application()
app.router.add_get("/health", health)
app.router.add_get("/gap", gap)

web.run_app(app, host="localhost", port=11489)
