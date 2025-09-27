# evaluate.py
import asyncio
from stable_baselines3 import PPO
from async_env import DodgerEnvGymAsync
from async_framestack import AsyncFrameStack

MODEL_PATH = "best_model/best_model.zip"
FPS = 60
N_STACK = 4

base_env = DodgerEnvGymAsync()
env = AsyncFrameStack(base_env, n_stack=N_STACK)
model = PPO.load(MODEL_PATH, device="cpu")
print(f"Model loaded from {MODEL_PATH}")

async def run_evaluation_stream():
    await env.become_owner()
    obs = await env.reset()
    step_count = 0
    while True:
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, info = await env.step(action)
        yield {
            "step": step_count,
            "action": int(action),
            "reward": float(reward),
            "terminated": bool(terminated),
        }
        if terminated:
            obs = await env.reset()
        await asyncio.sleep(1 / FPS)
        step_count += 1

async def main():
    async for step_result in run_evaluation_stream():
        continue

if __name__ == "__main__":
    asyncio.run(main())