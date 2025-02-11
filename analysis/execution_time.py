import os
import glob
import pandas as pd

def compute_mean_std(directory, nb_ops):
    # Define the file pattern to search for
    pattern = os.path.join(directory, f"**/perf_*_{nb_ops}.csv")
    files = glob.glob(pattern, recursive=True)

    if not files:
        print(f"No files found for NB_OPS={nb_ops}")
        return

    time_elapsed_values = []

    # Loop through all matching files
    for file in files:
        try:
            # Read the CSV file
            df = pd.read_csv(file)
            # Append the time_elapsed column to the list
            time_elapsed_values.extend(df["time_elapsed"].dropna())
        except Exception as e:
            print(f"Error reading file {file}: {e}")

    if not time_elapsed_values:
        print(f"No valid time_elapsed values found in files for NB_OPS={nb_ops}")
        return

    # Compute mean and standard deviation
    mean_time = sum(time_elapsed_values) / len(time_elapsed_values)
    std_dev_time = (sum((x - mean_time) ** 2 for x in time_elapsed_values) / len(time_elapsed_values)) ** 0.5

    print(f"Results for NB_OPS={nb_ops}:")
    print(f"  Mean time_elapsed: {mean_time:.6f} seconds")
    print(f"  Standard deviation: {std_dev_time:.6f} seconds")

# Example usage
# Replace "your_directory_path" with the actual path to the directory containing the files
print("For Ubuntu")
directory = "./batches/ubuntu2404nfs-6.8-0.d/results-ubuntu2404nfs-6.8-0.d/"
nb_ops = 25  # Change this to 250, 2500, or 25000 as needed
compute_mean_std(directory, nb_ops)
nb_ops = 250  # Change this to 250, 2500, or 25000 as needed
compute_mean_std(directory, nb_ops)
nb_ops = 2500  # Change this to 250, 2500, or 25000 as needed
compute_mean_std(directory, nb_ops)
nb_ops = 25000  # Change this to 250, 2500, or 25000 as needed
compute_mean_std(directory, nb_ops)

print("For Debian")
directory = "./batches/debian11-5.10-0.d/results-debian11-5.10-0.d/"
nb_ops = 25  # Change this to 250, 2500, or 25000 as needed
compute_mean_std(directory, nb_ops)
nb_ops = 250  # Change this to 250, 2500, or 25000 as needed
compute_mean_std(directory, nb_ops)
nb_ops = 2500  # Change this to 250, 2500, or 25000 as needed
compute_mean_std(directory, nb_ops)
nb_ops = 25000  # Change this to 250, 2500, or 25000 as needed
compute_mean_std(directory, nb_ops)

print("For Powerapi")
directory = "./results_powerapi2u"
nb_ops = 25  # Change this to 250, 2500, or 25000 as needed
compute_mean_std(directory, nb_ops)
nb_ops = 250  # Change this to 250, 2500, or 25000 as needed
compute_mean_std(directory, nb_ops)
nb_ops = 2500  # Change this to 250, 2500, or 25000 as needed
compute_mean_std(directory, nb_ops)
nb_ops = 25000  # Change this to 250, 2500, or 25000 as needed
compute_mean_std(directory, nb_ops)
