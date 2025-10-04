import time
from stable_baselines3 import PPO
from core.dodger_env_gym_train import DodgerEnvGymTrain
from stable_baselines3.common.vec_env import DummyVecEnv, VecFrameStack

MODEL_PATH = "best_model/best_model.zip"
FPS = 60  # Target frames per second for visualization
N_STACK = 4  # This MUST match the n_stack used during training

if __name__ == "__main__":
    def make_env():
        return DodgerEnvGymTrain()

    vec_env = DummyVecEnv([make_env])
    env = VecFrameStack(vec_env, n_stack=N_STACK)

    try:
        model = PPO.load(MODEL_PATH, device="cpu")
        print(f"Model loaded from {MODEL_PATH}")
    except FileNotFoundError:
        print(f"Error: Model file not found at {MODEL_PATH}")
        print("Please make sure you have trained and saved the model first.")
        exit()

    obs = env.reset()

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
