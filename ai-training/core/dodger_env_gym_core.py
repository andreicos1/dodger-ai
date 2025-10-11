import asyncio

import numpy as np

import gymnasium as gym
from gymnasium import spaces

MIN_WIDTH = 360
MAX_WIDTH = 2400
MIN_HEIGHT = 500
MAX_HEIGHT = 1200

DEFAULT_WIDTH = 800
DEFAULT_HEIGHT = 600
MAX_BLOCKS = 10
ACTIONS = ["LEFT", "RIGHT", "NONE"]
PLAYER_WIDTH = 60
PLAYER_HEIGHT = 20
BLOCK_SIZE = 30
PLAYER_Y_OFFSET = 10


class DodgerEnvGym(gym.Env):
    metadata = {"render_modes": []}

    def __init__(
        self,
        width=DEFAULT_WIDTH,
        height=DEFAULT_HEIGHT,
        max_blocks=MAX_BLOCKS,
        actions=ACTIONS,
        player_width=PLAYER_WIDTH,
        player_height=PLAYER_HEIGHT,
        block_size=BLOCK_SIZE,
        player_y_offset=PLAYER_Y_OFFSET,
    ):
        super().__init__()
        self.state = None
        self.width = width
        self.height = height
        self.max_blocks = max_blocks
        self.player_height = player_height
        self.actions = actions
        self.player_width = player_width
        self.block_size = block_size
        self.player_y_offset = player_y_offset

        self.player_y = self.height - self.player_height - self.player_y_offset
        # Observation space: player_x, width_norm, height_norm, (dx, dy, block_x)*max_blocks
        obs_size = 3 + 3 * max_blocks
        self.action_space = spaces.Discrete(len(actions))
        self.observation_space = spaces.Box(
            low=-1.0, high=1.0, shape=(obs_size,), dtype=np.float32
        )
        self.loop = asyncio.get_event_loop()

    def _process_state(self, state):
        obs = np.zeros(self.observation_space.shape, dtype=np.float32)

        # Player X normalized to [-1, 1] (center is 0)
        obs[0] = (state["playerX"] / (self.width / 2)) - 1.0

        # Width and height normalized to [-1, 1]
        obs[1] = (self.width - (MIN_WIDTH + MAX_WIDTH) / 2) / \
            ((MAX_WIDTH - MIN_WIDTH) / 2)
        obs[2] = (self.height - (MIN_HEIGHT + MAX_HEIGHT) / 2) / \
            ((MAX_HEIGHT - MIN_HEIGHT) / 2)

        # Sort blocks by vertical distance (closest first)
        blocks = sorted(state["blocks"], key=lambda b: abs(
            b["y"] - self.player_y))

        for i, block in enumerate(blocks[: self.max_blocks]):
            # Relative horizontal distance, normalized to [-1, 1]
            dx = (block["x"] - state["playerX"]) / self.width
            # Relative vertical distance, normalized to approx [-1, 1]
            dy = (self.player_y - block["y"]) / self.height
            # Absolute block X position, normalized to [-1, 1]
            block_x_norm = (block["x"] / (self.width / 2)) - 1.0

            obs[3 + 3 * i] = dx
            obs[3 + 3 * i + 1] = dy
            obs[3 + 3 * i + 2] = block_x_norm

        return obs
