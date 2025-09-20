from collections import defaultdict
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

class WSManager:
    def __init__(self):
        self.rooms: Dict[str, Set[WebSocket]] = defaultdict(set)

    async def connect(self, org_id: str, ws: WebSocket):
        await ws.accept()
        self.rooms[org_id].add(ws)
        print(f"[WS] connected org={org_id} clients={len(self.rooms[org_id])} ids={[id(x) for x in self.rooms[org_id]]}")
    def disconnect(self, org_id: str, ws: WebSocket):
        self.rooms[org_id].discard(ws)
        if not self.rooms[org_id]:
            self.rooms.pop(org_id, None)

    async def broadcast(self, org_id: str, message: dict):
        print(f"알람을 전송합니다: {org_id}, {message}")
        dead = []
        print(f"[WS] broadcast org={org_id} -> {len(self.rooms[org_id])} clients ids={[id(x) for x in self.rooms[org_id]]}")
        for ws in list(self.rooms.get(org_id, [])):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(org_id, ws)

manager = WSManager()
@router.websocket("/ws/alerts/{organization_id}")
async def ws_alerts(websocket: WebSocket, organization_id: str):
    await manager.connect(organization_id, websocket)
    try:
        while True:
            await websocket.receive_text()  # ping/pong or ignore
    except WebSocketDisconnect:
        manager.disconnect(organization_id, websocket)