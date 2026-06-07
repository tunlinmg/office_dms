# views/module_settings_view.py
import os
import shutil
import logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from src.models.module_manager import (
    register_new_module,
    toggle_module_status,
    delete_module_from_registry,
    get_all_modules,
)

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        filename="dms_errors.log",
        level=logging.ERROR,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

MODULES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "modules")


class ModuleSettingsView(ttk.Frame):
    """Module management screen — view, add, toggle, and delete registered modules."""

    COLS = ("id", "module_name", "file_name", "status", "description")

    def __init__(self, parent, current_user=None):
        super().__init__(parent)
        self.current_user = current_user
        self._build_ui()
        self.refresh_data()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=12, pady=(12, 8))

        ttk.Label(
            toolbar,
            text="Module Management",
            font=("Segoe UI", 14, "bold"),
        ).pack(side="left")

        btn_frame = ttk.Frame(toolbar)
        btn_frame.pack(side="right")

        ttk.Button(
            btn_frame, text="Add Module", command=self._add_module, width=14,
        ).pack(side="left", padx=4)

        ttk.Button(
            btn_frame, text="Activate / Deactivate", command=self._toggle_status, width=18,
        ).pack(side="left", padx=4)

        ttk.Button(
            btn_frame, text="Delete", command=self._delete_module, width=10,
        ).pack(side="left", padx=4)

        ttk.Button(
            btn_frame, text="Refresh", command=self.refresh_data, width=10,
        ).pack(side="left", padx=4)

        # Treeview table
        table_frame = ttk.Frame(self)
        table_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical")
        y_scroll.pack(side="right", fill="y")

        x_scroll = ttk.Scrollbar(table_frame, orient="horizontal")
        x_scroll.pack(side="bottom", fill="x")

        self.tree = ttk.Treeview(
            table_frame,
            columns=self.COLS,
            show="headings",
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set,
            selectmode="browse",
            height=15,
        )
        self.tree.pack(fill="both", expand=True)
        y_scroll.config(command=self.tree.yview)
        x_scroll.config(command=self.tree.xview)

        # Column headings and widths
        col_config = {
            "id": ("ID", 50),
            "module_name": ("Module Name", 180),
            "file_name": ("File Name", 180),
            "status": ("Status", 80),
            "description": ("Description", 300),
        }
        for col in self.COLS:
            heading, width = col_config[col]
            self.tree.heading(col, text=heading)
            self.tree.column(col, width=width, anchor="w")
        self.tree.column("id", anchor="center")
        self.tree.column("status", anchor="center")

        self.status_label = ttk.Label(self, text="")
        self.status_label.pack(anchor="w", padx=12, pady=(0, 8))

    # ------------------------------------------------------------------ data
    def refresh_data(self):
        """Reload modules from the database into the Treeview."""
        self.tree.delete(*self.tree.get_children())
        modules = get_all_modules()
        if not modules:
            self.status_label.config(text="No modules registered.")
            return
        for mod in modules:
            status_text = "Active" if mod.get("status") == 1 else "Inactive"
            self.tree.insert(
                "",
                "end",
                iid=str(mod["id"]),
                values=(
                    mod["id"],
                    mod.get("module_name", ""),
                    mod.get("file_name", ""),
                    status_text,
                    mod.get("description", ""),
                ),
            )
        self.status_label.config(text=f"{len(modules)} module(s) loaded.")

    # ------------------------------------------------------------------ helpers
    def _selected_id(self):
        """Return the selected module's database ID, or None."""
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select a module from the list.")
            return None
        return int(sel[0])

    # ------------------------------------------------------------------ actions
    def _add_module(self):
        """Open a file dialog to select a .py file, copy it to modules/, and register it."""
        filepath = filedialog.askopenfilename(
            title="Select a Python Module File",
            filetypes=[("Python Files", "*.py"), ("All Files", "*")],
        )
        if not filepath:
            return

        filename = os.path.basename(filepath)
        dest_path = os.path.join(MODULES_DIR, filename)

        # Prevent overwriting existing files
        if os.path.exists(dest_path):
            messagebox.showwarning(
                "File Exists",
                f"'{filename}' already exists in the modules folder. Choose a different file.",
            )
            return

        try:
            shutil.copy2(filepath, dest_path)
        except Exception as e:
            logger.exception("Could not copy file to modules/")
            messagebox.showerror("Copy Failed", f"Could not copy file:\n{e}")
            return

        # Derive a display name from the filename
        module_name = os.path.splitext(filename)[0].replace("_", " ").title()
        desc = f"Imported from {filename}"

        if register_new_module(module_name, filename, desc):
            messagebox.showinfo("Success", f"Module '{module_name}' registered successfully.")
            self.refresh_data()
        else:
            # Rollback: remove the copied file if DB insert failed
            try:
                os.remove(dest_path)
            except Exception:
                pass
            messagebox.showerror("Error", "Could not register module in the database.")

    def _toggle_status(self):
        """Toggle the selected module's status between 1 (active) and 0 (inactive)."""
        mod_id = self._selected_id()
        if mod_id is None:
            return

        # Find current status from the treeview
        sel = self.tree.selection()[0]
        values = self.tree.item(sel, "values")
        current_status = 1 if values[3] == "Active" else 0
        new_status = 0 if current_status == 1 else 1

        if toggle_module_status(mod_id, new_status):
            status_label = "Active" if new_status == 1 else "Inactive"
            messagebox.showinfo(
                "Success",
                f"Module ID {mod_id} is now {status_label}.",
            )
            self.refresh_data()
        else:
            messagebox.showerror("Error", "Could not update module status.")

    def _delete_module(self):
        """Delete the selected module's DB record and its physical file."""
        mod_id = self._selected_id()
        if mod_id is None:
            return

        if not messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete module ID {mod_id}?\n"
            "This will remove the database record and the physical file.",
        ):
            return

        # Get the filename from the treeview before deleting
        sel = self.tree.selection()[0]
        values = self.tree.item(sel, "values")
        filename = values[2]
        filepath = os.path.join(MODULES_DIR, filename)

        # Delete DB record first
        if not delete_module_from_registry(mod_id):
            messagebox.showerror("Error", "Could not delete module from the database.")
            return

        # Delete physical file
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            logger.exception("Could not delete file %s", filepath)
            messagebox.showwarning(
                "Partial Success",
                f"Database record deleted, but could not remove file:\n{e}",
            )
            self.refresh_data()
            return

        messagebox.showinfo("Success", f"Module '{values[1]}' deleted successfully.")
        self.refresh_data()