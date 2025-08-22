import asyncio
import json
import numpy as np
import gymnasium as gym
from gymnasium import spaces
import websockets

import os
import matplotlib.pyplot as plt
import pandas as pd
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor

# Log directory
log_dir = "logs/"
os.makedirs(log_dir, exist_ok=True)

ACTIONS = ["LEFT", "RIGHT", "NONE"]
PLAYER_WIDTH = 60
BLOCK_SIZE = 30


class DodgerEnvGym(gym.Env):
    metadata = {"render_modes": []}

    def __init__(
        self,
        uri="ws://localhost:8080",
        width=800,
        height=600,
        max_blocks=8,
    ):
        super().__init__()
        self.uri = uri
        self.ws = None
        self.state = None
        self.done = False
        self.width = width
        self.height = height
        self.max_blocks = max_blocks
        self.player_y = self.height - 20 - 10

        # Observation space: player_x, (dx, dy, block_x)*max_blocks
        obs_size = 1 + 3 * max_blocks
        self.action_space = spaces.Discrete(len(ACTIONS))
        self.observation_space = spaces.Box(
            low=-1.0, high=1.0, shape=(obs_size,), dtype=np.float32
        )

        self.loop = asyncio.get_event_loop()

    async def _connect(self):
        if self.ws is None or self.ws.closed:
            self.ws = await websockets.connect(self.uri)

    async def _reset_async(self):
        await self._connect()
        await self.ws.send(json.dumps({"type": "restart"}))
        while True:
            msg = await self.ws.recv()
            data = json.loads(msg)
            if data["type"] == "state":
                self.state = data["state"]
                self.done = self.state.get("gameOver", False)
                return self._process_state(self.state)

    async def _step_async(self, action):
        await self.ws.send(
            json.dumps({"type": "step", "action": ACTIONS[action]})
        )
        while True:
            msg = await self.ws.recv()
            data = json.loads(msg)
            if data["type"] == "state":
                self.state = data["state"]
                self.done = self.state.get("gameOver", False)

                reward = 0.1

                if self.done:
                    reward = -10.0  

                return (
                    self._process_state(self.state),
                    reward,
                    self.done,
                    False,
                    {},
                )

    def _process_state(self, state):
        obs = np.zeros(self.observation_space.shape, dtype=np.float32)

        # --- FIX 2: NORMALIZE ALL POSITIONS TO [-1, 1] for consistency ---
        # Player X normalized to [-1, 1] (center is 0)
        obs[0] = (state["playerX"] / (self.width / 2)) - 1.0

        # Sort blocks by vertical distance (closest first)
        blocks = sorted(state["blocks"], key=lambda b: abs(b["y"] - self.player_y))

        for i, block in enumerate(blocks[: self.max_blocks]):
            # Relative horizontal distance, normalized to [-1, 1]
            dx = (block["x"] - state["playerX"]) / self.width
            # Relative vertical distance, normalized to approx [-1, 1]
            dy = (self.player_y - block["y"]) / self.height
            # Absolute block X position, normalized to [-1, 1]
            block_x_norm = (block["x"] / (self.width / 2)) - 1.0

            obs[1 + 3 * i] = dx
            obs[1 + 3 * i + 1] = dy
            obs[1 + 3 * i + 2] = block_x_norm

        return obs

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        obs = self.loop.run_until_complete(self._reset_async())
        return obs, {}

    def step(self, action):
        obs, reward, terminated, truncated, info = self.loop.run_until_complete(
            self._step_async(action)
        )
        return obs, reward, terminated, truncated, info


if __name__ == "__main__":
    gym_env = DodgerEnvGym()
    env = Monitor(gym_env, log_dir)

    model = PPO(
        "MlpPolicy",
        env,
        verbose=1,
        tensorboard_log="./ppo_dodger_tensorboard/"
    )
    model.learn(total_timesteps=200_000)

    model.save("dodger_ppo_final_dense")

    # Plotting code...
    monitor_files = [f for f in os.listdir(log_dir) if f.startswith("monitor")]
    if not monitor_files:
        print("No monitor file found. Exiting.")
        exit()

    monitor_file = max(monitor_files, key=lambda f: os.path.getmtime(os.path.join(log_dir, f)))
    df = pd.read_csv(os.path.join(log_dir, monitor_file), skiprows=1)

    df["timesteps"] = df["l"].cumsum()
    window = 50
    df["reward_smooth"] = df["r"].rolling(window, min_periods=1).mean()

    plt.figure(figsize=(12, 5))
    plt.plot(df["timesteps"], df["r"], alpha=0.3, label="Episode reward (raw)")
    plt.plot(df["timesteps"], df["reward_smooth"], label=f"Smoothed reward (window={window})")
    plt.xlabel("Timesteps")
    plt.ylabel("Episode Reward")
    plt.title("Training Progress (Dense Reward)")
    plt.legend()
    plt.grid()
    plt.show()