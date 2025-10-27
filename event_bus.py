from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import asyncio, time, json

router = APIRouter()
_subscribers = []

def publish(event_type:str, data:dict):
    payload = json.dumps({"type":event_type,"data":data,"ts":int(time.time())})
    for q in list(_subscribers):
        try: q.put_nowait(payload)
        except: pass

@router.get("/stream")
async def stream(request: Request):
    q: asyncio.Queue = asyncio.Queue()
    _subscribers.append(q)
    async def eventgen():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    msg = await asyncio.wait_for(q.get(), timeout=10)
                    yield f"data: {msg}\n\n"
                except asyncio.TimeoutError:
                    yield 'data: {"type":"keepalive"}\n\n'
        finally:
            _subscribers.remove(q)
    return StreamingResponse(eventgen(), media_type="text/event-stream")
