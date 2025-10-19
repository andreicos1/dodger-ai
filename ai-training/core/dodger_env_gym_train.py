from core.dodger_env_gym_core import DodgerEnvGym
import websockets
import json
import numpy as np
from core.dodger_env_gym_core import MIN_WIDTH, MAX_WIDTH, MIN_HEIGHT, MAX_HEIGHT, MAX_BLOCKS, FRAMES_PER_SECOND, DANGER_ZONE_SECONDS, BLOCK_SPEED_PIXELS_PER_FRAME
import math


class DodgerEnvGymTrain(DodgerEnvGym):
    def __init__(self, uri="ws://localhost:8080", randomize_dimensions=False, *args, **kwargs):
        self.randomize_dimensions = randomize_dimensions
        self.rng = np.random.default_rng()

        super().__init__(*args, **kwargs)
        self.uri = uri
        self.ws = None
        self.done = False
        self.previous_state = None
        self.steps_survived = 0

    async def _connect(self):
        if self.ws is None or self.ws.closed:
            self.ws = await websockets.connect(self.uri)

    async def _reset_async(self):
        await self._connect()

        if self.randomize_dimensions:
            self.width = self.rng.integers(MIN_WIDTH, MAX_WIDTH)
            self.height = self.rng.integers(MIN_HEIGHT, MAX_HEIGHT)
            self.player_y = self.height - self.player_height - self.player_y_offset

        restart_msg = {
            "type": "restart",
            "width": int(self.width),
            "height": int(self.height)
        }
        await self.ws.send(json.dumps(restart_msg))

        while True:
            msg = await self.ws.recv()
            data = json.loads(msg)
            if data["type"] == "state":
                self.state = data["state"]
                self.done = self.state.get("gameOver", False)
                return self._process_state(self.state)

    def _get_evasion_reward(self, state):
        
        if self.previous_state is None:
            return 0
        player_x_start = state["playerX"]
        player_x_end = player_x_start + self.player_width
        # A block is a threat if it's in the bottom 2 seconds of the screen
        height_danger_zone = FRAMES_PER_SECOND * DANGER_ZONE_SECONDS * BLOCK_SPEED_PIXELS_PER_FRAME
        danger_zone_y_threshold = self.height - height_danger_zone
        threat_change = 0
        
        for block in state["blocks"][:MAX_BLOCKS]:
            if block["y"] < danger_zone_y_threshold:
                continue
            block_x_start = block["x"]
            block_x_end = block_x_start + self.block_size
            # Check for horizontal overlap (imminent collision path)
            is_under_block = (
                player_x_start <= block_x_end and player_x_end >= block_x_start
            )
            if not is_under_block:
                continue

            y_dist = abs(self.height - block["y"])
            y_proximity_normalized = 1.0 - (y_dist / (self.height - danger_zone_y_threshold))
            y_proximity_exp = math.exp(y_proximity_normalized)

            player_movement_direction = 'left' if state["playerX"] < self.previous_state["playerX"] else 'none' if self.previous_state["playerX"] == state["playerX"] else 'right'
            if player_movement_direction == 'none':
                threat_change -= y_proximity_exp
                continue

            box_x_middle = block_x_start + self.block_size / 2
            player_x_middle = player_x_start + self.player_width / 2
            player_to_box_relative_position = 'left' if player_x_middle < box_x_middle else 'middle' if player_x_middle == box_x_middle else 'right'
            if player_to_box_relative_position == player_movement_direction:
                threat_change += y_proximity_exp
            else:
                threat_change -= y_proximity_exp

        return threat_change * 0.1 # Because this is calculated per frame, we need to multiply by 0.1 to get a reasonable value

    def _get_reward(self):
        reward = 1e-3 * (self.steps_survived / 1000)

        if self.done:
            reward = -5.0  # Penalty for failure.
        else:
            evasion_reward = self._get_evasion_reward(self.state)
            reward += evasion_reward # Reward / Penalty for evasion

        return reward


    async def _step_async(self, action):
        await self.ws.send(
            json.dumps({"type": "step", "action": self.actions[action]})
        )
        while True:
            msg = await self.ws.recv()
            data = json.loads(msg)
            if data["type"] == "state":
                self.state = data["state"]
                self.done = self.state.get("gameOver", False)
                reward = self._get_reward()
                self.previous_state = self.state
                self.steps_survived += 1

                return (
                    self._process_state(self.state),
                    reward,
                    self.done,
                    False,
                    {},
                )

    def step(self, action):
        obs, reward, terminated, truncated, info = self.loop.run_until_complete(
            self._step_async(action)
        )
        return obs, reward, terminated, truncated, info

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.previous_state = None
        self.steps_survived = 0
        obs = self.loop.run_until_complete(self._reset_async())
        return obs, {}
