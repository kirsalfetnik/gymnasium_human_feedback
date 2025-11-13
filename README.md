<p style="text-align: center;">
  <img src="static/GymCapture_Logo.svg" alt="GymCapture Logo" width="200"><br>
  <strong>GymCapture</strong>
</p>



Capture the performance of human players for any [Gymnasium](https://gymnasium.farama.org/) compatible environment.  
Distribute the app with this link: https://gym-player.onrender.com

## Adding new Environments

The app reads available environments from a central config file `env_config.py`, which consists of a dictionary `ENVIRONMENTS`. Environments must support `render_mode="rgb_array"` and have a discrete action space.
Each entry has the following structure and new environments can be added by adding another entry:

```
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
        "description": "Frozen lake involves..." 
    }
}
```

- give the name of your environment as **key** (e.g. `"FrozenLake"`). This is the name that the user can see in the dropdown menu.
- `"id"`: the id used in the `gym.make(...)` call. The app calls `gym.make(env_cfg["id"], render_mode="rgb_array", **env_cfg["kwargs"])`. Make sure the environment supports `render_mode="rgb_array"`!
- `"kwargs"`: any other arguments given to the `gym.make(...)` call
- `"controls"`: a list containing one object for each action of the environment. The objects look like `{"key": <KeyCode>, "label": <Label>, "action": <action>}`
  - `<KeyCode>`: The code for the button used in Javascript Keydown event.key ([List of event.key codes](https://www.freecodecamp.org/news/javascript-keycode-list-keypress-event-key-codes/))
  - `<Label>`: The action description shown to the user in the app
  - `<action>`: The action values given to the `env.step()` call.
- `"description"`: An **optional** description of the gymnasium environment, that gets displayed in the app.
### Adding Custom Environments

To create a custom environment you can follow this [tutorial](https://gymnasium.farama.org/introduction/create_custom_env/) provided by gymnasium.
Custom environments can be added as playable environments the following way:

1) Copy the source code of the custom environment into the `custom_envs` folder. Make sure that your custom environment supports `render_mode="rgb_array"`.
2) All python libraries that need to be installed for your custom environment to function need to be included in the `requirements.txt` file.
3) Add a new entry in the `register_envs.py` file like this:

```
from .<your-env> import <your-env-class>

register(
    id="<your-env-id>",
    entry_point="custom_envs.<your-env>:<your-env-class>"
)
```
- `<your-env>`: the name of your source file without `.py`
- `<your-env-class>`: the name of your environment class in your source file looking something like this(`class <your-env-class>(gym.Env):`)
- `<your-env-id>`: This is where you assign the id used in the `gym.make(...)` call.

4. Add an entry to the config file `env_config.py` as described above.

## Hosting your own Gymplayer instance

The following provides a guide on how to host a new gymplayer instance either locally or in the cloud.

### Prerequisites

- [Python](https://www.python.org/downloads/) 3.9+ 
- a new GitHub- or GitLab-Repo with all project files
- a personal access token which provides authentication for that repository
- a `.env` file (_Do not share the .env file or upload it to your repo!_) with:
```
GITHUB_TOKEN=<your-token>
REPO_URL=https://<your-username>:<your-token>@<your-repo-url>
PORT=5000
```
- `<your-token>`: the personal access token granting access to your repository.
- `<your-username>`: the username you use in GitLab / GitHub
- `<your-repo-url>`: the url to your repository. For example for this repo: `gitlab.com/chair-of-artificial-intelligence-and-formal-methods/gymnasium-player-human-performance.git`

### Local deployment

1. Clone the repository:
```
git clone <your-repo-url>
cd <your-local-project-folder>
```
2. install the required python packages 
```
pip install -r requirements.txt
```
3. Save the `.env` file on the same level as `app.py`
4. Start the app:
```
python app.py
```
5. Open in browser:
http://localhost:5000

### Cloud Deployment

This repository is hosted on [render](https://render.com/). Feel free to host where you want, the following guide will describe how the project can be hosted on render.

1. Log in to render or create a new account
2. On your dashboard click _Add new_ and then _Web Service_
3. Choose your repository for the source code.
4. As build command use `pip install -r requirements.txt`
5. As start command use `python app.py`
6. add your `.env`as a secret file
7. Click on Deploy Web Service
8. You will receive a public url to access your site