# 🧠 Tracky RFID Agent – Native Windows Bridge for RFID Tag Detection

This is the official **RFID Agent** for [Tracky](https://github.com/hasan-mavlonov/Tracky), a real-time RFID inventory and POS system.  
The Agent runs as a background Windows application, continuously reading RFID tags from USB-connected readers and sending them to the local Flask service, which then relays the data to the Tracky Django server.

---

## 💡 What It Does

- Connects to an **INveton (or similar)** RFID reader via `SWHidApi.dll`
- Scans RFID tags **in real time**
- Filters out noisy or unstable reads (debounces short-lived tags)
- Sends a list of stable tags via **POST requests** to the Flask server
- Designed to auto-start on Windows and run quietly in the background

---

## 🛠️ Architecture Overview

```plaintext
[ RFID Reader + SWHidApi.dll ]
            ↓
[ Tracky RFID Agent (Windows App) ]
            ↓  (HTTP Post)
[ Flask Server (localhost) ]
            ↓
[ Django Server (on tracky.one) ]
