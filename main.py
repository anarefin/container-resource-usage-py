import subprocess
import time
from datetime import datetime
import argparse


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


if __name__ == "__main__":
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(
        description="Collect Docker container statistics and write to a CSV file."
    )
    parser.add_argument(
        "container_name", help="Name or ID of the Docker container to monitor"
    )
    parser.add_argument(
        "--output",
        default="container_stats.csv",
        help="Output CSV file path (default: container_stats.csv)",
    )

    args = parser.parse_args()

    print(
        f"Collecting stats for container '{args.container_name}'... Press Ctrl+C to stop."
    )
    collect_container_stats(args.container_name, args.output)
