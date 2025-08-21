import asyncio
import json
import numpy as np
import gymnasium as gym
from gymnasium import spaces
import websockets

# RL actions (no RESTART here, handled internally)
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

        # Action space: LEFT, RIGHT, NONE
        self.action_space = spaces.Discrete(len(ACTIONS))

        # Observation space: playerX, (x,y)*max_blocks
        obs_size = 1 + 2 * max_blocks
        self.observation_space = spaces.Box(
            low=0.0, high=1.0, shape=(obs_size,), dtype=np.float32
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


                blocks = self.state["blocks"]
                reward = 1  # survival reward

                # Collision penalty
                for block in blocks:
                    if block["y"] < self.height * 0.7:
                        continue
                    if block['x'] + BLOCK_SIZE >= self.state["playerX"] and block['x'] <= self.state["playerX"] + PLAYER_WIDTH:
                        reward -= 10.0

                # Wall penalty
                if self.state["playerX"] < self.width * 0.1 or self.state["playerX"] > self.width * 0.9:
                    reward -= 2.0

                # Centering bonus
                center_x = self.width / 2
                dist_from_center = abs(self.state["playerX"] - center_x) / (self.width / 2)
                reward -= 0.5 * dist_from_center

                return (
                    self._process_state(self.state),
                    reward,
                    self.done,
                    False,
                    {},
                )

    def _process_state(self, state):
        obs = np.zeros(self.observation_space.shape, dtype=np.float32)

        # Player X normalized
        obs[0] = state["playerX"] / self.width

        # Sort blocks by y (closest to bottom first)
        blocks = sorted(state["blocks"], key=lambda b: b["y"], reverse=True)

        for i, block in enumerate(blocks[: self.max_blocks]):
            dx = (block["x"] - state["playerX"]) / self.width   # relative horizontal distance
            dy = (self.height - block["y"]) / self.height       # distance from player vertically (time-to-impact proxy)

            obs[1 + 2*i] = dx
            obs[1 + 2*i + 1] = dy

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


# Example training loop with Stable-Baselines3 PPO
if __name__ == "__main__":
    from stable_baselines3 import PPO

    env = DodgerEnvGym()

    model = PPO("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=1_000_000)

    model.save("dodger_ppo")

    # Test run
    obs, _ = env.reset()
    for _ in range(1000):
        action, _ = model.predict(obs)
        obs, reward, terminated, truncated, info = env.step(action)
        if terminated or truncated:
            obs, _ = env.reset()