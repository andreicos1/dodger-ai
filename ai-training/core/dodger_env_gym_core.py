import asyncio

import numpy as np

import gymnasium as gym
from gymnasium import spaces


DEFAULT_WIDTH = 1200
DEFAULT_HEIGHT = 800
FRAMES_PER_SECOND = 60
HEIGHT_EXPLORATION_SECONDS = 4
DANGER_ZONE_SECONDS = 2
BLOCK_SPEED_PIXELS_PER_FRAME = 3

MIN_WIDTH = 360
MAX_WIDTH = 2400
MIN_HEIGHT = 500
MAX_HEIGHT = 1200

WIDTH_EXPLORATION_RANGE = 1200
HEIGHT_EXPLORATION_RANGE = FRAMES_PER_SECOND * HEIGHT_EXPLORATION_SECONDS * BLOCK_SPEED_PIXELS_PER_FRAME

MAX_BLOCKS = 20
ACTIONS = ["LEFT", "RIGHT", "NONE"]
PLAYER_WIDTH = 60
PLAYER_HEIGHT = 20
BLOCK_SIZE = 30
PLAYER_Y_OFFSET = 10

CONSTANT_OBS_SIZE = 3
PER_BLOCK_OBS_SIZE = 2


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
        # Observation space: player_x, game_height, game_width, (dx, dy)*max_blocks
        obs_size = CONSTANT_OBS_SIZE + PER_BLOCK_OBS_SIZE * max_blocks
        self.action_space = spaces.Discrete(len(actions))
        self.observation_space = spaces.Box(
            low=0.0, high=1.0, shape=(obs_size,), dtype=np.float32
        )
        self.loop = asyncio.get_event_loop()


    def _get_blocks_in_range(self, state):
        blocks_x_axis = [b for b in state["blocks"] if abs(b["x"] - state["playerX"]) <= WIDTH_EXPLORATION_RANGE]
        blocks_in_range = [b for b in blocks_x_axis if abs(b["y"] - self.player_y) <= HEIGHT_EXPLORATION_RANGE]
        return sorted(blocks_in_range, key=lambda b: abs(b["y"] - self.player_y))

    def _process_state(self, state):
        obs = np.zeros(self.observation_space.shape, dtype=np.float32)

        # Player X normalized to [0, 1]
        obs[0] = state["playerX"] / MAX_WIDTH

        # Game height normalized to [0, 1]
        obs[1] = (self.height - MIN_HEIGHT) / (MAX_HEIGHT - MIN_HEIGHT)

        # Game width normalized to [0, 1]
        obs[2] = (self.width - MIN_WIDTH) / (MAX_WIDTH - MIN_WIDTH)

        blocks = self._get_blocks_in_range(state)

        for i, block in enumerate(blocks[: self.max_blocks]):
            # Absolute distance normalized to [0, 1]
            dx = (block["x"] - state["playerX"]) / WIDTH_EXPLORATION_RANGE + 0.5
            dy = abs(self.player_y - block["y"]) / HEIGHT_EXPLORATION_RANGE

            obs[CONSTANT_OBS_SIZE + PER_BLOCK_OBS_SIZE * i] = dx
            obs[CONSTANT_OBS_SIZE + PER_BLOCK_OBS_SIZE * i + 1] = dy

        return obs
