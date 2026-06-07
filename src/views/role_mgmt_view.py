# views/role_mgmt_view.py
# Role Management — define roles and permissions with a modern split-pane interface.
import tkinter as tk
from tkinter import ttk, messagebox

from src.models.role_model import (
    PERMISSION_KEYS,
    PERMISSION_LABELS,
    DEPT_PERMISSION_KEYS,
    DEPT_PERMISSION_LABELS,
    fetch_all_roles,
    fetch_role_department_summaries,
    fetch_department_permissions,
    save_department_permissions,
    insert_role,
    update_role,
    delete_role,
)
from src.models.dept_model import fetch_department_names


class RoleMgmtView(ttk.Frame):
    """Manage system roles and department-level permissions."""

    ROLE_COLS = ("role_id", "role_name", "description", "permissions", "departments", "dept_permissions")

    def __init__(self, parent, current_user=None):
        super().__init__(parent)
        self.current_user = current_user
        self.selected_role_id = None
        self.selected_role_name = None
        self._updating_ui = False  # Infinite Loop / Recursive Call တားဆီးရန် Flag variable
        
        self.dept_names = fetch_department_names() or [f"Department {i}" for i in range(1, 11)]
        self.perm_vars = {key: tk.IntVar(value=0) for key in PERMISSION_KEYS}
        self.dept_perm_vars = {key: tk.IntVar(value=0) for key in DEPT_PERMISSION_KEYS}
        self.dept_vars = {}
        
        self._build_ui()
        self.load_roles()

    def _build_ui(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=12, pady=(12, 8))

        ttk.Label(toolbar, text="Role Management", font=("Segoe UI", 14, "bold")).pack(side="left")
        toolbar_actions = ttk.Frame(toolbar)
        toolbar_actions.pack(side="right")

        ttk.Button(toolbar_actions, text="Refresh", command=self.load_roles).pack(side="left", padx=4)
        ttk.Button(toolbar_actions, text="Load Selected", command=self.load_selected_role).pack(side="left", padx=4)
        ttk.Button(toolbar_actions, text="Delete", command=self.remove_role).pack(side="left", padx=4)

        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, borderwidth=0, highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)

        self.scrollable_frame = ttk.Frame(canvas)
        self.canvas_window = canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfig(self.canvas_window, width=e.width),
        )

        list_frame = ttk.LabelFrame(self.scrollable_frame, text="Roles")
        list_frame.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        self.status_label = ttk.Label(list_frame, text="")
        self.status_label.pack(anchor="w", padx=8, pady=(8, 4))

        tree_frame = ttk.Frame(list_frame)
        tree_frame.pack(fill="both", expand=True, padx=8, pady=6)

        tree_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical")
        tree_scrollbar.pack(side="right", fill="y")

        self.tree = ttk.Treeview(
            tree_frame,
            columns=self.ROLE_COLS,
            show="headings",
            yscrollcommand=tree_scrollbar.set,
            selectmode="browse",
            height=12,
        )
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scrollbar.config(command=self.tree.yview)

        headings = {
            "role_id": "ID",
            "role_name": "Role",
            "description": "Description",
            "permissions": "Permissions",
            "departments": "Departments",
            "dept_permissions": "Dept Perms",
        }
        for col in self.ROLE_COLS:
            self.tree.heading(col, text=headings[col])
            width = 90
            if col == "description":
                width = 180
            elif col == "permissions":
                width = 160
            elif col == "departments":
                width = 140
            elif col == "dept_permissions":
                width = 120
            self.tree.column(col, width=width, anchor="w")

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        role_info = ttk.LabelFrame(self.scrollable_frame, text="Role details")
        role_info.pack(fill="x", padx=12, pady=(0, 8))
        role_info.columnconfigure(1, weight=1)

        ttk.Label(role_info, text="Role name:").grid(row=0, column=0, sticky="e", padx=8, pady=6)
        self.ent_role_name = ttk.Entry(role_info)
        self.ent_role_name.grid(row=0, column=1, sticky="we", padx=8, pady=6)

        ttk.Label(role_info, text="Description:").grid(row=1, column=0, sticky="e", padx=8, pady=6)
        self.ent_description = ttk.Entry(role_info)
        self.ent_description.grid(row=1, column=1, sticky="we", padx=8, pady=6)

        permissions_frame = ttk.LabelFrame(self.scrollable_frame, text="Role permissions")
        permissions_frame.pack(fill="x", padx=12, pady=(0, 8))

        for index, key in enumerate(PERMISSION_KEYS):
            ttk.Checkbutton(
                permissions_frame,
                text=PERMISSION_LABELS[key],
                variable=self.perm_vars[key],
                onvalue=1,
                offvalue=0,
            ).grid(row=index // 2, column=index % 2, sticky="w", padx=10, pady=4)

        buttons_frame = ttk.Frame(self.scrollable_frame)
        buttons_frame.pack(fill="x", padx=12, pady=(0, 8))
        ttk.Button(buttons_frame, text="Add Role", command=self.add_role).pack(side="left", padx=4)
        ttk.Button(buttons_frame, text="Update Role", command=self.update_role).pack(side="left", padx=4)
        ttk.Button(buttons_frame, text="Clear", command=self.clear_form).pack(side="left", padx=4)

        dept_frame = ttk.LabelFrame(self.scrollable_frame, text="Department permissions")
        dept_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        dept_frame.columnconfigure(0, weight=1)

        header = ttk.Frame(dept_frame)
        header.pack(fill="x", padx=8, pady=(8, 4))
        ttk.Label(header, text="Selected role:").pack(side="left")
        self.selected_role_label = ttk.Label(header, text="None", foreground="#4b5563")
        self.selected_role_label.pack(side="left", padx=6)

        self.dept_status = ttk.Label(dept_frame, text="Choose a role and departments to preview permissions.")
        self.dept_status.pack(fill="x", padx=8, pady=(0, 6))

        selector_frame = ttk.Frame(dept_frame)
        selector_frame.pack(fill="both", expand=True, padx=8, pady=4)

        canvas2 = tk.Canvas(selector_frame, borderwidth=0, highlightthickness=0, height=120)
        canvas2.pack(side="left", fill="both", expand=True)
        scrollbar2 = ttk.Scrollbar(selector_frame, orient="vertical", command=canvas2.yview)
        scrollbar2.pack(side="right", fill="y")
        canvas2.configure(yscrollcommand=scrollbar2.set)

        self.dept_check_container = ttk.Frame(canvas2)
        self._dept_canvas_id = canvas2.create_window((0, 0), window=self.dept_check_container, anchor="nw")
        self.dept_check_container.bind(
            "<Configure>",
            lambda e: canvas2.configure(scrollregion=canvas2.bbox("all")),
        )
        canvas2.bind(
            "<Configure>",
            lambda e: canvas2.itemconfig(self._dept_canvas_id, width=e.width),
        )
        self._build_department_checklist()

        dept_permission_frame = ttk.LabelFrame(dept_frame, text="Dept permission flags")
        dept_permission_frame.pack(fill="x", padx=8, pady=8)
        for index, key in enumerate(DEPT_PERMISSION_KEYS):
            ttk.Checkbutton(
                dept_permission_frame,
                text=DEPT_PERMISSION_LABELS[key],
                variable=self.dept_perm_vars[key],
                onvalue=1,
                offvalue=0,
            ).grid(row=index // 2, column=index % 2, sticky="w", padx=10, pady=4)

        ttk.Button(dept_frame, text="Save selected departments", command=self.save_department_role_permissions).pack(
            side="right", padx=8, pady=8
        )

    def _build_department_checklist(self):
        for widget in self.dept_check_container.winfo_children():
            widget.destroy()
        self.dept_vars = {}
        for index, dept in enumerate(self.dept_names):
            var = tk.BooleanVar(value=False)
            var.trace_add("write", lambda *_args: self._refresh_department_preview())
            self.dept_vars[dept] = var
            ttk.Checkbutton(
                self.dept_check_container,
                text=dept,
                variable=var,
                onvalue=True,
                offvalue=False,
            ).grid(row=index // 2, column=index % 2, sticky="w", padx=10, pady=4)

    def _get_selected_role_db_id(self):
        """Helper to safely get the database role_id from active selection."""
        sel = self.tree.selection()
        if not sel:
            return None
        try:
            return int(self.tree.set(sel[0], "role_id"))
        except (ValueError, IndexError):
            return None

    def _selected_departments(self):
        return [name for name, var in self.dept_vars.items() if var.get()]

    def _refresh_department_preview(self):
        # UI က data load လုပ်နေစဉ်အတွင်း Variable trace ကြောင့် loop ထပ်ပတ်ခြင်းကို ကျော်လွှာရန်
        if self._updating_ui:
            return

        if not self.selected_role_name:
            self.dept_status.config(text="Select a role to preview department permissions.")
            return
        departments = self._selected_departments()
        if not departments:
            self.dept_status.config(text="Select departments to preview permissions.")
            # ဘာမှမရွေးထားရင် Flag field တွေကို reset ချပေးခြင်း
            for var in self.dept_perm_vars.values():
                var.set(0)
            return

        perms = fetch_department_permissions(self.selected_role_name, departments)
        aggregated = {}
        mixed = []
        for key in DEPT_PERMISSION_KEYS:
            values = [perms.get(dept, {}).get(key, False) for dept in departments]
            if all(values):
                aggregated[key] = 1
            elif any(values):
                aggregated[key] = 0
                mixed.append(key)
            else:
                aggregated[key] = 0

        # UI state ကို စနစ်တကျ ပြောင်းလဲခြင်း
        self._updating_ui = True
        for key, var in self.dept_perm_vars.items():
            var.set(aggregated[key])
        self._updating_ui = False

        if mixed:
            mixed_names = ", ".join(DEPT_PERMISSION_LABELS[key] for key in mixed)
            self.dept_status.config(text=f"Mixed permissions: {mixed_names}")
        else:
            active = [DEPT_PERMISSION_LABELS[key] for key, value in aggregated.items() if value]
            self.dept_status.config(
                text=f"Active permissions: {', '.join(active)}" if active else "No active permissions for selected departments."
            )

    def _permission_summary(self, record):
        labels = [PERMISSION_LABELS[k] for k in PERMISSION_KEYS if record.get(k)]
        return ", ".join(labels) if labels else "None"

    def load_roles(self):
        self.tree.delete(*self.tree.get_children())
        roles = fetch_all_roles()
        if not roles:
            self.status_label.config(text="No roles found.")
            return
        summaries = fetch_role_department_summaries()
        for record in roles:
            self.tree.insert(
                "",
                "end",
                iid=str(record["role_id"]),
                values=(
                    record["role_id"],
                    record["role_name"],
                    record.get("description", ""),
                    self._permission_summary(record),
                    summaries.get(record["role_name"], {}).get("departments", ""),
                    summaries.get(record["role_name"], {}).get("dept_permissions", ""),
                ),
            )
        self.status_label.config(text=f"Loaded {len(roles)} role(s).")

    def _on_select(self, _event=None):
        if self._updating_ui:
            return
        self.load_selected_role()

    def load_selected_role(self):
        role_id = self._get_selected_role_db_id()
        if role_id is None:
            return

        roles_list = fetch_all_roles()
        record = next((r for r in roles_list if r["role_id"] == role_id), None)
        if not record:
            messagebox.showerror("Error", "Selected role could not be loaded.")
            return

        self._updating_ui = True
        try:
            self.selected_role_id = role_id
            self.selected_role_name = record["role_name"]
            self.selected_role_label.config(text=self.selected_role_name)
            
            self.ent_role_name.delete(0, tk.END)
            self.ent_role_name.insert(0, self.selected_role_name)
            self.ent_description.delete(0, tk.END)
            self.ent_description.insert(0, record.get("description", ""))
            
            for key in PERMISSION_KEYS:
                self.perm_vars[key].set(1 if record.get(key) else 0)
                
            # Role အသစ်တစ်ခု ရွေးလိုက်တိုင်း Checklist boxes များကို ခေတ္တအမှန်ခြစ်ဖြုတ်ပေးခြင်း
            for var in self.dept_vars.values():
                var.set(False)
                
            self.dept_status.config(text="Select departments to preview permissions.")
        finally:
            self._updating_ui = False
            
        self._refresh_department_preview()

    def add_role(self):
        role_name = self.ent_role_name.get().strip().lower()
        if not role_name:
            messagebox.showwarning("Validation", "Enter a role name.")
            return
        if insert_role(role_name, self.ent_description.get().strip(), {k: v.get() for k, v in self.perm_vars.items()}):
            messagebox.showinfo("Success", f"Role '{role_name}' created.")
            self.clear_form()
            self.load_roles()

    def update_role(self):
        if self.selected_role_id is None:
            messagebox.showwarning("Select", "Load a role before updating.")
            return
        role_name = self.ent_role_name.get().strip().lower()
        if not role_name:
            messagebox.showwarning("Validation", "Enter a role name.")
            return
        if update_role(
            self.selected_role_id,
            role_name,
            self.ent_description.get().strip(),
            {k: v.get() for k, v in self.perm_vars.items()},
        ):
            messagebox.showinfo("Success", "Role updated.")
            self.load_roles()
            self.selected_role_name = role_name
            self.selected_role_label.config(text=role_name)

    def save_department_role_permissions(self):
        if not self.selected_role_name:
            messagebox.showwarning("Select", "Load a role first.")
            return
        departments = self._selected_departments()
        if not departments:
            messagebox.showwarning("Validation", "Select at least one department.")
            return
        permissions = {k: v.get() for k, v in self.dept_perm_vars.items()}
        if save_department_permissions(self.selected_role_name, departments, permissions):
            messagebox.showinfo(
                "Success",
                f"Permissions saved for role '{self.selected_role_name}' on {len(departments)} department(s).",
            )
            self.load_roles()  # Treeview table ထဲက စာသားများပါ ချက်ချင်း update ဖြစ်သွားစေရန်
            self._refresh_department_preview()

    def remove_role(self):
        role_id = self._get_selected_role_db_id()
        if role_id is None:
            messagebox.showwarning("Select", "ဖျက်ရန် role ရွေးချယ်ပါ။")
            return
        role_record = next((r for r in fetch_all_roles() if r["role_id"] == role_id), None)
        if role_record and delete_role(role_record["role_id"], role_record["role_name"]):
            messagebox.showinfo("Success", "Role deleted.")
            self.clear_form()
            self.load_roles()

    def clear_form(self):
        self._updating_ui = True
        try:
            self.selected_role_id = None
            self.selected_role_name = None
            self.selected_role_label.config(text="None")
            self.ent_role_name.delete(0, tk.END)
            self.ent_description.delete(0, tk.END)
            for var in self.perm_vars.values():
                var.set(0)
            for var in self.dept_perm_vars.values():
                var.set(0)
            for var in self.dept_vars.values():
                var.set(False)
            self.dept_status.config(text="Choose a role and departments to preview permissions.")
        finally:
            self._updating_ui = False