# rfid_agent/credential_ui.py
import tkinter as tk
from tkinter import messagebox
import httpx
import keyring
import logging

logger = logging.getLogger(__name__)

def create_credential_ui(on_submit, login_url="http://localhost:8000/api/login/"):
    logger.debug("Creating credential UI")
    root = tk.Tk()
    root.title("RFID Agent Login")
    root.geometry("300x250")
    root.resizable(False, False)
    root.configure(bg="#f0f0f0")

    label_style = {"bg": "#f0f0f0", "font": ("Arial", 12)}
    entry_style = {"font": ("Arial", 12), "width": 20}
    button_style = {"bg": "#4CAF50", "fg": "white", "font": ("Arial", 12), "width": 15}

    tk.Label(root, text="Phone Number", **label_style).pack(pady=5)
    phone_entry = tk.Entry(root, **entry_style)
    phone_entry.pack(pady=5)

    tk.Label(root, text="Password", **label_style).pack(pady=5)
    password_entry = tk.Entry(root, show="*", **entry_style)
    password_entry.pack(pady=5)

    tk.Label(root, text="Test Token (Optional)", **label_style).pack(pady=5)
    token_entry = tk.Entry(root, **entry_style)
    token_entry.pack(pady=5)

    def submit():
        phone = phone_entry.get().strip()
        password = password_entry.get().strip()
        test_token = token_entry.get().strip()
        logger.debug(f"Submitting credentials: phone={phone}, test_token={'set' if test_token else 'not set'}")
        if test_token:
            keyring.set_password("rfid_agent", "token", test_token)
            logger.debug("Test token stored")
            messagebox.showinfo("Success", "Test token saved")
            on_submit(test_token)
            root.destroy()
            return
        if not phone or not password:
            logger.debug("Empty phone number or password")
            messagebox.showerror("Error", "Please enter phone number and password")
            return
        token = validate_credentials(phone, password, login_url)
        if token:
            keyring.set_password("rfid_agent", "token", token)
            logger.debug("Credentials valid, token stored")
            messagebox.showinfo("Success", "Credentials valid")
            on_submit(token)
            root.destroy()
        else:
            logger.debug("Invalid credentials")
            messagebox.showerror("Error", "Invalid credentials")

    tk.Button(root, text="Submit", command=submit, **button_style).pack(pady=10)
    tk.Button(root, text="Update Credentials", command=lambda: root.deiconify(), **button_style).pack(pady=5)
    return root

def validate_credentials(phone, password, login_url):
    try:
        logger.debug(f"Validating credentials against {login_url}")
        response = httpx.post(
            login_url,
            json={"phone_number": phone, "password": password},
            headers={"Content-Type": "application/json"},
            timeout=5.0
        )
        if response.status_code == 200:
            logger.debug("Validation successful")
            return response.json().get("token")
        logger.debug(f"Validation failed: {response.status_code}")
        return None
    except Exception as e:
        logger.debug(f"Validation error: {e}")
        return None