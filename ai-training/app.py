from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from evaluate import run_evaluation_stream

app = FastAPI()

@app.websocket("/ws/run")
async def websocket_run(websocket: WebSocket):
    await websocket.accept()
    try:
        async for step_result in run_evaluation_stream():
            await websocket.send_json(step_result)
    except WebSocketDisconnect:
        print("Client disconnected")