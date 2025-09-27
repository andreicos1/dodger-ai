import asyncio
import json
import numpy as np
import gymnasium as gym
from gymnasium import spaces
import websockets
from sync_env import DodgerEnvGymSync
import os
from gymnasium.wrappers import TimeLimit
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import SubprocVecEnv, VecFrameStack
from stable_baselines3.common.callbacks import EvalCallback
from stable_baselines3.common.utils import get_schedule_fn
from stable_baselines3.common.logger import configure

# Log directory
log_dir = "logs/"
os.makedirs(log_dir, exist_ok=True)

if __name__ == "__main__":
    log_dir = "logs/"
    os.makedirs(log_dir, exist_ok=True)

    def make_env():
        def _init():
            env = DodgerEnvGymSync()
            env = Monitor(env, log_dir)
            # hard-limit episode length to 30 real-world minutes @60 fps
            env = TimeLimit(env, max_episode_steps=60 * 60 * 30)
            return env
        return _init

    num_envs = 8
    vec_env   = SubprocVecEnv([make_env() for _ in range(num_envs)])
    train_env = VecFrameStack(vec_env, n_stack=4)

    # single-environment eval wrapper
    eval_env  = VecFrameStack(SubprocVecEnv([make_env()]), n_stack=4)

    # OVERRIDE HYPER-PARAMETERS WHEN LOADING
    # new hyper-parameters
    new_lr      = 2.5e-4           # constant learning rate
    new_n_steps = 4096             # per env  →  4096*8 = 32 768 collected steps
    new_bsize   = 1024
    new_clip    = 0.15
    new_entc    = 0.002

    custom_objects = {
        "learning_rate": new_lr,
        "n_steps":       new_n_steps,
        "batch_size":    new_bsize,
        "clip_range":    new_clip,
        "ent_coef":      new_entc,
        # schedules built from the new scalars
        "lr_schedule":      get_schedule_fn(new_lr),
        "clip_range_sched": get_schedule_fn(new_clip),
    }

    model = PPO.load(
        "./best_model/best_model.zip",
        env=train_env,
        device="cuda",
        custom_objects=custom_objects,
    )

    # PERIODIC EVALUATION – SAVE THE BEST MODEL
    eval_freq = 100_000 // num_envs      # callback counter is in "env steps"

    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path="./best_model/",
        log_path="./best_model/",
        eval_freq=eval_freq,
        n_eval_episodes=20,
        deterministic=True,
        render=False,
    )
    tb_path = "./ppo_dodger_tensorboard/"
    logger = configure(tb_path, ["stdout", "tensorboard", "log", "json"])
    model.set_logger(logger)

    # CONTINUE TRAINING
    model.learn(
        total_timesteps=5_000_000,     # extra timesteps to collect
        reset_num_timesteps=False,     # keep the timestep counter
        callback=eval_callback,
    )

    model.save("dodger_ppo_framestack_parallel_v2")