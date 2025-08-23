import asyncio
import json
import numpy as np
import gymnasium as gym
from gymnasium import spaces
import websockets

import os
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv, VecFrameStack

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
        max_blocks=6,
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
        self.was_threatened = False

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
            
    def _is_player_threatened(self, state):
        """Helper function to determine if the player is in immediate danger."""
        player_x_start = state["playerX"]
        player_x_end = player_x_start + PLAYER_WIDTH
        # A block is a threat if it's in the bottom 35% of the screen
        danger_zone_y_threshold = self.height * 0.65

        for block in state["blocks"]:
            if block["y"] > danger_zone_y_threshold:
                block_x_start = block["x"]
                block_x_end = block_x_start + BLOCK_SIZE
                # Check for horizontal overlap (imminent collision path)
                is_under_block = (
                    player_x_start < block_x_end and player_x_end > block_x_start
                )
                if is_under_block:
                    return True  # At least one block is a direct threat
        return False

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

                reward = 0.0  # Default reward is zero. No reward for just surviving.

                if self.done:
                    reward = -1.0  # Clear, simple penalty for failure.
                else:
                    is_currently_threatened = self._is_player_threatened(self.state)

                    # Check for the "successful dodge" event
                    if self.was_threatened and not is_currently_threatened:
                        reward = 1.0  # Big reward for the specific action of dodging!

                    # Update the state for the next frame
                    self.was_threatened = is_currently_threatened

                return (
                    self._process_state(self.state),
                    reward,
                    self.done,
                    False,
                    {},
                )

    def _process_state(self, state):
        obs = np.zeros(self.observation_space.shape, dtype=np.float32)

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
        self.was_threatened = False
        obs = self.loop.run_until_complete(self._reset_async())
        return obs, {}

    def step(self, action):
        obs, reward, terminated, truncated, info = self.loop.run_until_complete(
            self._step_async(action)
        )
        return obs, reward, terminated, truncated, info


if __name__ == "__main__":
    base_env = DodgerEnvGym()
    monitored_env = Monitor(base_env, log_dir)
    vec_env = DummyVecEnv([lambda: monitored_env])
    stacked_env = VecFrameStack(vec_env, n_stack=4)

    model = PPO(
        "MlpPolicy",
        stacked_env, 
        verbose=1,
        tensorboard_log="./ppo_dodger_tensorboard/",
        gamma=0.999,          # Value future rewards more highly
        n_steps=4096,         # Collect more experience before each update
        ent_coef=0.01,        # Encourage more exploration
        learning_rate=1e-4,   # Use a smaller, more stable learning rate
    )
    model.learn(total_timesteps=5_000_000)

    model.save("dodger_ppo_framestack")