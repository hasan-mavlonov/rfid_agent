# rfid_agent/uploader_async.py
import asyncio
import httpx
import keyring

from config import API_URL
from credential_ui import create_credential_ui

async def send_rfids_to_server_async(rfid_list, retries=3, login_url="http://localhost:8000/api/login/"):
    if not rfid_list:
        return
    token = keyring.get_password("rfid_agent", "token")
    if not token:
        print("⚠️ No token found, prompting for credentials")
        loop = asyncio.get_event_loop()
        token_set = False
        def set_token(t):
            nonlocal token_set
            token_set = True
        loop.run_in_executor(None, lambda: create_credential_ui(set_token, login_url).mainloop())
        while not token_set:
            await asyncio.sleep(0.1)
        token = keyring.get_password("rfid_agent", "token")
        if not token:
            print("⚠️ Failed to obtain token")
            return
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
                    return
                elif response.status_code == 401:
                    print("⚠️ Invalid token, prompting for credentials")
                    loop = asyncio.get_event_loop()
                    token_set = False
                    def set_token(t):
                        nonlocal token_set
                        token_set = True
                    loop.run_in_executor(None, lambda: create_credential_ui(set_token, login_url).mainloop())
                    while not token_set:
                        await asyncio.sleep(0.1)
                    token = keyring.get_password("rfid_agent", "token")
                    if not token:
                        print("⚠️ Failed to obtain token")
                        return
                else:
                    print(f"❌ Server error: {response.status_code}")
        except Exception as e:
            print(f"⚠️ Attempt {attempt+1} failed: {e}")
        await asyncio.sleep(0.5)