import subprocess
import time
from datetime import datetime
import argparse
import pandas as pd


def collect_container_stats(container_name, output_file):
    """
    Collect CPU, memory, and disk I/O usage for a specific Docker container
    and write it to a file with a 5-second interval.

    Args:
        container_name (str): The name or ID of the Docker container.
        output_file (str): Path to the output file.
    """
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
                time.sleep(5)
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

        # Empty the CSV file after analysis
        open(csv_file, "w").close()
        print(f"\nCleared contents of {csv_file}")

    except FileNotFoundError:
        print(f"Error: Could not find {csv_file}")
    except Exception as e:
        print(f"Error analyzing statistics: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Collect and analyze Docker container statistics."
    )
    parser.add_argument(
        "container_name", help="Name or ID of the Docker container to monitor"
    )
    parser.add_argument(
        "--output",
        default="container_stats.csv",
        help="Output CSV file path (default: container_stats.csv)",
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Analyze existing statistics file instead of collecting new data",
    )

    args = parser.parse_args()

    if args.analyze:
        analyze_max_usage(args.output)
    else:
        print(
            f"Collecting stats for container '{args.container_name}'... Press Ctrl+C to stop."
        )
        collect_container_stats(args.container_name, args.output)
