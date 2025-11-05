import numpy as np


def get_bin(value, bin_size, n_bins):
    """ Return the bin index for a given value. """
    bin_index = int(np.floor(value / bin_size))
    return min(bin_index, n_bins - 1)


def bin_data(samples: list[tuple], n_bins:int, max_value:float=None) -> tuple:
    """ Bin the data and return mean and std deviation for each bin. """
    if max_value is None:
        max_value = max(x for x, y in samples if np.isfinite(x))
        
    print(samples)
    
    bin_size = max_value / n_bins
    bins = [[] for _ in range(n_bins)]  # A list of lists to hold samples for each bin
    # the bin values (center of bin)
    print(bin_size, '\n', max_value, '\n', n_bins)
    bin_pos_center = [i * bin_size + bin_size / 2 for i in range(n_bins)]
    
    for sample in samples:
        x, y = sample
        bin_index = get_bin(x, bin_size, n_bins)
        bins[bin_index].append(y)
        if y ==0:
            print(f"Value {y} at x={x} goes to bin {bin_index} (bin range: {bin_index*bin_size} - {(bin_index+1)*bin_size})")
        
    # mean and std deviation for each bin
    
    bin_means = [np.mean(b) if b else np.nan for b in bins]
    bin_stds  = [np.std(b)  if b else np.nan for b in bins]
    print(bins)
    print(bin_means)
    bin_pos_center, bin_means, bin_stds = np.array(bin_pos_center), np.array(bin_means), np.array(bin_stds)
        
    return bin_pos_center, bin_means, bin_stds
    
    
    
    
    
if __name__ == "__main__":
    # Example usage
    samples = ((20, 1), (20,2), (15, 3), (22, 4), (30, 5), (25, 6), (40, 7), (35, 8), (45, 9), (50, 10))

    n_bins = 6
    max_value = 60
    bins, means, stds = bin_data(samples, n_bins, max_value)
    
    print(bins)
    print("Bin Means:", means)
    print("Bin Stds:", stds)