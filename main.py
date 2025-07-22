# rfid_agent/main.py
import asyncio
import time
import threading
import sys

import keyring
import pystray
from PIL import Image
from utils import resource_path
from config import API_URL, DLL_PATH, POLL_INTERVAL, SEND_COOLDOWN
from uploader_async import send_rfids_to_server_async
from rfid_reader import logger, RFIDReader
from credential_ui import create_credential_ui
import queue

def create_icon():
    try:
        return Image.open(resource_path("icon.ico"))
    except Exception as e:
        logger.debug(f"Failed to load icon: {e}")
        return Image.new('RGB', (64, 64), color='black')

def run_reader(reader, stop_event):
    try:
        reader.run()
    except Exception as e:
        logger.debug(f"Reader thread error: {e}")
        stop_event.set()

def run_tag_sender(reader, stop_event, auth_valid):
    last_sent_tags = set()
    last_sent_time = 0.0
    max_failed_attempts = 3
    failed_attempts = 0
    last_logged_tags = set()  # Track last logged tags to reduce duplicates

    while not stop_event.is_set():
        if auth_valid.is_set():
            try:
                now = time.time()
                current_tags = set(reader.get_recent_tags().keys())
                if current_tags != last_logged_tags and current_tags:  # Log only on change and non-empty
                    logger.info(f"Detected tags: {current_tags}")
                    last_logged_tags = current_tags
                if current_tags != last_sent_tags and now - last_sent_time >= SEND_COOLDOWN:
                    if current_tags:
                        logger.info(f"Sending tags to server: {current_tags}")
                        success = asyncio.run(send_rfids_to_server_async(
                            current_tags,
                            login_url="http://localhost:8000/api/login/"
                        ))
                        if success:
                            last_sent_tags = current_tags
                            last_sent_time = now
                            logger.info(f"Tags sent: {current_tags}")
                            failed_attempts = 0  # Reset on success
                        else:
                            failed_attempts += 1
                            logger.debug(f"Failed to send tags, attempts: {failed_attempts}")
                            if failed_attempts >= max_failed_attempts:
                                logger.debug("Too many failed attempts, halting sending")
                                auth_valid.clear()  # Invalidate authentication state
                                failed_attempts = 0  # Reset after halting
            except Exception as e:
                logger.debug(f"Tag sender error: {e}")
        else:
            logger.debug("Authentication invalid, waiting for re-authentication")
            last_sent_tags = set()  # Reset to avoid sending on re-auth
            last_logged_tags = set()  # Reset logged tags
            time.sleep(POLL_INTERVAL)  # Wait while auth is invalid

def on_exit(icon, item):
    logger.debug("Exiting application via system tray")
    stop_event.set()
    # Ensure threads are joined with a timeout
    if reader_thread and reader_thread.is_alive():
        reader_thread.join(timeout=2.0)
    if sender_thread and sender_thread.is_alive():
        sender_thread.join(timeout=2.0)
    # Stop the icon after threads are handled
    icon.stop()
    sys.exit(0)

def on_update_credentials(icon, item):
    logger.debug("Opening credential UI via system tray")
    def run_ui():
        result_queue = queue.Queue()
        def on_submit(token):
            result_queue.put(token)
            root.quit()  # Close the UI after submission
        root = create_credential_ui(on_submit, "http://localhost:8000/api/login/")
        root.mainloop()
        try:
            token = result_queue.get_nowait()
            if token:
                keyring.set_password("rfid_agent", "token", token)
                logger.debug(f"Credentials updated: {token}")
                auth_valid.set()  # Restore authentication state on success
            else:
                auth_valid.clear()  # Invalidate if no token
        except queue.Empty:
            logger.debug("UI closed without submitting credentials")
            auth_valid.clear()  # Invalidate on UI closure without submission

    # Run UI in a separate thread, non-daemon, to ensure it completes
    ui_thread = threading.Thread(target=run_ui, daemon=False)
    ui_thread.start()

def main():
    global stop_event, reader, reader_thread, sender_thread, auth_valid
    stop_event = threading.Event()
    auth_valid = threading.Event()  # New authentication state flag
    reader = None
    reader_thread = None
    sender_thread = None

    # Set initial authentication state based on existing token
    if keyring.get_password("rfid_agent", "token"):
        auth_valid.set()
    else:
        auth_valid.clear()

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
        logger.debug("Attempting to initialize RFID reader...")
        reader = RFIDReader(DLL_PATH)
        reader_thread = threading.Thread(target=run_reader, args=(reader, stop_event), daemon=True)
        reader_thread.start()
        logger.debug("RFID reader thread started successfully")
        sender_thread = threading.Thread(target=run_tag_sender, args=(reader, stop_event, auth_valid), daemon=True)
        sender_thread.start()
        logger.debug("Tag sender thread started successfully")
    except Exception as e:
        logger.debug(f"Failed to initialize RFID reader: {e}. Application will exit.")
        on_exit(icon, None)
        return

    icon.run()

if __name__ == "__main__":
    main()  