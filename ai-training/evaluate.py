import time
from stable_baselines3 import PPO
from train import DodgerEnvGym  
from stable_baselines3.common.vec_env import DummyVecEnv, VecFrameStack
import asyncio
import json

MODEL_PATH = "best_model/best_model.zip" 
FPS = 60  # Target frames per second for visualization
N_STACK = 4 # This MUST match the n_stack used during training

if __name__ == "__main__":
    def make_env():
        return DodgerEnvGym()
    
    vec_env = DummyVecEnv([make_env])
    env = VecFrameStack(vec_env, n_stack=N_STACK)

    try:
        model = PPO.load(MODEL_PATH)
        print(f"Model loaded from {MODEL_PATH}")
    except FileNotFoundError:
        print(f"Error: Model file not found at {MODEL_PATH}")
        print("Please make sure you have trained and saved the model first.")
        exit()

    obs = env.reset()

    inner_env = vec_env.envs[0]

    async def become_owner():
        await inner_env.ws.send(json.dumps({"type": "become_shared_owner"}))

    inner_env.loop.run_until_complete(become_owner())

    while True:
        try:
            action, _states = model.predict(obs, deterministic=True)

            obs, reward, terminated, info = env.step(action)

            if terminated[0]:
                print("Episode finished. Resetting...")
                obs = env.reset()

            time.sleep(1 / FPS)

        except KeyboardInterrupt:
            print("\nEvaluation stopped by user.")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            env.close()
            break

    env.close()