from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from stable_baselines3.common.vec_env import DummyVecEnv, VecFrameStack
import asyncio
from core.dodger_env_gym_eval import DodgerEnvGymEval
from stable_baselines3 import PPO

MODEL_PATH = "best_model/best_model.zip"
FPS = 60  # Target frames per second for visualization
N_STACK = 4  # This MUST match the n_stack used during training


model = PPO.load(MODEL_PATH, device="cpu")


def make_env():
    return DodgerEnvGymEval()


async def run_evaluation_stream(env: VecFrameStack):
    obs = env.reset()

    while True:
        action, _states = model.predict(obs, deterministic=True)
        obs, reward, terminated, info = env.step(action)

        yield {
            "type": "step",
            "action": env.actions[int(action)],
            "reward": float(reward),
        }

        if terminated[0]:
            print("Episode finished. Resetting...")
            yield {
                "type": "restart",
            }

        await asyncio.sleep(1 / FPS)

app = FastAPI()


@app.websocket("/ws/run")
async def websocket_run(websocket: WebSocket):
    await websocket.accept()
    vec_env = DummyVecEnv([make_env])
    env = VecFrameStack(vec_env, n_stack=N_STACK)
    try:
        async for step_result in run_evaluation_stream(env):
            continue
    except WebSocketDisconnect:
        print("Client disconnected")
