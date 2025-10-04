from core.dodger_env_gym_core import DodgerEnvGym
import websockets
import json


class DodgerEnvGymTrain(DodgerEnvGym):
    def __init__(self, uri="ws://localhost:8080", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.uri = uri
        self.ws = None
        self.done = False
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
        player_x_end = player_x_start + self.player_width
        # A block is a threat if it's in the bottom 35% of the screen
        danger_zone_y_threshold = self.height * 0.65

        for block in state["blocks"]:
            if block["y"] > danger_zone_y_threshold:
                block_x_start = block["x"]
                block_x_end = block_x_start + self.block_size
                # Check for horizontal overlap (imminent collision path)
                is_under_block = (
                    player_x_start < block_x_end and player_x_end > block_x_start
                )
                if is_under_block:
                    return True  # At least one block is a direct threat
        return False

    def _get_reward(self):
        reward = 0.001  # Default reward for surviving

        if self.done:
            reward = -5.0  # Penalty for failure.
        else:
            is_currently_threatened = self._is_player_threatened(self.state)

            # Check for the "successful dodge" event
            if self.was_threatened and not is_currently_threatened:
                reward = 2.0  # Reward for the specific action of dodging!

            if not self.was_threatened and is_currently_threatened:
                reward = -1.5  # Penalty for entering the danger zone

            # Update the state for the next frame
            self.was_threatened = is_currently_threatened

        return reward

    def _get_reward_curriculum_adjustment(self):
        reward = 0.005  # Default reward for surviving

        if self.done:
            reward = -10.0
        else:
            is_currently_threatened = self._is_player_threatened(self.state)
            if not self.was_threatened and is_currently_threatened:
                reward = -0.25  # Penalty for entering the danger zone

            self.was_threatened = is_currently_threatened

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
                # reward = self._get_reward()
                reward = self._get_reward_curriculum_adjustment()

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
        self.was_threatened = False
        obs = self.loop.run_until_complete(self._reset_async())
        return obs, {}
