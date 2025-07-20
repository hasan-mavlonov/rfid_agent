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

def create_icon():
    """Load the company logo icon."""
    return Image.open(resource_path("icon.ico"))

def run_reader(reader, stop_event):
    """Run the RFID reader's run method in a thread."""
    try:
        reader.run()
    except Exception as e:
        logger.error(f"Reader thread error: {e}")
        stop_event.set()

def run_tag_sender(reader, stop_event):
    """Run the tag-sending loop in a thread."""
    last_sent_tags = set()
    last_sent_time = 0.0
    while not stop_event.is_set():
        try:
            now = time.time()
            current_tags = set(reader.get_recent_tags().keys())
            if current_tags != last_sent_tags and now - last_sent_time >= SEND_COOLDOWN:
                if current_tags:
                    asyncio.run(send_rfids_to_server_async(current_tags))
                    last_sent_tags = current_tags
                    last_sent_time = now
                    logger.info(f"Tags sent: {current_tags}")
        except Exception as e:
            logger.error(f"Tag sender error: {e}")
        time.sleep(POLL_INTERVAL)

def main():
    # Create stop event for threads
    stop_event = threading.Event()

    # Initialize reader
    reader = None
    reader_thread = None
    sender_thread = None

    def on_exit(icon, item):
        """Handle system tray exit action."""
        stop_event.set()
        if reader_thread and reader_thread.is_alive():
            reader_thread.join(timeout=2.0)
        if sender_thread and sender_thread.is_alive():
            sender_thread.join(timeout=2.0)
        icon.stop()
        sys.exit(0)

    # Create system tray icon
    icon = pystray.Icon(
        "RFID Reader",
        create_icon(),
        "RFID Reader",
        menu=pystray.Menu(
            pystray.MenuItem("Exit", on_exit)
        )
    )

    try:
        logger.info("Attempting to initialize RFID reader...")
        reader = RFIDReader(DLL_PATH)
        # Start RFID reader thread
        reader_thread = threading.Thread(target=run_reader, args=(reader, stop_event), daemon=True)
        reader_thread.start()
        logger.info("RFID reader thread started successfully")
        # Start tag sender thread
        sender_thread = threading.Thread(target=run_tag_sender, args=(reader, stop_event), daemon=True)
        sender_thread.start()
        logger.info("Tag sender thread started successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RFID reader: {e}. Application will exit.")
        on_exit(icon, None)
        return

    # Run system tray icon in the main thread
    icon.run()

if __name__ == "__main__":
    main()