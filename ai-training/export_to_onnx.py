import torch
import numpy as np
from stable_baselines3 import PPO

model = PPO.load("best_model/best_model.zip", device="cpu")
policy = model.policy


class ActionExtractor(torch.nn.Module):
    def __init__(self, policy):
        super().__init__()
        self.policy = policy

    def forward(self, obs):
        features = self.policy.extract_features(obs)
        latent_pi = self.policy.mlp_extractor.forward_actor(features)
        action_logits = self.policy.action_net(latent_pi)
        return action_logits


wrapper = ActionExtractor(policy)
wrapper.eval()

dummy_input = torch.randn(1, 124)

with torch.no_grad():
    test_output = wrapper(dummy_input)
    print(f"Output shape: {test_output.shape}")
    print(f"Output: {test_output}")

torch.onnx.export(
    wrapper,
    dummy_input,
    "dodger_model.onnx",
    export_params=True,
    opset_version=14,
    input_names=['observation'],
    output_names=['action_logits'],
    dynamic_axes={'observation': {0: 'batch_size'}}
)
print("Model exported successfully")
