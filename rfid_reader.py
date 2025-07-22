import ctypes
import time
import logging
from ctypes import c_int, byref, create_string_buffer

from config import POLL_INTERVAL

# Create or get logger
logger = logging.getLogger("rfid_reader")

# Set root logger level to DEBUG to capture all messages
logger.setLevel(logging.DEBUG)

# Custom filter to allow only DEBUG level
class DebugOnlyFilter(logging.Filter):
    def filter(self, record):
        return record.levelno == logging.DEBUG

# Create file handler for DEBUG level only
log_file = "rfid_reader.log"
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)  # Restrict file to DEBUG messages
file_handler.addFilter(DebugOnlyFilter())  # Ensure only DEBUG messages pass
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

class RFIDReader:
    def __init__(self, dll_path):
        self.dll = ctypes.windll.LoadLibrary(dll_path)
        self._initialize_reader()
        self.tag_registry = {}  # {tag_id: timestamp}
        logger.debug("[RFID Reader Initialized] Device is active.")

    def _initialize_reader(self):
        """Initialize the RFID reader device."""
        if self.dll.SWHid_GetUsbCount() == 0:
            raise RuntimeError("No USB device found")
        if self.dll.SWHid_OpenDevice(0) != 1:
            raise RuntimeError("Failed to open device")

        self.dll.SWHid_ClearTagBuf()
        self.dll.SWHid_SetDeviceOneParam(0xFF, 2, 1)  # Set to active mode
        self.dll.SWHid_StartRead(0xFF)

    def parse_tag_data(self, buffer, offset):
        """Parse tag data from the buffer at the given offset."""
        raw = bytearray(buffer)
        bPackLength = raw[offset]

        # EPC data: from offset + 1 + 2 to offset + 1 + bPackLength - 1
        epc_start = offset + 1 + 2
        epc_end = offset + 1 + bPackLength - 1
        tag_id_bytes = raw[epc_start:epc_end]

        # Convert bytes to hex string
        tag_id = ''.join(f"{b:02X}" for b in tag_id_bytes)
        return tag_id, bPackLength

    def run(self):
        """Continuously read tags from the device."""
        logger.debug("[RFID Reader Running] Reading loop started.")
        while True:
            try:
                buffer = create_string_buffer(9182)
                iTagLength = c_int(0)
                iTagNumber = c_int(0)
                ret = self.dll.SWHid_GetTagBuf(buffer, byref(iTagLength), byref(iTagNumber))
                now = time.time()

                if ret and iTagNumber.value > 0:
                    offset = 0
                    detected_tags = set()
                    for _ in range(iTagNumber.value):
                        tag_id, pack_len = self.parse_tag_data(buffer, offset)
                        offset += pack_len
                        if tag_id:
                            detected_tags.add(tag_id)
                            self.tag_registry[tag_id] = now

                    # Remove tags older than 2 seconds
                    self.tag_registry = {
                        tag: ts for tag, ts in self.tag_registry.items()
                        if now - ts <= 2.0
                    }

            except Exception as e:
                logger.debug(f"Reader loop error: {e}")
                time.sleep(POLL_INTERVAL)

            time.sleep(POLL_INTERVAL)  # Poll every 20ms

    def get_recent_tags(self):
        """Return tags detected within the last 2 seconds."""
        now = time.time()
        recent_tags = {
            tag: ts for tag, ts in self.tag_registry.items()
            if now - ts <= 2.0
        }
        return recent_tags