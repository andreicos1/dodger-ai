import os
from core.dodger_env_gym_train import DodgerEnvGymTrain
from gymnasium.wrappers import TimeLimit

from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import SubprocVecEnv
from stable_baselines3.common.callbacks import EvalCallback

LOG_DIR = "logs/"
os.makedirs(LOG_DIR, exist_ok=True)
TRAIN_FROM_SCRATCH = True


if __name__ == "__main__":
    def make_env():
        def _init():
            env = DodgerEnvGymTrain(randomize_dimensions=False)
            env = Monitor(env, LOG_DIR)
            env = TimeLimit(env, max_episode_steps=10000)
            return env
        return _init

    num_envs = 4
    train_env = SubprocVecEnv([make_env() for _ in range(num_envs)])
    eval_env = SubprocVecEnv([make_env()])

    if TRAIN_FROM_SCRATCH:
        policy_kwargs = dict(net_arch=[256, 128])
        model = PPO(
            "MlpPolicy",
            train_env,
            learning_rate=3e-4,
            n_steps=4096,
            batch_size=216,
            clip_range=0.25,
            ent_coef=0.02,
            vf_coef=0.3,
            n_epochs=15,
            gamma=0.99,
            gae_lambda=0.95,
            max_grad_norm=0.5,
            policy_kwargs=policy_kwargs,
            verbose=1,
            device="cpu",
            tensorboard_log="./ppo_dodger_tensorboard/",
        )
    else:
        model = PPO.load(
            "./best_model_new/best_model.zip",
            env=train_env,
            device="cpu",
            tensorboard_log="./ppo_dodger_tensorboard/",
        )
        model.policy.value_net.reset_parameters()

    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path="./best_model_new/",
        log_path="./best_model_new/",
        eval_freq=50_000 // num_envs,
        deterministic=True,
        render=False,
        verbose=1,
    )

    model.learn(
        total_timesteps=10_000_000,
        reset_num_timesteps=TRAIN_FROM_SCRATCH,
        callback=eval_callback,
    )

    model.save("dodger_ppo_framestack_parallel")
