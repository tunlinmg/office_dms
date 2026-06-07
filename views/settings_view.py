# views/settings_view.py
# View: System Settings page for admin-only database maintenance (MVC)
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import config
from models.activity_log_model import log_activity
from models.user_model import is_admin


class SettingsView(ttk.Frame):
    """Admin-only view for database backup, restore, and delete operations."""

    def __init__(self, parent, current_user=None):
        super().__init__(parent)
        self.current_user = current_user
        self._setup_ui()

    def _setup_ui(self):
        """Build the settings UI or show access denied for non-admins."""
        if not is_admin(self.current_user):
            ttk.Label(self, text="Access denied.", font=("Segoe UI", 14, "bold")).pack(padx=20, pady=20)
            return

        title = ttk.Label(self, text="System Settings", font=("Segoe UI", 16, "bold"))
        title.pack(anchor="w", padx=24, pady=(8, 16))

        description = ttk.Label(
            self,
            text=(
                "Admin-only database maintenance: create a backup, restore from a SQL backup file, "
                "or delete and recreate the application database."
            ),
            font=("Segoe UI", 10),
            wraplength=760,
        )
        description.pack(anchor="w", padx=24, pady=(0, 16))

        button_frame = tk.Frame(self)
        button_frame.pack(anchor="w", padx=24, pady=4)

        # Action buttons for database operations
        self._create_action_button(
            button_frame,
            "Backup Database",
            "Create a SQL backup of the current database.",
            self.backup_database,
            bg="#2563eb",
        )
        self._create_action_button(
            button_frame,
            "Restore Database",
            "Restore database from an existing SQL backup file.",
            self.restore_database,
            bg="#059669",
        )
        self._create_action_button(
            button_frame,
            "Delete Database",
            "Delete and recreate the database. This will remove all current data.",
            self.delete_database,
            bg="#dc2626",
        )

    def _create_action_button(self, parent, text, tooltip, command, bg="#2563eb"):
        """Helper to create a styled action button with hover effect."""
        btn = tk.Button(
            parent,
            text=text,
            font=("Segoe UI", 10, "bold"),
            bg=bg,
            fg="white",
            activebackground="#1d4ed8",
            activeforeground="white",
            relief="flat",
            padx=14,
            pady=10,
            cursor="hand2",
            command=command,
        )
        btn.pack(side="left", padx=(0, 12), pady=6)
        btn.bind("<Enter>", lambda e: btn.config(relief="raised"))
        btn.bind("<Leave>", lambda e: btn.config(relief="flat"))

    def backup_database(self):
        """Prompt for a file path and back up the database to a SQL file."""
        filename = filedialog.asksaveasfilename(
            title="Save Database Backup",
            defaultextension=".sql",
            filetypes=[("SQL Files", "*.sql"), ("All Files", "*")],
        )
        if not filename:
            return
        if config.backup_database(filename):
            log_activity(
                self.current_user.get("user_id"),
                self.current_user.get("username"),
                "BACKUP_DB",
                f"Database backed up to {filename}",
            )
            messagebox.showinfo("Backup Complete", f"Database backup saved to:\n{filename}")

    def restore_database(self):
        """Prompt for a SQL backup file and restore the database from it."""
        filename = filedialog.askopenfilename(
            title="Select Database Backup File",
            filetypes=[("SQL Files", "*.sql"), ("All Files", "*")],
        )
        if not filename:
            return
        if not messagebox.askyesno(
            "Confirm Restore",
            "Restoring the database will overwrite the current database. Continue?",
        ):
            return
        if config.restore_database(filename):
            log_activity(
                self.current_user.get("user_id"),
                self.current_user.get("username"),
                "RESTORE_DB",
                f"Database restored from {filename}",
            )
            messagebox.showinfo("Restore Complete", "Database restored successfully.")

    def delete_database(self):
        """Confirm and delete the database, then recreate an empty one."""
        if not messagebox.askyesno(
            "Confirm Delete",
            "Deleting the database will remove all current records and recreate an empty database. Continue?",
        ):
            return
        if config.delete_database():
            log_activity(
                self.current_user.get("user_id"),
                self.current_user.get("username"),
                "DELETE_DB",
                "Database deleted and recreated empty.",
            )
            messagebox.showinfo("Delete Complete", "Database has been deleted and recreated.")