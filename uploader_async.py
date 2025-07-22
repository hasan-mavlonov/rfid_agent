# rfid_agent/uploader_async.py
import asyncio
import queue
import threading

import httpx
import keyring

from config import API_URL
from credential_ui import create_credential_ui


def run_ui_in_thread(login_url, result_queue):
    def on_submit(token):
        result_queue.put(token)

    root = create_credential_ui(on_submit, login_url)
    root.mainloop()


async def send_rfids_to_server_async(rfid_list, retries=3, login_url="http://localhost:8000/api/login/"):
    if not rfid_list:
        return False  # Indicate sending failed
    print(f"Attempting to send RFIDs: {rfid_list}")
    token = keyring.get_password("rfid_agent", "token")
    if not token:
        print("⚠️ No token found, prompting for credentials")
        result_queue = queue.Queue()
        ui_thread = threading.Thread(target=run_ui_in_thread, args=(login_url, result_queue), daemon=True)
        ui_thread.start()
        ui_thread.join()  # Wait for UI to close
        try:
            token = result_queue.get_nowait()
        except queue.Empty:
            print("⚠️ Failed to obtain token from UI")
            return False
        if not token:
            print("⚠️ Failed to obtain token")
            return False

    for attempt in range(retries):
        try:
            async with httpx.AsyncClient(
                    timeout=5.0,
                    headers={
                        "Connection": "keep-alive",
                        "Accept-Encoding": "gzip, deflate",
                        "Authorization": f"Bearer {token}"
                    }
            ) as client:
                response = await client.post(API_URL, json={"rfids": list(rfid_list)})
                if response.status_code == 200:
                    print(f"✔ Sent: {rfid_list}")
                    return True
                elif response.status_code == 401:
                    print("⚠️ Invalid token, prompting for credentials")
                    keyring.delete_password("rfid_agent", "token")  # Clear invalid token
                    result_queue = queue.Queue()
                    ui_thread = threading.Thread(target=run_ui_in_thread, args=(login_url, result_queue), daemon=True)
                    ui_thread.start()
                    ui_thread.join()
                    try:
                        token = result_queue.get_nowait()
                    except queue.Empty:
                        print("⚠️ Failed to obtain token from UI")
                        return False
                    if not token:
                        print("⚠️ Failed to obtain token")
                        return False
                else:
                    print(f"❌ Server error: {response.status_code}")
        except Exception as e:
            print(f"⚠️ Attempt {attempt + 1} failed: {e}")
        await asyncio.sleep(0.5)
    return False  # Return False if all retries fail
