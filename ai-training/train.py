import os
import numpy as np
from core.dodger_env_gym_train import DodgerEnvGymTrain
from gymnasium.wrappers import TimeLimit

from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import SubprocVecEnv, VecFrameStack
from stable_baselines3.common.callbacks import EvalCallback
from stable_baselines3.common.utils import get_schedule_fn
from stable_baselines3.common.logger import configure
from stable_baselines3.common.evaluation import evaluate_policy

LOG_DIR = "logs/"
os.makedirs(LOG_DIR, exist_ok=True)


class EvalCallbackByLength(EvalCallback):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.best_mean_length = -np.inf

    def _on_step(self) -> bool:
        continue_training = True

        if self.eval_freq > 0 and self.n_calls % self.eval_freq == 0:
            episode_rewards, episode_lengths = evaluate_policy(
                self.model,
                self.eval_env,
                n_eval_episodes=self.n_eval_episodes,
                render=self.render,
                deterministic=self.deterministic,
                return_episode_rewards=True,
            )

            mean_reward = np.mean(episode_rewards)
            mean_length = np.mean(episode_lengths)
            std_length = np.std(episode_lengths)

            if self.verbose >= 1:
                print(f"Eval episodes: {self.n_eval_episodes}")
                print(f"Mean reward: {mean_reward:.2f}")
                print(f"Mean length: {mean_length:.2f} +/- {std_length:.2f}")

            self.logger.record("eval/mean_reward", float(mean_reward))
            self.logger.record("eval/mean_length", float(mean_length))
            self.logger.record("eval/std_length", float(std_length))

            if mean_length > self.best_mean_length:
                self.best_mean_length = mean_length
                if self.verbose >= 1:
                    print(f"New best mean length: {self.best_mean_length:.2f}")
                if self.best_model_save_path is not None:
                    os.makedirs(self.best_model_save_path, exist_ok=True)
                    self.model.save(os.path.join(
                        self.best_model_save_path, "best_model"))

            if self.log_path is not None:
                os.makedirs(self.log_path, exist_ok=True)
                self.evaluations_timesteps.append(self.num_timesteps)
                self.evaluations_results.append(episode_rewards)
                self.evaluations_length.append(episode_lengths)

                np.savez(
                    os.path.join(self.log_path, "evaluations.npz"),
                    timesteps=self.evaluations_timesteps,
                    results=self.evaluations_results,
                    ep_lengths=self.evaluations_length,
                )

            self.last_mean_reward = float(np.mean(episode_rewards))
            continue_training = self._check_success_callback(
            ) if self.callback_on_new_best else True

        return continue_training


if __name__ == "__main__":
    TRAIN_FROM_SCRATCH = True
    os.makedirs(LOG_DIR, exist_ok=True)

    def make_env():
        def _init():
            env = DodgerEnvGymTrain(randomize_dimensions=True)
            env = Monitor(env, LOG_DIR)
            env = TimeLimit(env, max_episode_steps=5000)
            return env
        return _init

    num_envs = 8
    vec_env = SubprocVecEnv([make_env() for _ in range(num_envs)])
    train_env = VecFrameStack(vec_env, n_stack=4)

    # single-environment eval wrapper
    eval_env = VecFrameStack(SubprocVecEnv([make_env()]), n_stack=4)

    new_lr = 3e-4
    new_n_steps = 2048
    new_bsize = 256
    new_clip = 0.2
    new_entc = 0.01

    custom_objects = {
        "learning_rate": new_lr,
        "n_steps":       new_n_steps,
        "batch_size":    new_bsize,
        "clip_range":    new_clip,
        "ent_coef":      new_entc,
        "lr_schedule":      get_schedule_fn(new_lr),
        "clip_range_sched": get_schedule_fn(new_clip),
    }

    tb_path = "./ppo_dodger_tensorboard/"

    if TRAIN_FROM_SCRATCH:
        model = PPO(
            "MlpPolicy",
            train_env,
            learning_rate=new_lr,
            n_steps=new_n_steps,
            batch_size=new_bsize,
            clip_range=new_clip,
            ent_coef=new_entc,
            n_epochs=10,
            gamma=0.995,
            gae_lambda=0.95,
            max_grad_norm=0.5,
            verbose=1,
            device="cuda",
            tensorboard_log=tb_path,
        )
    else:
        model = PPO.load(
            "./best_model/best_model.zip",
            env=train_env,
            device="cuda",
            custom_objects=custom_objects,
        )
    # evaluate every ~100 000 environment steps & save the best model
    eval_freq = 100_000 // num_envs

    eval_callback = EvalCallbackByLength(
        eval_env,
        best_model_save_path="./best_model/",
        log_path="./best_model/",
        eval_freq=eval_freq,
        n_eval_episodes=20,
        deterministic=True,
        render=False,
        verbose=1,
    )
    logger = configure(tb_path, ["stdout", "tensorboard", "log", "json"])
    model.set_logger(logger)

    # continue training
    model.learn(
        total_timesteps=5_000_000,
        reset_num_timesteps=False,
        callback=eval_callback,
    )

    model.save("dodger_ppo_framestack_parallel_v2")
