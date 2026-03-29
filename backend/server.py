from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
from edge_ai.navigation import calculate_drive_command

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("[SERVER] Edge AI Client connected via WebSockets!")
    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            
            # Predict actions using Edge AI
            drive_cmd = calculate_drive_command(payload.get('lidar', []))
            
            # Send actions back
            await websocket.send_text(json.dumps(drive_cmd))
    except WebSocketDisconnect:
        print("[SERVER] Client disconnected")
    except Exception as e:
        print("[SERVER] Error:", e)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
