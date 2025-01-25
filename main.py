import subprocess
import time
from datetime import datetime
import argparse
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
import os
import numpy as np
from datetime import timedelta
import sys
import matplotlib.dates as mdates


def collect_container_stats(container_name, output_file):
    """
    Collect CPU, memory, and disk I/O usage for a specific Docker container
    and write it to a file with a 5-second interval.

    Args:
        container_name (str): The name or ID of the Docker container.
        output_file (str): Path to the output file.
    """
    # Clear the file contents before starting
    open(output_file, "w").close()

    with open(output_file, "a") as f:
        # Add a header to the file
        f.write(
            "Timestamp,Container,CPU_Usage,Memory_Usage,Memory_Percent,Disk_Read,Disk_Write\n"
        )

        while True:
            try:
                # Run docker stats command for the specified container
                result = subprocess.run(
                    [
                        "docker",
                        "stats",
                        container_name,
                        "--no-stream",
                        "--format",
                        "{{.Container}},{{.CPUPerc}},{{.MemUsage}},{{.MemPerc}},{{.BlockIO}}",
                    ],
                    stdout=subprocess.PIPE,
                    text=True,
                )

                # Parse the output
                if result.stdout.strip():
                    stats = result.stdout.strip().split(",")
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    container_id = stats[0]
                    cpu_usage = stats[1]
                    mem_usage = stats[2]
                    mem_percent = stats[3]
                    block_io = stats[4]

                    # Parse Block I/O (Disk I/O) stats
                    disk_read, disk_write = (
                        block_io.split(" / ") if " / " in block_io else (block_io, "0B")
                    )

                    # Write to the file
                    f.write(
                        f"{timestamp},{container_id},{cpu_usage},{mem_usage},{mem_percent},{disk_read},{disk_write}\n"
                    )
                    f.flush()  # Ensure data is written immediately

                # Wait for 5 seconds
                time.sleep(1)
            except KeyboardInterrupt:
                print("\nExiting on user interruption...")
                break
            except Exception as e:
                print(f"An error occurred: {e}")
                break


def analyze_max_usage(csv_file):
    """
    Analyze the maximum resource usage from the container statistics CSV file.
    """
    try:
        df = pd.read_csv(csv_file)

        # Convert percentage strings to float values
        df["CPU_Usage"] = df["CPU_Usage"].str.rstrip("%").astype(float)
        df["Memory_Percent"] = df["Memory_Percent"].str.rstrip("%").astype(float)

        # Convert disk I/O values to numeric (MB)
        def convert_to_mb(value):
            value = value.strip()
            if "GB" in value:
                return float(value.rstrip("GB")) * 1024
            elif "MB" in value:
                return float(value.rstrip("MB"))
            elif "kB" in value:
                return float(value.rstrip("kB")) / 1024
            elif "B" in value:
                return float(value.rstrip("B")) / (1024 * 1024)
            return 0

        df["Disk_Read_MB"] = df["Disk_Read"].apply(convert_to_mb)
        df["Disk_Write_MB"] = df["Disk_Write"].apply(convert_to_mb)

        # Get maximum values
        max_cpu = df["CPU_Usage"].max()
        max_mem_percent = df["Memory_Percent"].max()
        max_mem_idx = df["Memory_Percent"].idxmax()
        max_mem = df.at[max_mem_idx, "Memory_Usage"]
        max_disk_read = df["Disk_Read_MB"].max()
        max_disk_write = df["Disk_Write_MB"].max()

        print("\nMaximum Resource Usage:")
        print(f"CPU Usage: {max_cpu:.2f}%")
        print(f"Memory Usage: {max_mem} ({max_mem_percent:.2f}%)")
        print(f"Disk Read: {max_disk_read:.2f}MB")
        print(f"Disk Write: {max_disk_write:.2f}MB")

        # Get timestamps of peak usage
        cpu_peak_idx = df["CPU_Usage"].idxmax()
        mem_peak_idx = df["Memory_Percent"].idxmax()
        disk_read_peak_idx = df["Disk_Read_MB"].idxmax()
        disk_write_peak_idx = df["Disk_Write_MB"].idxmax()

        print("\nPeak Usage Timestamps:")
        print(f"CPU: {df.at[cpu_peak_idx, 'Timestamp']}")
        print(f"Memory: {df.at[mem_peak_idx, 'Timestamp']}")
        print(f"Disk Read: {df.at[disk_read_peak_idx, 'Timestamp']}")
        print(f"Disk Write: {df.at[disk_write_peak_idx, 'Timestamp']}")

    except FileNotFoundError:
        print(f"Error: Could not find {csv_file}")
    except Exception as e:
        print(f"Error analyzing statistics: {e}")


def generate_dummy_data(output_file, duration_minutes=30):
    """
    Generate dummy container statistics data for testing.

    Args:
        output_file (str): Path to the output CSV file
        duration_minutes (int): Duration of data to generate in minutes
    """
    # Clear the file contents
    open(output_file, "w").close()

    with open(output_file, "a") as f:
        # Write header
        f.write(
            "Timestamp,Container,CPU_Usage,Memory_Usage,Memory_Percent,Disk_Read,Disk_Write\n"
        )

        # Generate timestamps (one entry per second)
        start_time = datetime.now() - timedelta(minutes=duration_minutes)
        timestamps = [
            start_time + timedelta(seconds=x) for x in range(duration_minutes * 60)
        ]

        # Generate dummy data
        for timestamp in timestamps:
            # Simulate realistic patterns
            time_factor = (
                np.sin(timestamp.timestamp() / 300) * 0.5 + 0.5
            )  # 5-minute cycle

            # CPU usage: 0-100% with some variation
            cpu = max(0, min(100, np.random.normal(20, 10) * time_factor))

            # Memory: Fluctuating between 100-200MB
            mem_mb = max(100, min(200, np.random.normal(150, 20) * time_factor))
            mem_percent = (mem_mb / 1024) * 100  # Assuming 1GB total memory

            # Disk I/O: Occasional spikes
            disk_read = f"{np.random.normal(200, 50) * time_factor:.0f}kB"
            disk_write = f"{np.random.normal(100, 30) * time_factor:.0f}MB"

            # Write the data
            f.write(
                f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')},"
                f"dummy_container,"
                f"{cpu:.2f}%,"
                f"{mem_mb:.1f}MiB / 1GiB,"
                f"{mem_percent:.2f}%,"
                f"{disk_read},"
                f"{disk_write}\n"
            )

    print(f"Generated {duration_minutes} minutes of dummy data in {output_file}")


def load_and_plot_data(file_path="container_stats.csv"):
    # Load the data
    data = pd.read_csv(file_path)

    # Preprocess data
    data["Timestamp"] = pd.to_datetime(data["Timestamp"])
    data["CPU_Usage"] = data["CPU_Usage"].str.rstrip("%").astype(float)
    data["Memory_Usage"] = data["Memory_Usage"].str.replace(r"[^\d./]", "", regex=True)
    data["Memory_Used"] = data["Memory_Usage"].str.split("/").str[0].astype(float)
    data["Memory_Total"] = (
        data["Memory_Usage"].str.split("/").str[1].astype(float) * 1024
    )  # Convert GiB to MiB
    data["Disk_Read"] = data["Disk_Read"].str.rstrip("kBMB").astype(float)
    data["Disk_Write"] = data["Disk_Write"].str.rstrip("kBMB").astype(float)

    # Create the plots
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    plt.subplots_adjust(hspace=0.4)

    # CPU Usage
    axes[0, 0].plot(data["Timestamp"], data["CPU_Usage"], label="CPU", color="blue")
    axes[0, 0].set_title("CPU Usage")
    axes[0, 0].set_ylabel("CPU Usage (%)")
    axes[0, 0].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    axes[0, 0].tick_params(axis="x", rotation=45)

    # Memory Usage
    axes[0, 1].plot(
        data["Timestamp"], data["Memory_Used"], label="Memory Used", color="green"
    )
    axes[0, 1].set_title("Memory Usage")
    axes[0, 1].set_ylabel("Memory (MiB)")
    axes[0, 1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    axes[0, 1].tick_params(axis="x", rotation=45)

    # Disk Read/Write
    axes[1, 0].plot(
        data["Timestamp"], data["Disk_Read"], label="Data Read", color="blue"
    )
    axes[1, 0].plot(
        data["Timestamp"], data["Disk_Write"], label="Data Write", color="orange"
    )
    axes[1, 0].set_title("Disk Read/Write")
    axes[1, 0].set_ylabel("Data (MB)")
    axes[1, 0].legend()
    axes[1, 0].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    axes[1, 0].tick_params(axis="x", rotation=45)

    # Network I/O (Placeholder as network columns are missing in the data)
    axes[1, 1].plot(
        data["Timestamp"], data["Disk_Read"], label="Data Received", color="blue"
    )  # Using Disk_Read as a placeholder
    axes[1, 1].plot(
        data["Timestamp"], data["Disk_Write"], label="Data Sent", color="orange"
    )  # Using Disk_Write as a placeholder
    axes[1, 1].set_title("Network I/O")
    axes[1, 1].set_ylabel("Data (MB)")
    axes[1, 1].legend()
    axes[1, 1].xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    axes[1, 1].tick_params(axis="x", rotation=45)

    # Show plot
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Collect and analyze Docker container statistics."
    )
    parser.add_argument(
        "container_name",
        nargs="?",  # Make container_name optional
        help="Name or ID of the Docker container to monitor",
    )
    parser.add_argument(
        "--output",
        default="container_stats.csv",
        help="Output CSV file path (default: container_stats.csv)",
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Analyze existing statistics file",
    )
    parser.add_argument(
        "--graphs",
        action="store_true",  # Change back to store_true
        help="Generate graphs from the statistics file",
    )
    parser.add_argument(
        "--generate-dummy",
        action="store_true",
        help="Generate dummy data for testing",
    )

    args = parser.parse_args()

    if args.generate_dummy:
        generate_dummy_data(args.output)
    elif args.analyze or args.graphs:
        if not os.path.exists(args.output):
            print(f"Error: File {args.output} does not exist. Generate data first.")
            sys.exit(1)
        if args.analyze:
            analyze_max_usage(args.output)
        if args.graphs:
            load_and_plot_data(args.output)  # Use load_and_plot_data instead
    else:
        if not args.container_name:
            parser.error("container_name is required when collecting statistics")
        print(
            f"Collecting stats for container '{args.container_name}'... Press Ctrl+C to stop."
        )
        collect_container_stats(args.container_name, args.output)
