import numpy as np
import gymnasium as gym
from gymnasium import spaces

ACTIONS = ["LEFT", "RIGHT", "NONE"]
PLAYER_WIDTH = 60
BLOCK_SIZE = 30

class DodgerEnvGymCore(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, width=800, height=600, max_blocks=10):
        super().__init__()
        self.width = width
        self.height = height
        self.max_blocks = max_blocks
        self.player_y = self.height - 20 - 10
        self.was_threatened = False
        self.done = False
        self.state = None

        obs_size = 1 + 3 * max_blocks
        self.action_space = spaces.Discrete(len(ACTIONS))
        self.observation_space = spaces.Box(
            low=-1.0, high=1.0, shape=(obs_size,), dtype=np.float32
        )

    def process_state(self, state):
        obs = np.zeros(self.observation_space.shape, dtype=np.float32)
        obs[0] = (state["playerX"] / (self.width / 2)) - 1.0
        blocks = sorted(state["blocks"], key=lambda b: abs(b["y"] - self.player_y))
        for i, block in enumerate(blocks[: self.max_blocks]):
            dx = (block["x"] - state["playerX"]) / self.width
            dy = (self.player_y - block["y"]) / self.height
            block_x_norm = (block["x"] / (self.width / 2)) - 1.0
            obs[1 + 3 * i] = dx
            obs[1 + 3 * i + 1] = dy
            obs[1 + 3 * i + 2] = block_x_norm
        return obs

    def is_player_threatened(self, state):
        player_x_start = state["playerX"]
        player_x_end = player_x_start + PLAYER_WIDTH
        danger_zone_y_threshold = self.height * 0.65
        for block in state["blocks"]:
            if block["y"] > danger_zone_y_threshold:
                block_x_start = block["x"]
                block_x_end = block_x_start + BLOCK_SIZE
                if player_x_start < block_x_end and player_x_end > block_x_start:
                    return True
        return False

    def compute_reward(self, state):
        if self.done:
            return -5.0
        is_threatened = self.is_player_threatened(state)
        reward = 0.001
        if self.was_threatened and not is_threatened:
            reward = 2.0
        if not self.was_threatened and is_threatened:
            reward = -1.5
        self.was_threatened = is_threatened
        return reward