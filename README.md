# 🧠 Tracky RFID Agent – Native Windows Bridge for RFID Tag Detection

This is the official **RFID Agent** for [Tracky](https://github.com/YourOrg/Tracky), a real-time RFID inventory and POS system.  
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

```
[ RFID Reader + SWHidApi.dll ]
            ↓
[ Tracky RFID Agent (Windows App) ]
            ↓  (HTTP Post)
[ Flask Server (localhost) ]
            ↓
[ Django Server (on Render or elsewhere) ]
```

---

## 📂 Project Structure

```
rfid-agent/
├── main.py                   # Main loop that interacts with DLL and sends tag data
├── reader.py                 # Encapsulates RFID reading logic using ctypes and DLL
├── sender.py                 # Sends data to local Flask endpoint
├── config.py                 # Constants (e.g., DLL path, endpoints, timing)
├── requirements.txt          # Python dependencies
├── readme.txt                # You’re here
```

---

## ⚙️ Requirements

* Windows 10 or higher
* Python 3.10+
* USB-connected RFID Reader (INveton or compatible)
* `SWHidApi.dll` (provided by manufacturer)

---

## 🔧 Installation

1. **Clone the Repo**

   ```
   git clone https://github.com/YourOrg/rfid-agent.git
   cd rfid-agent
   ```

2. **Install Dependencies**

   ```
   pip install -r requirements.txt
   ```

3. **Place the DLL**
   Place `SWHidApi.dll` in the project root or adjust the path in `config.py`.

4. **Run the Agent**

   ```
   python main.py
   ```

   The agent will begin scanning for RFID tags and sending stable results to your local Flask server at `http://localhost:5000/rfids/`.

---

## 📡 Configuration

Edit `config.py` to customize:

```
DLL_PATH = "SWHidApi.dll"  # Path to the manufacturer's DLL
SEND_INTERVAL_MS = 100     # How often to send tags (in milliseconds)
MINIMUM_STABLE_READS = 3   # Only send tags seen N times consecutively
FLASK_ENDPOINT = "http://localhost:5000/rfids/"
```

---

## 🧪 Debug Mode

Set `DEBUG = True` in `config.py` to enable verbose logging to the console:

```
[INFO] Detected tag: E2003412012345678900AABB
[INFO] Sending 3 stable tags to Flask...
```

---

## 🤖 Autorun on Startup (Optional)

To run the agent in the background on Windows startup:

1. Convert it to an `.exe` using PyInstaller:

   ```
   pyinstaller --onefile main.py
   ```

2. Add the `.exe` to your Windows startup folder:

   ```
   shell:startup
   ```

---

## 🔐 Security

* Data is only sent to `localhost` by default
* No persistent storage; all reads are ephemeral
* Will later include authentication headers if needed

---

## 📬 Contact

Want to integrate another RFID reader or report a bug?  
📧 [hasanmavlonov@gmail.com](mailto:hasanmavlonov@gmail.com)  
🌐 [https://github.com/hasanmavlonov](https://github.com/hasanmavlonov) (or your organization page)

---

## 🪪 License

This project is currently closed-source for commercial deployment.  
Contact us if you’re interested in bundling the agent with your own POS system.

---

## 🧭 TL;DR

The Tracky RFID Agent is a native Windows tool that bridges RFID hardware with our Flask/Django inventory system. It reads tag data via USB, filters noise, and sends live updates to your store’s backend — powering Tracky’s 24/7 inventory monitoring.
