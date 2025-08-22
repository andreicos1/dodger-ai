import asyncio
import time
from stable_baselines3 import PPO
from train import DodgerEnvGym  # Import your environment from the training script

# --- Configuration ---
MODEL_PATH = "dodger_ppo_final_dense.zip"  # Path to your saved model
FPS = 60  # Target frames per second for visualization

# --- Main Evaluation Loop ---
if __name__ == "__main__":
    # Create the environment
    env = DodgerEnvGym()

    # Load the trained model
    try:
        model = PPO.load(MODEL_PATH)
        print(f"Model loaded from {MODEL_PATH}")
    except FileNotFoundError:
        print(f"Error: Model file not found at {MODEL_PATH}")
        print("Please make sure you have trained and saved the model first.")
        exit()


    # Run episodes indefinitely
    obs, _ = env.reset()
    while True:
        try:
            # Get the action from the model
            action, _states = model.predict(obs, deterministic=True)

            # Perform the action in the environment
            obs, reward, terminated, truncated, info = env.step(action)

            # If the episode is over, reset the environment
            if terminated or truncated:
                print("Episode finished. Resetting...")
                obs, _ = env.reset()

            # --- THIS IS THE SLOWDOWN ---
            # Add a delay to control the speed of the simulation
            time.sleep(1 / FPS)

        except KeyboardInterrupt:
            print("\nEvaluation stopped by user.")
            break
        except Exception as e:
            print(f"An error occurred: {e}")
            break