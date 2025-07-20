# rfid_agent/main.py
import asyncio
import time
import threading
import sys
import pystray
from PIL import Image
from utils import resource_path
from config import API_URL, DLL_PATH, POLL_INTERVAL, SEND_COOLDOWN
from uploader_async import send_rfids_to_server_async
from rfid_reader import logger, RFIDReader
from credential_ui import create_credential_ui

def create_icon():
    try:
        return Image.open(resource_path("icon.ico"))
    except Exception as e:
        logger.error(f"Failed to load icon: {e}")
        return Image.new('RGB', (64, 64), color='black')

def run_reader(reader, stop_event):
    try:
        reader.run()
    except Exception as e:
        logger.error(f"Reader thread error: {e}")
        stop_event.set()

def run_tag_sender(reader, stop_event):
    last_sent_tags = set()
    last_sent_time = 0.0
    while not stop_event.is_set():
        try:
            now = time.time()
            current_tags = set(reader.get_recent_tags().keys())
            logger.info(f"Detected tags: {current_tags}")
            if current_tags != last_sent_tags and now - last_sent_time >= SEND_COOLDOWN:
                if current_tags:
                    logger.info(f"Sending tags to server: {current_tags}")
                    asyncio.run(send_rfids_to_server_async(
                        current_tags,
                        login_url="http://localhost:8000/api/login/"
                    ))
                    last_sent_tags = current_tags
                    last_sent_time = now
                    logger.info(f"Tags sent: {current_tags}")
        except Exception as e:
            logger.error(f"Tag sender error: {e}")
        time.sleep(POLL_INTERVAL)

def main():
    stop_event = threading.Event()
    reader = None
    reader_thread = None
    sender_thread = None

    def on_exit(icon, item):
        stop_event.set()
        if reader_thread and reader_thread.is_alive():
            reader_thread.join(timeout=2.0)
        if sender_thread and sender_thread.is_alive():
            sender_thread.join(timeout=2.0)
        icon.stop()
        sys.exit(0)

    def on_update_credentials(icon, item):
        logger.info("Opening credential UI via system tray")
        threading.Thread(
            target=create_credential_ui,
            args=(lambda t: logger.info(f"Credentials updated: {t}"), "http://localhost:8000/api/login/"),
            daemon=True
        ).start()

    icon = pystray.Icon(
        "RFID Reader",
        create_icon(),
        "RFID Reader",
        menu=pystray.Menu(
            pystray.MenuItem("Update Credentials", on_update_credentials),
            pystray.MenuItem("Exit", on_exit)
        )
    )

    try:
        logger.info("Attempting to initialize RFID reader...")
        reader = RFIDReader(DLL_PATH)
        reader_thread = threading.Thread(target=run_reader, args=(reader, stop_event), daemon=True)
        reader_thread.start()
        logger.info("RFID reader thread started successfully")
        sender_thread = threading.Thread(target=run_tag_sender, args=(reader, stop_event), daemon=True)
        sender_thread.start()
        logger.info("Tag sender thread started successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RFID reader: {e}. Application will exit.")
        on_exit(icon, None)
        return

    icon.run()

if __name__ == "__main__":
    main()