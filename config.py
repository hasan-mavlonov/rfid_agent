# config.py
import configparser
from utils import resource_path

config = configparser.ConfigParser()
config.read(resource_path("config.ini"))

API_URL = config["server"]["api_url"]
DLL_PATH = config["rfid"]["dll_path"]
POLL_INTERVAL = float(config["agent"]["poll_interval"])
SEND_COOLDOWN = float(config["agent"]["send_cooldown"])
RECONNECT_INTERVAL = 5.0  # Time to wait before retrying device connection (seconds)