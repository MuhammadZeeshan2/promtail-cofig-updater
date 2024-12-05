# Promtail Dynamic Configuration and Docker Integration

This project automates the configuration of Promtail and updates the `docker-compose.yaml` file dynamically when log files are added, modified, or deleted in a specified directory. The solution also restarts the Promtail container to apply the new configurations.

## Features

- Automatically updates the `promtail-config.yaml` file when new log files are detected.
- Updates the `docker-compose.yaml` file to include new log file paths in the Promtail service's `volumes` section.
- Restarts the Promtail container to apply updated configurations.
- Watches a specified directory (`LOGS_DIR`) for any changes to log files.
- Handles file creation, modification, and deletion events.

## Prerequisites

- **Python 3.7+** installed
- **Docker** and **docker-compose** installed
- Promtail, Loki, and Grafana set up via `docker-compose.yaml`

## Directory Structure

```plaintext
├── Promtail/
│   ├── docker-compose.yaml
│   ├── promtail-config.yaml
├── Logger/  # Directory to monitor for log files
└── main.py  # Script to monitor directory and update configurations
```

## Setup

1. Clone this repository and navigate to the project directory.

2. Ensure the following files and directories exist:
   - `promtail-config.yaml` in the `Promtail/` directory.
   - `docker-compose.yaml` in the `Promtail/` directory.
   - `Logger/` directory to store log files.

3. Install the required Python dependencies:
   ```bash
   pip install watchdog pyyaml
   ```

4. Update the configuration paths in `main.py`:
   - `CONFIG_FILE`: Path to the `promtail-config.yaml` file.
   - `COMPOSE_FILE`: Path to the `docker-compose.yaml` file.
   - `LOGS_DIR`: Path to the directory to monitor for log files.

## Usage

1. **Start Loki, Promtail, and Grafana**:
   ```bash
   cd /home/zeeshan/Promtail
   docker-compose up -d
   ```

2. **Run the script**:
   ```bash
   python3 main.py
   ```

3. **Add, modify, or delete log files** in the `Logger/` directory:
   - When a new file is added, it is automatically:
     - Added to the `promtail-config.yaml`.
     - Appended to the `volumes` section in `docker-compose.yaml`.
     - Applied by restarting the Promtail container.

4. **Stop the script**:
   - Use `CTRL+C` to stop watching the directory.

## Example Workflow

1. **Add a new log file**:
   ```bash
   echo "Sample log" > /home/zeeshan/Logger/sample.log
   ```
   - The new file is added to Promtail's configuration.
   - The file path is added to `docker-compose.yaml`.
   - The Promtail container is restarted.

2. **View logs in Grafana**:
   - Access Grafana at `http://localhost:3200`.
   - Use the pre-configured Loki datasource to visualize logs.

## Configuration Example

### Promtail Configuration (`promtail-config.yaml`)

```yaml
server:
  http_listen_port: 9080
  grpc_listen_port: 0
positions:
  filename: /tmp/positions.yaml
clients:
  - url: http://loki:3100/loki/api/v1/push
scrape_configs:
  - job_name: sample.log-logs
    static_configs:
      - targets:
          - localhost
        labels:
          job: sample.log-logs
          __path__: /home/zeeshan/Logger/sample.log
```

### Docker Compose (`docker-compose.yaml`)

```yaml
services:
  promtail:
    image: grafana/promtail:2.9.2
    volumes:
      - ./promtail-config.yaml:/etc/promtail/promtail-config.yaml:ro
      - /home/zeeshan/Logger/sample.log:/home/zeeshan/Logger/sample.log:ro
```

## Troubleshooting

1. **Promtail container fails to restart**:
   - Ensure the log file paths in `docker-compose.yaml` exist.
   - Verify the syntax of `docker-compose.yaml` using:
     ```bash
     docker-compose config
     ```

2. **No logs in Grafana**:
   - Check Promtail logs:
     ```bash
     docker logs promtail
     ```
   - Ensure the log file contains data.

## Contributing

Feel free to open issues or submit pull requests to improve this project.

## License

This project is licensed under the MIT License.

---
