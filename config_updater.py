import os
import yaml
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from time import sleep

# Paths
CONFIG_FILE = "/etc/promtail/promtail-config.yaml"
LOGS_DIR = "/var/log/services/"  # Directory to monitor for new log files
PROMTAIL_TEMPLATE = {
    "server": {"http_listen_port": 9080, "grpc_listen_port": 0},
    "positions": {"filename": "/tmp/positions.yaml"},
    "clients": [{"url": "http://loki:3100/loki/api/v1/push"}],
    "scrape_configs": []
}


# Function to update Promtail config
def update_promtail_config():
    scrape_configs = []

    # Iterate over log files in the logs directory
    for log_file in os.listdir(LOGS_DIR):
        full_path = os.path.join(LOGS_DIR, log_file)
        if os.path.isfile(full_path):
            scrape_configs.append({
                "job_name": f"{log_file}-logs",
                "static_configs": [{
                    "targets": ["localhost"],
                    "labels": {
                        "job": f"{log_file}-logs",
                        "__path__": full_path
                    }
                }]
            })

    # Generate new configuration
    promtail_config = PROMTAIL_TEMPLATE.copy()
    promtail_config["scrape_configs"] = scrape_configs

    # Write updated configuration
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(promtail_config, f)

    print(f"Updated Promtail config with {len(scrape_configs)} jobs.")


# Event handler to detect changes
class LogDirectoryHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            print(f"New log file detected: {event.src_path}")
            update_promtail_config()


# Main function to start the watcher
def main():
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)

    print(f"Watching {LOGS_DIR} for changes...")
    event_handler = LogDirectoryHandler()
    observer = Observer()
    observer.schedule(event_handler, path=LOGS_DIR, recursive=False)
    observer.start()

    try:
        while True:
            sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
