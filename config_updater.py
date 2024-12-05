import os
import yaml
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from time import sleep

CONFIG_FILE = "/home/zeeshan/Promtail/promtail-config.yaml"
DOCKER_COMPOSE_FILE = "/home/zeeshan/Promtail/docker-compose.yaml"
LOGS_DIR = "/home/zeeshan/Logger/"  # Ensure this is a directory
PROMTAIL_TEMPLATE = {
    "server": {"http_listen_port": 9080, "grpc_listen_port": 0},
    "positions": {"filename": "/tmp/positions.yaml"},
    "clients": [{"url": "http://loki:3100/loki/api/v1/push"}],
    "scrape_configs": []
}


def update_promtail_config():
    # Load existing configuration if the file exists
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            try:
                promtail_config = yaml.safe_load(f)
                scrape_configs = promtail_config.get("scrape_configs", [])
            except yaml.YAMLError as e:
                print(f"Error reading Promtail config: {e}")
                return False
    else:
        scrape_configs = []

    existing_paths = {config["static_configs"][0]["labels"]["__path__"] for config in scrape_configs}

    # Add new configurations only for new files
    for log_file in os.listdir(LOGS_DIR):
        full_path = os.path.join(LOGS_DIR, log_file)
        if os.path.isfile(full_path) and full_path not in existing_paths:
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

    # Update the configuration
    promtail_config = PROMTAIL_TEMPLATE.copy()
    promtail_config["scrape_configs"] = scrape_configs

    try:
        with open(CONFIG_FILE, "w") as f:
            yaml.dump(promtail_config, f)
        print(f"Updated Promtail config with {len(scrape_configs)} jobs.")
        return True
    except Exception as e:
        print(f"Error updating Promtail config: {e}")
        return False


def update_docker_compose():
    try:
        # Load docker-compose.yml
        with open(DOCKER_COMPOSE_FILE, "r") as f:
            docker_compose = yaml.safe_load(f)

        promtail_service = docker_compose["services"]["promtail"]
        current_volumes = set(promtail_service.get("volumes", []))

        # Extract log paths from promtail config
        with open(CONFIG_FILE, "r") as f:
            promtail_config = yaml.safe_load(f)

        new_paths = set()
        for config in promtail_config["scrape_configs"]:
            log_path = config["static_configs"][0]["labels"]["__path__"]
            new_paths.add(f"{log_path}:{log_path}")  # Docker-compose volume syntax

        # Add missing volumes
        updated_volumes = current_volumes.union(new_paths)
        promtail_service["volumes"] = list(updated_volumes)

        # Write back the updated docker-compose.yml
        with open(DOCKER_COMPOSE_FILE, "w") as f:
            yaml.dump(docker_compose, f)

        print("Updated docker-compose.yml with new volumes.")
        return True

    except Exception as e:
        print(f"Error updating docker-compose.yml: {e}")
        return False


def reload_promtail_docker():
    try:
        result = subprocess.run(["docker-compose", "restart", "promtail"], cwd=os.path.dirname(DOCKER_COMPOSE_FILE), stdout=subprocess.PIPE, text=True)
        if result.returncode == 0:
            print("Promtail container restarted successfully.")
            return True
        else:
            print("Failed to restart Promtail container.")
            return False
    except Exception as e:
        print(f"Error restarting Promtail container: {e}")
        return False


class LogDirectoryHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            print(f"New file created: {event.src_path}")
            if update_promtail_config() and update_docker_compose():
                reload_promtail_docker()

    def on_modified(self, event):
        if not event.is_directory:
            print(f"File modified: {event.src_path}")
            if update_promtail_config() and update_docker_compose():
                reload_promtail_docker()

    def on_deleted(self, event):
        if not event.is_directory:
            print(f"File deleted: {event.src_path}")
            if update_promtail_config() and update_docker_compose():
                reload_promtail_docker()


def main():
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)

    print(f"Watching directory: {LOGS_DIR} for changes...")
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
