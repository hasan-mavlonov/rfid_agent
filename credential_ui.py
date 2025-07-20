import tkinter as tk
from tkinter import messagebox

import httpx
import keyring


def create_credential_ui(on_submit, login_url="http://localhost:8000/api/login/"):
    root = tk.Tk()
    root.title("RFID Agent Login")
    root.geometry("300x200")
    root.resizable(False, False)
    root.configure(bg="#f0f0f0")

    # Styling
    label_style = {"bg": "#f0f0f0", "font": ("Arial", 12)}
    entry_style = {"font": ("Arial", 12), "width": 20}
    button_style = {"bg": "#4CAF50", "fg": "white", "font": ("Arial", 12), "width": 15}

    tk.Label(root, text="Phone Number", **label_style).pack(pady=10)
    phone_entry = tk.Entry(root, **entry_style)
    phone_entry.pack(pady=5)

    tk.Label(root, text="Password", **label_style).pack(pady=10)
    password_entry = tk.Entry(root, show="*", **entry_style)
    password_entry.pack(pady=5)

    def submit():
        phone = phone_entry.get().strip()
        password = password_entry.get().strip()
        if not phone or not password:
            messagebox.showerror("Error", "Please enter phone number and password")
            return
        token = validate_credentials(phone, password, login_url)
        if token:
            keyring.set_password("rfid_agent", "token", token)
            messagebox.showinfo("Success", "Credentials valid")
            on_submit(token)
            root.destroy()
        else:
            messagebox.showerror("Error", "Invalid credentials")

    tk.Button(root, text="Submit", command=submit, **button_style).pack(pady=10)
    tk.Button(root, text="Update Credentials", command=lambda: root.deiconify(), **button_style).pack(pady=5)
    return root


def validate_credentials(phone, password, login_url):
    try:
        response = httpx.post(
            login_url,
            data={"phone_number": phone, "password": password},
            timeout=5.0
        )
        if response.status_code == 200:
            return response.json().get("token")
        return None
    except Exception as e:
        print(f"Validation error: {e}")
        return None
