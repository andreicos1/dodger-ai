from core.dodger_env_gym_core import DodgerEnvGym


class DodgerEnvGymEval(DodgerEnvGym):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
