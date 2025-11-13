from pandas.core.window.doc import kwargs_scipy

from custom_envs.register_envs import *

ENVIRONMENTS = {
    "FrozenLake": {
        "id": "FrozenLake-v1",
        "kwargs": {
            "is_slippery": False
        },
        "controls": [
            {"key": "ArrowLeft", "label": "Move Left", "action": 0},
            {"key": "ArrowDown", "label": "Move Down", "action": 1},
            {"key": "ArrowRight", "label": "Move Right", "action": 2},
            {"key": "ArrowUp", "label": "Move Up", "action": 3}
        ],
        "description": "Frozen lake involves crossing a frozen lake from start to goal without falling into any holes by walking over the frozen lake. The player may not always move in the intended direction due to the slippery nature of the frozen lake."
    },
    "Taxi": {
        "id": "Taxi-v3",
        "kwargs": {},
        "controls": [
            {"key": "ArrowLeft", "label": "Move West", "action": 3},
            {"key": "ArrowDown", "label": "Move South", "action": 0},
            {"key": "ArrowRight", "label": "Move East", "action": 2},
            {"key": "ArrowUp", "label": "Move North", "action": 1},
            {"key": "w", "label": "Pick Up Passenger", "action": 4},
            {"key": "e", "label": "Drop Passenger", "action": 5}
        ],
        #"description": "The Taxi Problem involves navigating to passengers in a grid world, picking them up and dropping them off at one of four locations."
    },
    "GridWorld": {
        "id": "GridWorld-v0",
        "kwargs": {},
        "controls": [
            {"key": "ArrowRight", "label": "Move Right", "action": 0},
            {"key": "ArrowDown", "label": "Move Down", "action": 1},
            {"key": "ArrowLeft", "label": "Move Left", "action": 2},
            {"key": "ArrowUp", "label": "Move Up", "action": 3},
        ],
        "description": "This is a custom environment created for the purpose of testing the Gymplayer logic."
    },
    "Pacman": {
        "id": "ALE/Pacman-v5",
        "kwargs": {},
        "controls": [
            {"key": "ArrowUp", "label": "Move Up", "action": 1},
            {"key": "ArrowRight", "label": "Move Right", "action": 2},
            {"key": "ArrowLeft", "label": "Move Left", "action": 3},
            {"key": "ArrowDown", "label": "Move Down", "action": 4}
        ]
    }
}
