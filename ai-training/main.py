import asyncio
import json
import numpy as np
import gymnasium as gym
from gymnasium import spaces
import websockets

# RL actions (no RESTART here, handled internally)
ACTIONS = ["LEFT", "RIGHT", "NONE"]


class DodgerEnvGym(gym.Env):
    metadata = {"render_modes": []}

    def __init__(
        self,
        uri="ws://localhost:8080",
        width=800,
        height=600,
        max_blocks=20,
        score_norm=1000.0,
    ):
        super().__init__()
        self.uri = uri
        self.ws = None
        self.state = None
        self.done = False
        self.width = width
        self.height = height
        self.max_blocks = max_blocks
        self.score_norm = score_norm

        # Action space: LEFT, RIGHT, NONE
        self.action_space = spaces.Discrete(len(ACTIONS))

        # Observation space: playerX, playerY, (x,y)*max_blocks, score
        obs_size = 1 + 2 * max_blocks + 1  # 42 if max_blocks=20
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

                # Reward: survive = +1, game over = -1000
                reward = 1.0
                if self.done:
                    reward = -1000.0

                return (
                    self._process_state(self.state),
                    reward,
                    self.done,
                    False,
                    {},
                )

    def _process_state(self, state):
        obs = np.zeros(self.observation_space.shape, dtype=np.float32)

        # Player X only (normalized)
        obs[0] = state["playerX"] / self.width

        # Sort blocks by distance to player Y (since playerY is fixed, just use block.y)
        blocks = sorted(
            state["blocks"],
            key=lambda b: b["y"],  # closest to bottom first
        )

        # Take up to max_blocks (20)
        for i, block in enumerate(blocks[: self.max_blocks]):
            obs[1 + 2 * i] = block["x"] / self.width
            obs[1 + 2 * i + 1] = block["y"] / self.height

        # Normalize score
        obs[-1] = state["score"] / self.score_norm

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
    model.learn(total_timesteps=200_000)

    model.save("dodger_ppo")

    # Test run
    obs, _ = env.reset()
    for _ in range(1000):
        action, _ = model.predict(obs)
        obs, reward, terminated, truncated, info = env.step(action)
        if terminated or truncated:
            obs, _ = env.reset()