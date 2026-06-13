# views/settings_view.py
# View: System Settings page for admin-only database maintenance (MVC)
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import mysql.connector

import config
from src.models.activity_log_model import log_activity
from src.models.user_model import is_admin


class SettingsView(ttk.Frame):
    """Admin-only view for database backup, restore, delete, and module management."""

    def __init__(self, parent, current_user=None, on_navigate=None):
        """Initialize the SettingsView.
        
        Args:
            parent: The parent widget (content container from dashboard).
            current_user: Dictionary containing current user info (user_id, username, role).
            on_navigate: Callback function to dashboard's switch_view for navigation.
        """
        super().__init__(parent)
        self.current_user = current_user
        self.on_navigate = on_navigate  # callback to dashboard's switch_view
        self._setup_ui()

    def _setup_ui(self):
        """Build the settings UI or show access denied for non-admins.
        
        Creates the complete settings page layout including:
        - Page title and description
        - Database Operations section (Backup, Restore, Delete buttons)
        - Module Management section (Module Setting button)
        
        If the current user is not an admin, displays an access denied message instead.
        """
        # Check if user has admin privileges
        if not is_admin(self.current_user):
            # Show access denied message for non-admin users
            ttk.Label(self, text="Access denied.", font=("Segoe UI", 14, "bold")).pack(padx=20, pady=20)
            return

        # --- Page Header Section ---
        # Main title for the settings page
        title = ttk.Label(self, text="System Settings", font=("Segoe UI", 16, "bold"))
        title.pack(anchor="w", padx=24, pady=(8, 16))

        # Description text explaining the purpose of this page
        description = ttk.Label(
            self,
            text=(
                "Admin-only system maintenance: database operations and module management."
            ),
            font=("Segoe UI", 10),
            wraplength=760,
        )
        description.pack(anchor="w", padx=24, pady=(0, 16))

        # --- Database Operations Section ---
        # LabelFrame containing all database-related action buttons
        db_section = ttk.LabelFrame(self, text=" Database Operations ", padding=10)
        db_section.pack(fill="x", padx=24, pady=(0, 16))

        # Container frame for database operation buttons
        db_btn_frame = ttk.Frame(db_section)
        db_btn_frame.pack(fill="x")

        # Backup Database button - creates a SQL backup file
        self._create_action_button(
            db_btn_frame, "Backup Database",
            "Create a SQL backup of the current database.",
            self.backup_database, bg="#2563eb",  # Blue color
        )
        # Restore Database button - restores from a SQL backup file
        self._create_action_button(
            db_btn_frame, "Restore Database",
            "Restore database from an existing SQL backup file.",
            self.restore_database, bg="#059669",  # Green color
        )
        # Delete Database button - deletes and recreates empty database
        self._create_action_button(
            db_btn_frame, "Delete Database",
            "Delete and recreate the database. This will remove all current data.",
            self.delete_database, bg="#dc2626",  # Red color
        )
        # Config Database button - opens dialog to configure DB connection
        self._create_action_button(
            db_btn_frame, "Config Database",
            "Configure database server, name, user, and password.",
            self._open_db_config_dialog, bg="#d97706",  # Amber/Orange color
        )

        # --- Module Management Section ---
        # LabelFrame containing module-related action buttons
        mod_section = ttk.LabelFrame(self, text=" Module Management ", padding=10)
        mod_section.pack(fill="x", padx=24, pady=(0, 16))

        # Description text for module management section
        mod_desc = ttk.Label(
            mod_section,
            text="Register, activate, deactivate, or remove plugin modules.",
            font=("Segoe UI", 10),
            wraplength=760,
        )
        mod_desc.pack(anchor="w", pady=(0, 8))

        # Container frame for module management buttons
        mod_btn_frame = ttk.Frame(mod_section)
        mod_btn_frame.pack(fill="x")

        # Module Setting button - navigates to Module Settings View
        self._create_action_button(
            mod_btn_frame, "Module Setting",
            "Manage registered modules — add, toggle status, or delete.",
            self._open_module_setting, bg="#7c3aed",  # Purple color
        )

    def _create_action_button(self, parent, text, tooltip, command, bg="#2563eb"):
        """Helper to create a styled action button with hover effect.
        
        Creates a consistently styled button with:
        - Custom background color
        - White text
        - Hover effect (relief change)
        - Hand cursor on hover
        
        Args:
            parent: The parent widget to pack the button into.
            text: The button label text.
            tooltip: Tooltip text (currently unused, for future implementation).
            command: The callback function to execute when button is clicked.
            bg: Background color (hex color code).
        """
        # Create the button with specified styling
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
        # Pack button to the left with padding
        btn.pack(side="left", padx=(0, 12), pady=6)
        # Bind hover events for visual feedback
        btn.bind("<Enter>", lambda e: btn.config(relief="raised"))  # Raised on hover
        btn.bind("<Leave>", lambda e: btn.config(relief="flat"))    # Flat on leave

    # ── Database Configuration Dialog ─────────────────────────────────────────

    def _open_db_config_dialog(self):
        """Open a Toplevel dialog for configuring database connection settings."""
        dialog = tk.Toplevel(self)
        dialog.title("Database Configuration")
        dialog.geometry("420x340")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        # Center the dialog on the parent window
        dialog.update_idletasks()
        parent_x = self.winfo_toplevel().winfo_x()
        parent_y = self.winfo_toplevel().winfo_y()
        parent_w = self.winfo_toplevel().winfo_width()
        parent_h = self.winfo_toplevel().winfo_height()
        x = parent_x + (parent_w - 420) // 2
        y = parent_y + (parent_h - 340) // 2
        dialog.geometry(f"+{x}+{y}")

        # --- Dialog Header ---
        header = ttk.Label(
            dialog,
            text="Database Connection Settings",
            font=("Segoe UI", 13, "bold"),
        )
        header.pack(anchor="w", padx=20, pady=(16, 4))

        sub = ttk.Label(
            dialog,
            text="Configure the MySQL database connection parameters.",
            font=("Segoe UI", 9),
            foreground="#6b7280",
        )
        sub.pack(anchor="w", padx=20, pady=(0, 12))

        # --- Form Fields ---
        form_frame = ttk.Frame(dialog)
        form_frame.pack(fill="x", padx=20, pady=(0, 8))

        # Field definitions: (label, key, show_password)
        fields = [
            ("Database Server (Host):", "host", False),
            ("Database Name:", "database", False),
            ("Database User Name:", "user", False),
            ("Database Password:", "password", True),
        ]

        self._db_config_entries = {}
        for i, (label_text, key, is_password) in enumerate(fields):
            lbl = ttk.Label(form_frame, text=label_text, font=("Segoe UI", 9))
            lbl.grid(row=i, column=0, sticky="w", pady=(0, 2))

            var = tk.StringVar(value=config.DB_CONFIG.get(key, ""))
            entry = ttk.Entry(
                form_frame,
                textvariable=var,
                width=36,
                show="*" if is_password else "",
            )
            entry.grid(row=i, column=1, sticky="ew", padx=(10, 0), pady=(0, 8))
            self._db_config_entries[key] = var

        form_frame.columnconfigure(1, weight=1)

        # --- Status Label ---
        self._db_config_status = ttk.Label(
            dialog,
            text="",
            font=("Segoe UI", 9),
            foreground="#6b7280",
        )
        self._db_config_status.pack(anchor="w", padx=20, pady=(0, 8))

        # --- Buttons ---
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill="x", padx=20, pady=(0, 16))

        test_btn = tk.Button(
            btn_frame,
            text="Test Connection",
            font=("Segoe UI", 10, "bold"),
            bg="#2563eb",
            fg="white",
            activebackground="#1d4ed8",
            activeforeground="white",
            relief="flat",
            padx=14,
            pady=8,
            cursor="hand2",
            command=lambda: self._test_db_connection(dialog),
        )
        test_btn.pack(side="left", padx=(0, 10))
        test_btn.bind("<Enter>", lambda e: test_btn.config(relief="raised"))
        test_btn.bind("<Leave>", lambda e: test_btn.config(relief="flat"))

        save_btn = tk.Button(
            btn_frame,
            text="Save",
            font=("Segoe UI", 10, "bold"),
            bg="#059669",
            fg="white",
            activebackground="#047857",
            activeforeground="white",
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2",
            command=lambda: self._save_db_config(dialog),
        )
        save_btn.pack(side="left", padx=(0, 10))
        save_btn.bind("<Enter>", lambda e: save_btn.config(relief="raised"))
        save_btn.bind("<Leave>", lambda e: save_btn.config(relief="flat"))

        cancel_btn = tk.Button(
            btn_frame,
            text="Cancel",
            font=("Segoe UI", 10),
            bg="#6b7280",
            fg="white",
            activebackground="#4b5563",
            activeforeground="white",
            relief="flat",
            padx=14,
            pady=8,
            cursor="hand2",
            command=dialog.destroy,
        )
        cancel_btn.pack(side="right")
        cancel_btn.bind("<Enter>", lambda e: cancel_btn.config(relief="raised"))
        cancel_btn.bind("<Leave>", lambda e: cancel_btn.config(relief="flat"))

    def _test_db_connection(self, dialog):
        """Test the database connection using the values currently in the dialog fields.

        Attempts to connect to the MySQL server (without specifying a database) using
        the host, user, and password from the dialog. Shows a messagebox with the result.

        Args:
            dialog: The Toplevel dialog window (used for transient messagebox positioning).
        """
        host = self._db_config_entries["host"].get().strip()
        user = self._db_config_entries["user"].get().strip()
        password = self._db_config_entries["password"].get()
        database = self._db_config_entries["database"].get().strip()

        # Basic validation
        if not host:
            messagebox.showwarning("Validation Error", "Database Server (Host) is required.", parent=dialog)
            return
        if not user:
            messagebox.showwarning("Validation Error", "Database User Name is required.", parent=dialog)
            return
        if not database:
            messagebox.showwarning("Validation Error", "Database Name is required.", parent=dialog)
            return

        self._db_config_status.config(text="Testing connection...", foreground="#2563eb")
        dialog.update_idletasks()

        try:
            conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                charset="utf8mb4",
                use_unicode=True,
                connection_timeout=5,
            )
            conn.close()
            self._db_config_status.config(text="Connection successful!", foreground="#059669")
            messagebox.showinfo(
                "Test Connection",
                "Connection successful!\n\nThe database server is reachable with the provided credentials.",
                parent=dialog,
            )
        except mysql.connector.Error as err:
            self._db_config_status.config(text=f"Connection failed: {err}", foreground="#dc2626")
            messagebox.showerror(
                "Test Connection Failed",
                f"Could not connect to the database server.\n\nError: {err}",
                parent=dialog,
            )

    def _save_db_config(self, dialog):
        """Save the database configuration from the dialog fields.

        Validates the input, tests the connection, writes to db_config.json,
        updates the in-memory config.DB_CONFIG, and re-initializes the database.

        Args:
            dialog: The Toplevel dialog window to close on success.
        """
        host = self._db_config_entries["host"].get().strip()
        user = self._db_config_entries["user"].get().strip()
        password = self._db_config_entries["password"].get()
        database = self._db_config_entries["database"].get().strip()

        # Basic validation
        if not host:
            messagebox.showwarning("Validation Error", "Database Server (Host) is required.", parent=dialog)
            return
        if not user:
            messagebox.showwarning("Validation Error", "Database User Name is required.", parent=dialog)
            return
        if not database:
            messagebox.showwarning("Validation Error", "Database Name is required.", parent=dialog)
            return

        # Confirm before saving
        if not messagebox.askyesno(
            "Confirm Save",
            "Saving will update the database configuration and re-initialize the connection.\n\n"
            "Make sure the credentials are correct. Continue?",
            parent=dialog,
        ):
            return

        self._db_config_status.config(text="Saving configuration...", foreground="#2563eb")
        dialog.update_idletasks()

        # Build the new config dict
        new_config = {
            "host": host,
            "user": user,
            "password": password,
            "database": database,
            "charset": "utf8mb4",
        }

        # Test connection first
        try:
            conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                charset="utf8mb4",
                use_unicode=True,
                connection_timeout=5,
            )
            conn.close()
        except mysql.connector.Error as err:
            self._db_config_status.config(text=f"Connection failed: {err}", foreground="#dc2626")
            messagebox.showerror(
                "Save Failed",
                f"Could not connect to the database server with the provided credentials.\n\n"
                f"Error: {err}\n\nConfiguration was NOT saved.",
                parent=dialog,
            )
            return

        # Save to JSON and update in-memory config
        try:
            config.save_db_config(new_config)
        except Exception as err:
            self._db_config_status.config(text=f"Save error: {err}", foreground="#dc2626")
            messagebox.showerror(
                "Save Failed",
                f"Could not save configuration.\n\nError: {err}",
                parent=dialog,
            )
            return

        # Re-initialize the database with the new config
        try:
            config.init_db()
        except Exception as err:
            messagebox.showwarning(
                "Initialization Warning",
                f"Configuration saved, but database initialization encountered an issue:\n{err}\n\n"
                f"You may need to restart the application.",
                parent=dialog,
            )

        # Log the activity
        if self.current_user:
            log_activity(
                self.current_user.get("user_id"),
                self.current_user.get("username"),
                "CONFIG_DB",
                f"Database configuration updated. Host: {host}, Database: {database}, User: {user}",
            )

        messagebox.showinfo(
            "Configuration Saved",
            "Database configuration has been saved successfully.\n\n"
            "The connection has been updated. You may need to restart the application for all changes to take effect.",
            parent=dialog,
        )
        dialog.destroy()

    def _open_module_setting(self):
        """Navigate to the Module Settings view via the dashboard callback.

        This method is called when the "Module Setting" button is clicked.
        It uses the on_navigate callback to switch to the ModuleSettingsView.

        If the navigation callback is not available (on_navigate is None),
        displays an error message to the user.
        """
        if self.on_navigate:
            # Import the ModuleSettingsView and navigate to it
            from src.views.module_settings_view import ModuleSettingsView
            self.on_navigate(ModuleSettingsView)
        else:
            # Show error if navigation is not available
            messagebox.showerror("Error", "Navigation not available.")

    def backup_database(self):
        """Prompt for a file path and back up the database to a SQL file.
        
        This method:
        1. Opens a file save dialog for the user to choose backup location
        2. Calls the config.backup_database function to create the backup
        3. Logs the backup activity
        4. Shows a success message to the user
        
        If the user cancels the file dialog, no action is taken.
        """
        # Open file save dialog to get backup file path
        filename = filedialog.asksaveasfilename(
            title="Save Database Backup",
            defaultextension=".sql",
            filetypes=[("SQL Files", "*.sql"), ("All Files", "*")],
        )
        # Return if user cancelled the dialog
        if not filename:
            return
        # Perform the backup operation
        if config.backup_database(filename):
            # Log the backup activity
            log_activity(
                self.current_user.get("user_id"),
                self.current_user.get("username"),
                "BACKUP_DB",
                f"Database backed up to {filename}",
            )
            # Show success message
            messagebox.showinfo("Backup Complete", f"Database backup saved to:\n{filename}")

    def restore_database(self):
        """Prompt for a SQL backup file and restore the database from it.
        
        This method:
        1. Opens a file open dialog for the user to select a backup file
        2. Asks for confirmation before proceeding (destructive operation)
        3. Calls the config.restore_database function to restore the database
        4. Logs the restore activity
        5. Shows a success message to the user
        
        If the user cancels the file dialog or confirmation, no action is taken.
        """
        # Open file open dialog to select backup file
        filename = filedialog.askopenfilename(
            title="Select Database Backup File",
            filetypes=[("SQL Files", "*.sql"), ("All Files", "*")],
        )
        # Return if user cancelled the dialog
        if not filename:
            return
        # Ask for confirmation before restoring (destructive operation)
        if not messagebox.askyesno(
            "Confirm Restore",
            "Restoring the database will overwrite the current database. Continue?",
        ):
            return
        # Perform the restore operation
        if config.restore_database(filename):
            # Log the restore activity
            log_activity(
                self.current_user.get("user_id"),
                self.current_user.get("username"),
                "RESTORE_DB",
                f"Database restored from {filename}",
            )
            # Show success message
            messagebox.showinfo("Restore Complete", "Database restored successfully.")

    def delete_database(self):
        """Confirm and delete the database, then recreate an empty one.
        
        This method:
        1. Asks for confirmation before proceeding (destructive operation)
        2. Calls the config.delete_database function to delete and recreate the database
        3. Logs the delete activity
        4. Shows a success message to the user
        
        Warning: This will remove ALL current data from the database!
        If the user cancels the confirmation, no action is taken.
        """
        # Ask for confirmation before deleting (destructive operation)
        if not messagebox.askyesno(
            "Confirm Delete",
            "Deleting the database will remove all current records and recreate an empty database. Continue?",
        ):
            return
        # Perform the delete operation
        if config.delete_database():
            # Log the delete activity
            log_activity(
                self.current_user.get("user_id"),
                self.current_user.get("username"),
                "DELETE_DB",
                "Database deleted and recreated empty.",
            )
            # Show success message
            messagebox.showinfo("Delete Complete", "Database has been deleted and recreated.")