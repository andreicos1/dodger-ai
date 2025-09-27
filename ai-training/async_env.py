import asyncio
import json
import websockets
from core_env import DodgerEnvGymCore, ACTIONS

class DodgerEnvGymAsync:
    def __init__(self, uri="ws://localhost:8080", width=800, height=600, max_blocks=10):
        self.uri = uri
        self.ws = None
        self.core = DodgerEnvGymCore(width, height, max_blocks)
        self.state_queue = asyncio.Queue()
        self.listener_task = None

    async def _connect(self):
        if self.ws is None or self.ws.closed:
            self.ws = await websockets.connect(self.uri)

    async def become_owner(self):
        await self._connect()
        await self.ws.send(json.dumps({"type": "become_shared_owner"}))
        print("Sent become_shared_owner")

        # Start background listener
        self.listener_task = asyncio.create_task(self._listen())

    async def _listen(self):
        """Background task: continuously receive state messages."""
        try:
            async for msg in self.ws:
                data = json.loads(msg)
                if data["type"] == "state":
                    await self.state_queue.put(data["state"])
        except Exception as e:
            print("Listener stopped:", e)

    async def reset(self):
        await self._connect()
        await self.ws.send(json.dumps({"type": "restart"}))
        state = await self.state_queue.get()
        self.core.state = state
        self.core.done = state.get("gameOver", False)
        return self.core.process_state(state)

    async def step(self, action):
        await self.ws.send(json.dumps({"type": "step", "action": ACTIONS[action]}))
        state = await self.state_queue.get()
        self.core.state = state
        self.core.done = state.get("gameOver", False)
        reward = self.core.compute_reward(state)
        return (
            self.core.process_state(state),
            reward,
            self.core.done,
            False,
            {},
        )

    async def close(self):
        if self.listener_task:
            self.listener_task.cancel()
        if self.ws and not self.ws.closed:
            await self.ws.close()