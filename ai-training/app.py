from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
from core.dodger_env_gym_eval import DodgerEnvGymEval
from stable_baselines3 import PPO
import numpy as np

MODEL_PATH = "best_model/best_model.zip"
FPS = 60
N_STACK = 4

model = PPO.load(MODEL_PATH, device="cpu")

app = FastAPI()


@app.websocket("/ws/run")
async def websocket_run(websocket: WebSocket):
    await websocket.accept()
    env = DodgerEnvGymEval()

    try:
        await websocket.send_json({"type": "restart"})
        data = await websocket.receive_json()
        obs = env._process_state(data["state"])

        obs_stack = [obs] * N_STACK

        while True:
            stacked_obs = np.concatenate(obs_stack, axis=0)
            action, _states = model.predict(stacked_obs, deterministic=True)

            await websocket.send_json({"type": "step", "action": env.actions[int(action)]})
            data = await websocket.receive_json()

            obs = env._process_state(data["state"])
            done = data["state"].get("gameOver", False)

            obs_stack.pop(0)
            obs_stack.append(obs)

            if done:
                print("Episode finished. Resetting...")
                await websocket.send_json({"type": "restart"})
                data = await websocket.receive_json()
                obs = env._process_state(data["state"])
                obs_stack = [obs] * N_STACK

            await asyncio.sleep(1 / FPS)

    except WebSocketDisconnect:
        print("Client disconnected")
