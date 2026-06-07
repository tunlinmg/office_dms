# views/login_view.py
import tkinter as tk
from tkinter import ttk, messagebox
from src.models.user_model import authenticate
from src.models.activity_log_model import log_activity


class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.user = None
        self.title("DMS - User Login")
        self.geometry("420x280")
        self.resizable(False, False)
        self._setup_ui()

    def _setup_ui(self):
        frame = ttk.LabelFrame(self, text=" အကောင့်ဝင်ရောက်ရန် (Login) ")
        frame.pack(fill="both", expand=True, padx=30, pady=30)

        ttk.Label(frame, text="Username:").grid(row=0, column=0, sticky="w", padx=10, pady=8)
        self.ent_user = ttk.Entry(frame, width=30)
        self.ent_user.grid(row=0, column=1, padx=10, pady=8)
        self.ent_user.focus()

        ttk.Label(frame, text="Password:").grid(row=1, column=0, sticky="w", padx=10, pady=8)
        self.ent_pass = ttk.Entry(frame, width=30, show="*")
        self.ent_pass.grid(row=1, column=1, padx=10, pady=8)
        self.ent_pass.bind("<Return>", lambda e: self.do_login())

        ttk.Button(frame, text="Login", command=self.do_login).grid(row=2, column=1, sticky="e", padx=10, pady=12)

        hint = ttk.Label(
            frame,
            text="Default: admin / admin123",
            font=("Helvetica", 9),
            foreground="gray",
        )
        hint.grid(row=3, column=0, columnspan=2, pady=5)

    def do_login(self):
        username = self.ent_user.get().strip()
        password = self.ent_pass.get()
        if not username or not password:
            messagebox.showwarning("Login", "Username နှင့် Password ထည့်ပါ။")
            return
        user = authenticate(username, password)
        if not user:
            messagebox.showerror("Login Failed", "Username သို့မဟုတ် Password မှားနေပါသည်။")
            return
        self.user = user
        log_activity(user.get("user_id"), user.get("username"), "LOGIN", f"User '{user.get('username')}' logged in")
        self.destroy()
