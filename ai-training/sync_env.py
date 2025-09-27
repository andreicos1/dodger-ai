# sync_env.py
import asyncio
import threading
import gymnasium as gym
from async_env import DodgerEnvGymAsync

class DodgerEnvGymSync(gym.Env):
    """
    Sync wrapper for SB3 training.
    Runs the async env in a background thread with its own event loop.
    """

    metadata = {"render_modes": []}

    def __init__(self, uri="ws://localhost:8080", width=800, height=600, max_blocks=10):
        super().__init__()
        self.async_env = DodgerEnvGymAsync(uri, width, height, max_blocks)

        # Expose spaces
        self.action_space = self.async_env.core.action_space
        self.observation_space = self.async_env.core.observation_space

        # Background event loop
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.loop.run_forever, daemon=True)
        self.thread.start()

        # 🔑 Do handshake once at startup
        self._run(self.async_env.become_owner())

    def _run(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self.loop).result()

    def reset(self, seed=None, options=None):
        obs = self._run(self.async_env.reset())
        return obs, {}

    def step(self, action):
        obs, reward, terminated, truncated, info = self._run(self.async_env.step(action))
        return obs, reward, terminated, truncated, info

    def close(self):
        self._run(self.async_env.close())
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.thread.join()