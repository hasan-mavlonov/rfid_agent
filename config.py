# rfid_agent/config.py
import configparser
import os

from utils import resource_path

config = configparser.ConfigParser()
config_path = resource_path("config.ini")
if not os.path.exists(config_path):
    raise FileNotFoundError(f"config.ini not found at {config_path}")
config.read(config_path)

# Verify sections
for section in ['rfid', 'server', 'agent']:
    if section not in config:
        raise KeyError(f"Missing [{section}] section in config.ini")

API_URL = config["server"]["api_url"]
DLL_PATH = config["rfid"]["dll_path"]
POLL_INTERVAL = float(config["agent"]["poll_interval"])
SEND_COOLDOWN = float(config["agent"]["send_cooldown"])
RECONNECT_INTERVAL = 5.0  # Time to wait before retrying device connection (seconds)
