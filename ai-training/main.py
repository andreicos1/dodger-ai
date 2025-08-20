import asyncio
import json
import random
import websockets

ACTIONS = ["LEFT", "RIGHT", "UP", "DOWN", "NONE"]


class DodgerEnv:
    def __init__(self, uri="ws://localhost:8080"):
        self.uri = uri
        self.ws = None
        self.state = None
        self.done = False

    async def connect(self):
        if self.ws is None or self.ws.closed:
            self.ws = await websockets.connect(self.uri)

    async def reset(self):
        await self.connect()
        await self.ws.send(json.dumps({"type": "restart"}))
        # Wait for first state
        while True:
            msg = await self.ws.recv()
            data = json.loads(msg)
            if data["type"] == "state":
                self.state = data["state"]
                self.done = self.state.get("gameOver", False)
                return self.state

    async def step(self, action):
        await self.ws.send(json.dumps({"type": "step", "action": action}))
        # Wait for next state
        while True:
            msg = await self.ws.recv()
            data = json.loads(msg)
            if data["type"] == "state":
                self.state = data["state"]
                self.done = self.state.get("gameOver", False)
                # TODO: Replace with real reward function
                reward = 1.0 if not self.done else -10.0
                return self.state, reward, self.done, {}


# Example random-agent loop
async def run_random_agent():
    env = DodgerEnv()
    state = await env.reset()
    print("Initial state:", state)

    for _ in range(100000):  # Run 1000 steps
        action = random.choice(ACTIONS)
        state, reward, done, _ = await env.step(action)
        print("Action:", action, "Reward:", reward, "Done:", done)

        if done:
            print("Game over, restarting...")
            state = await env.reset()


if __name__ == "__main__":
    asyncio.run(run_random_agent())