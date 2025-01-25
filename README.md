# Container Statistics Analyzer

This Python script collects real-time Docker container statistics and saves them to a CSV file for monitoring and analysis.

## Features

- Collects real-time container statistics every 5 seconds
- Monitors CPU usage, memory usage, and disk I/O
- Saves data to CSV format for further analysis
- Supports monitoring of specific containers by name or ID

## Prerequisites

- Python 3.x
- Docker installed and running
- Required Python packages:
  - argparse
  - subprocess

## Usage

Run the script with a container name or ID:
```bash
python main.py CONTAINER_NAME [--output OUTPUT_FILE]
```

Options:
- `CONTAINER_NAME`: Name or ID of the Docker container to monitor (required)
- `--output`: Output CSV file path (default: container_stats.csv)

## Stopping the Collection

Press Ctrl+C to stop collecting statistics.

## Output File Format

The script generates a CSV file with the following columns:
- Timestamp
- Container ID
- CPU Usage
- Memory Usage
- Memory Percent
- Disk Read
- Disk Write

## Example

## License

This project is licensed under the MIT License - see the LICENSE file for details.
