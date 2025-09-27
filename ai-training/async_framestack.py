import numpy as np
from collections import deque

class AsyncFrameStack:
    def __init__(self, env, n_stack=4):
        self.env = env
        self.n_stack = n_stack
        self.frames = deque([], maxlen=n_stack)

    async def reset(self):
        obs = await self.env.reset()
        for _ in range(self.n_stack):
            self.frames.append(obs)
        return np.concatenate(list(self.frames), axis=0)

    async def step(self, action):
        obs, reward, terminated, truncated, info = await self.env.step(action)
        self.frames.append(obs)
        stacked_obs = np.concatenate(list(self.frames), axis=0)
        return stacked_obs, reward, terminated, truncated, info

    async def close(self):
        if hasattr(self.env, "close"):
            await self.env.close()

    async def become_owner(self):
        if hasattr(self.env, "become_owner"):
            await self.env.become_owner()