from core.dodger_env_gym_core import DodgerEnvGym
from fastapi import WebSocket
import json
import asyncio


class DodgerEnvGymEval(DodgerEnvGym):
    def __init__(self, ws: WebSocket, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ws = ws

    async def _reset_async(self):
        await self.ws.send(json.dumps({"type": "restart"}))

    async def _step_async(self, action):
        await self.ws.send(json.dumps({"type": "step", "action": self.actions[action]}))

    def step(self, action):
        obs, reward, terminated, truncated, info = asyncio.run(
            self._step_async(action)
        )
        return obs, reward, terminated, truncated, info

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        obs = asyncio.run(self._reset_async())
        return obs, {}
