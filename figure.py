import matplotlib.pyplot as plt
import pandas as pd

from binning import bin_data

def read_csv(path) -> pd.DataFrame:
    """Reads a CSV file and returns a pandas DataFrame."""
    return pd.read_csv(path, sep=',', header=0)

def pre_processing(df: pd.DataFrame) -> pd.DataFrame:
    df['steps'] = df.groupby(['player_name', 'env_name'])['steps'].cumsum()
    return df

def plot_data(df: pd.DataFrame, env_name: str, output_path: str):
    WINDOW_SIZE = 1
    N_BINS = 10
    
    # get environment name from dataframe
    df = df[df['env_name'] == env_name]
    
    if df.empty:
        raise ValueError(f"Environment name '{env_name}' not found in the data.")
        return
    
    # create the figuer
    fig = plt.figure(figsize=(10, 6))
    # bold font
    plt.title(f"Environment: {env_name}", fontsize=16, fontweight='bold')
    plt.xlabel("Steps")
    plt.ylabel("Reward")
    
    cmap = plt.get_cmap("tab10")
    
    # get unique player names
    player_names = df['player_name'].unique()
    
    # plot average reward per player with std deviation as shaded area
    if len(player_names) != 0:
        ddf = df[['steps', 'reward']]
        
        bin_pos_center, mean, std = bin_data(ddf.values.tolist(), n_bins=N_BINS)
        print(bin_pos_center)
        print(mean)
        print(std.round(1))
        
        mask = ~pd.isna(mean)
        bin_pos_center = bin_pos_center[mask]
        mean = mean[mask]
        std = std[mask]
    
        plt.plot(bin_pos_center, mean, label="Average Reward (all players)", marker='o', color='black', lw=3, alpha=0.8, zorder=10)
        plt.fill_between(bin_pos_center, mean - std, mean + std, color='gray', alpha=0.2, label="Std Deviation")
        
    
    for i, player in enumerate(player_names):
        color = cmap(i % 10)
        # ddf = range(len(df[df['player_name'] == player]))
        ddf = df[df['player_name'] == player]
        x = ddf['steps']
        y = ddf['reward']
        
        # sum previous steps so we obtain current cumulative step count
        # x = x.cumsum()

        # rolling average for smoothing
        rolling_window = y.rolling(window=WINDOW_SIZE, min_periods=0)
        y = rolling_window.mean()
        y_std = rolling_window.std()
        # plot mean
        plt.plot(x, y, label=f"{player} (rolling avg $n={WINDOW_SIZE}$)", marker="o", linestyle='--', c=color, alpha=0.5)
        # plot std deviation as shaded area
        plt.fill_between(x, y -y_std, y + y_std, linestyle=':', alpha=0.2, color=color)
        
        
        
    # legend outside the plot, on the right
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    # plt.show()
    
    return fig


if __name__ == "__main__":
    data_path = "rewards.csv"  # Path to your CSV file
    output_path = "rewards.svg"  # Path to save the plot
    env_name = "FrozenLake-v1"  # Example environment name

    df = read_csv(data_path)
    df = pre_processing(df)
    
    
    # print(df)
    fig = plot_data(df, env_name, output_path)
    plt.show()