# views/settings_view.py
# View: System Settings page for admin-only database maintenance (MVC)
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

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