from gymnasium.envs.registration import register
from .grid_world import GridWorldEnv

register(
    id="GridWorld-v0",
    entry_point="custom_envs.grid_world:GridWorldEnv"
)
