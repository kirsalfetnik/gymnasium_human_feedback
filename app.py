import datetime
import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import gymnasium as gym
import ale_py
from PIL import Image
import io
import base64
import subprocess
import pandas as pd
from setuptools.command.register import register

from env_config import ENVIRONMENTS
import uuid
import threading
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from figure import read_csv, pre_processing, plot_data
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__)
app.secret_key = 'geheimes-passwort'  # nötig für Sessions

user_data = {}
ENV_NAMES = list(ENVIRONMENTS.keys())
gym.register_envs(ale_py)

REPO_URL = os.environ["REPO_URL"]
LOCAL_DATA_PATH = "/tmp/repo"
GITLAB_TOKEN = os.environ["GITHUB_TOKEN"]
PROJECT_ID = "73346802"
FILE_PATH = "rewards.csv"
SERVER_NAME = os.environ.get("SERVER_NAME", "default")
BRANCH = f"results/{SERVER_NAME}"


def make_env(env_name):
    env_cfg = ENVIRONMENTS[env_name]
    return gym.make(env_cfg["id"], render_mode="rgb_array", **env_cfg["kwargs"])


def get_rendered_frame(env):
    frame = env.render()
    image = Image.fromarray(frame)
    buf = io.BytesIO()
    image.save(buf, format='PNG')
    buf.seek(0)
    base64_image = base64.b64encode(buf.read()).decode('utf-8')
    return f"data:image/png;base64,{base64_image}"

def ensure_repo():
    """Repo clonen falls nötig und Git-Config setzen."""
    if not os.path.exists(LOCAL_DATA_PATH):
        subprocess.run(["git", "clone", REPO_URL, LOCAL_DATA_PATH], check=True)
    else:
        subprocess.run(
            ["git", "remote", "set-url", "origin", REPO_URL],
            cwd=LOCAL_DATA_PATH,
            check=True
        )
    # Git-Author-Identity setzen (nur lokal im Repo)
    subprocess.run(["git", "config", "user.name", "ci-bot"], cwd=LOCAL_DATA_PATH, check=True)
    subprocess.run(["git", "config", "user.email", "ci-bot@example.com"], cwd=LOCAL_DATA_PATH, check=True)
    branches = subprocess.check_output(
        ["git", "ls-remote", "--heads", "origin", BRANCH],
        cwd=LOCAL_DATA_PATH
    ).decode().strip()

    if not branches:
        # Branch existiert noch nicht → neu erstellen aus main
        subprocess.run(["git", "checkout", "main"], cwd=LOCAL_DATA_PATH, check=True)
        subprocess.run(["git", "pull", "origin", "main"], cwd=LOCAL_DATA_PATH, check=True)
        subprocess.run(["git", "checkout", "-b", BRANCH], cwd=LOCAL_DATA_PATH, check=True)
        subprocess.run(["git", "push", "-u", "origin", BRANCH], cwd=LOCAL_DATA_PATH, check=True)
    else:
        # Branch existiert schon → wechseln und updaten
        subprocess.run(["git", "fetch", "origin"], cwd=LOCAL_DATA_PATH, check=True)
        subprocess.run(["git", "checkout", BRANCH], cwd=LOCAL_DATA_PATH, check=True)
        subprocess.run(["git", "pull", "origin", BRANCH], cwd=LOCAL_DATA_PATH, check=True)

def submit_to_csv_background(name, reward, env_name, steps):
    def worker():
        try:
            submit_to_csv(name, reward, env_name, steps)
        except Exception as e:
            print(f"[Git Worker] Error: {e}")

    threading.Thread(target=worker, daemon=True).start()

def submit_to_csv(name, reward, env_name, steps):
    ensure_repo()

    csv_path = os.path.join(LOCAL_DATA_PATH, "rewards.csv")

    subprocess.run(["git", "pull", "origin", BRANCH], cwd=LOCAL_DATA_PATH, check=True)

    dataframe = pd.read_csv(csv_path)
    new_row = {
        "player_name": name,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "env_name": env_name,
        "reward": reward,
        "steps": steps
    }
    dataframe = pd.concat([dataframe, pd.DataFrame([new_row])], ignore_index=True)
    dataframe.to_csv(csv_path, index=False)

    subprocess.run(["git", "add", "rewards.csv"], cwd=LOCAL_DATA_PATH, check=True)
    subprocess.run(["git", "commit", "-m", "appended new entry to csv"], cwd=LOCAL_DATA_PATH, check=True)

    try:
        subprocess.run(["git", "push", "origin", BRANCH], cwd=LOCAL_DATA_PATH, check=True)
    except subprocess.CalledProcessError:
        subprocess.run(["git", "pull", "--rebase", "origin", BRANCH], cwd=LOCAL_DATA_PATH, check=True)
        subprocess.run(["git", "push", "origin", BRANCH], cwd=LOCAL_DATA_PATH, check=True)


#not in use anymore
def update_user_visualization(user_id):
    user = user_data.get(user_id)
    if not user:
        return

    ensure_repo()
    # Ensure CSV exists
    csv_path = os.path.join(LOCAL_DATA_PATH, "rewards.csv")
    if not os.path.exists(csv_path):
        subprocess.run(["git", "clone", REPO_URL, LOCAL_DATA_PATH], check=True)
        csv_path = os.path.join(LOCAL_DATA_PATH, "rewards.csv")

    # Load and preprocess data using figure.py
    df = pd.read_csv(csv_path, sep=',', encoding='utf-8-sig')
    if df[df["env_name"] == user["env_name"]].empty:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.text(0.5, 0.5, "No data yet for this environment", ha="center", va="center", fontsize=12)
        ax.set_axis_off()
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        user_data[user_id]["score_plot"] = "data:image/png;base64," + base64.b64encode(buf.read()).decode("utf-8")
        return

    df = pre_processing(df)

    # Generate the plot exactly as figure.py does
    fig = plot_data(df, env_name=user["env_name"], output_path="/tmp/temp_plot.png")

    # Convert plot to Base64
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=300)
    plt.close(fig)
    buf.seek(0)
    base64_image = base64.b64encode(buf.read()).decode('utf-8')

    # Store in session data for the user
    user_data[user_id]["score_plot"] = f"data:image/png;base64,{base64_image}"

def end_episode(name, reward, env_name, steps, user_id):
    if user_id not in user_data:
        return
    user = user_data.get(user_id)

    ensure_repo()

    csv_path = os.path.join(LOCAL_DATA_PATH, "rewards.csv")
    t_csv_path = os.path.join(LOCAL_DATA_PATH, "trajectories.csv")
    df = pd.read_csv(csv_path, sep=',', encoding='utf-8-sig')
    episode_id = uuid.uuid4()
    new_row = {
        "id": episode_id,
        "player_name": name,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "env_name": env_name,
        "reward": reward,
        "steps": steps
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    df_t = pd.read_csv(t_csv_path, sep=',', encoding='utf-8-sig')
    new_rows = user["trajectories"]
    for t in new_rows:
        t["episode_id"] = episode_id
    df_t = pd.concat([df_t, pd.DataFrame(new_rows)], ignore_index=True)

    threading.Thread(target=save_episode, args=(df, df_t, csv_path, t_csv_path), daemon=True).start()
    threading.Thread(target=build_visualization, args=(user_id, env_name, df), daemon=True).start()


def save_episode(df, df_t, csv_path, t_csv_path):
    df_t.to_csv(t_csv_path, index=False)
    df.to_csv(csv_path, index=False)

    subprocess.run(["git", "add", "rewards.csv"], cwd=LOCAL_DATA_PATH, check=True)
    subprocess.run(["git", "add", "trajectories.csv"], cwd=LOCAL_DATA_PATH, check=True)
    subprocess.run(["git", "commit", "-m", "appended new entry to csv"], cwd=LOCAL_DATA_PATH, check=True)

    try:
        subprocess.run(["git", "push", "origin", BRANCH], cwd=LOCAL_DATA_PATH, check=True)
    except subprocess.CalledProcessError:
        subprocess.run(["git", "pull", "--rebase", "origin", BRANCH], cwd=LOCAL_DATA_PATH, check=True)
        subprocess.run(["git", "push", "origin", BRANCH], cwd=LOCAL_DATA_PATH, check=True)

def build_visualization(user_id, env_name, df):
    if user_id not in user_data:
        return
    user = user_data.get(user_id)

    plot_path = f"/tmp/{env_name}.svg"
    df = pre_processing(df.copy(deep=True))

    fig = plot_data(df, env_name=env_name, output_path=plot_path)

    if os.path.exists(plot_path):
        with open(plot_path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode('utf-8')
            plot = f"data:image/svg+xml;base64,{base64_image}"
            user["score_plot"] = plot
    else:
        plot = None
        user["score_plot"] = None

    #with open(plot_path, "rb") as f:
    #    base64_image = base64.b64encode(f.read()).decode('utf-8')
    #user_data[user_id]["score_plot"] = f"data:image/png;base64,{base64_image}"

def build_all_visualizations(user_id, df):
    if user_id not in user_data:
        return
    user = user_data.get(user_id)

    if user.get("visualizations_running"):
        return
    user["visualizations_running"] = True
    try:
        for env_name in ENV_NAMES:
            if os.path.exists(f"/tmp/{env_name}.svg"):
                continue

            build_visualization(user_id, env_name, df)
    finally:
        user["visualizations_running"] = False


@app.before_request
def ensure_session():
    if "id" not in session:
        session["id"] = str(uuid.uuid4())

    if session["id"] not in user_data:
        user_data[session["id"]] = {}


@app.route('/', methods=['GET', 'POST'])
def index():
    ensure_session()

    user = user_data.get(session["id"])
    if user is None:
        user_data[session["id"]] = {}
        user = user_data[session["id"]]

    if request.method == 'POST':
        name = request.form.get('name')
        env_choice = request.form.get('env_name')
        env = make_env(env_choice)
        user["obs"], info = env.reset()

        user["env"] = env
        user["total_reward"] = 0
        user["env_name"] = env_choice
        user["player_name"] = name
        user["steps"] = 0
        user["trajectories"] = []

        return redirect(url_for('game'))

    player_names = []
    ensure_repo()
    csv_path = os.path.join(LOCAL_DATA_PATH, "rewards.csv")

    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path, sep=',', encoding='utf-8-sig')
        threading.Thread(
            target=build_all_visualizations,
            args=(session["id"], df),
            daemon=True
        ).start()

        if "player_name" in df.columns:
            player_names = sorted(df["player_name"].dropna().unique().tolist())

    return render_template(
        'index.html',
        env_names=ENV_NAMES,
        player_names=player_names
    )


@app.route('/game')
def game():
    user = user_data.get(session["id"])
    if not user:
        return redirect(url_for("index"))
    env = user["env"]
    env_name = user["env_name"]
    img_data = get_rendered_frame(env)

    env_cfg = ENVIRONMENTS[env_name]
    controls = env_cfg.get("controls", {})
    description = env_cfg.get("description", "")

    plot_path = f"/tmp/{env_name}.svg"
    if os.path.exists(plot_path):
        with open(plot_path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode('utf-8')
            plot = f"data:image/svg+xml;base64,{base64_image}"
            user["score_plot"] = plot
    else:
        plot = None
        user["score_plot"] = None

    score_plot = plot
    return render_template(
        'game.html',
        image_data=img_data,
        total_reward=user["total_reward"],
        name=user["player_name"],
        controls=controls,
        description=description,
        score_plot=score_plot
    )


@app.route('/step', methods=['POST'])
def step():
    user = user_data.get(session["id"])
    env = user["env"]
    total_reward = user["total_reward"]
    steps = user["steps"]
    data = request.get_json()
    action = data.get('action')

    if action == 'reset':
        total_reward = 0
        steps = 0
        user["obs"], _ = env.reset()
        user["trajectories"] = []
    else:
        action = int(action)
        obs, reward, terminated, truncated, _ = env.step(action)
        total_reward += reward
        steps += 1

        t_data = {"player_name": user["player_name"], "env_name": user["env_name"], "step": steps, "state": user["obs"], "action": action, "reward": reward}
        user["trajectories"].append(t_data)
        user["obs"] = obs

        if terminated or truncated:
            threading.Thread(
                target=end_episode,
                args=(user["player_name"], total_reward, user["env_name"], steps, session["id"]),
                daemon=True
            ).start()
            env.reset()
            total_reward = 0
            steps = 0

    user["total_reward"] = total_reward
    user["steps"] = steps
    img_data = get_rendered_frame(env)
    return jsonify({
        'image_data': img_data,
        'total_reward': total_reward,
        'score_plot': user["score_plot"]
    })


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
