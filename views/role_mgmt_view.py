# views/role_mgmt_view.py
# Role Management — define roles and permissions (MVC View)
import tkinter as tk
from tkinter import ttk, messagebox

from models.role_model import (
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
from models.dept_model import fetch_department_names


class ScrollableFrame(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.scrollable_frame = ttk.Frame(self.canvas)
        self.window_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.window_id, width=e.width),
        )


class RoleMgmtView(ttk.Frame):
    """Manage system roles and permission flags."""

    ROLE_COLS = ("role_id", "role_name", "description", "permissions", "departments", "dept_permissions")

    def __init__(self, parent, current_user=None):
        super().__init__(parent)
        self.current_user = current_user
        self.selected_role_id = None
        self.selected_role_name = None
        self._perm_vars = {}
        self._dept_perm_vars = {}
        self.dept_names = fetch_department_names() or [f"Department-{i}" for i in range(1, 11)]
        self.dept_vars = {}
        self.setup_ui()
        self.load_roles()

    def setup_ui(self):
        container = ScrollableFrame(self)
        container.pack(fill="both", expand=True)
        content = container.scrollable_frame

        top = ttk.LabelFrame(content, text=" Role Management ")
        top.pack(fill="x", padx=15, pady=10)

        toolbar = ttk.Frame(top)
        toolbar.pack(fill="x", padx=10, pady=8)
        ttk.Button(toolbar, text="Refresh", command=self.load_roles).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Edit Selected", command=self.edit_role).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Save Permissions", command=self.save_department_role_permissions).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Delete Selected", command=self.remove_role).pack(side="left", padx=4)

        add = ttk.LabelFrame(content, text=" Add New Role ")
        add.pack(fill="x", padx=15, pady=4)
        f = ttk.Frame(add)
        f.pack(fill="x", padx=10, pady=8)

        ttk.Label(f, text="Role name:").grid(row=0, column=0, padx=5, pady=4, sticky="w")
        self.ent_role = ttk.Entry(f, width=18)
        self.ent_role.grid(row=0, column=1, padx=5, pady=4)

        ttk.Label(f, text="Description:").grid(row=0, column=2, padx=5, pady=4, sticky="w")
        self.ent_desc = ttk.Entry(f, width=35)
        self.ent_desc.grid(row=0, column=3, padx=5, pady=4)

        ttk.Button(f, text="Add Role", command=self.add_role).grid(row=0, column=4, padx=10, pady=4)

        perm_box = ttk.LabelFrame(content, text=" Permissions for new role ")
        perm_box.pack(fill="x", padx=15, pady=4)
        pf = ttk.Frame(perm_box)
        pf.pack(fill="x", padx=10, pady=8)
        for i, key in enumerate(PERMISSION_KEYS):
            var = tk.IntVar(value=0)
            self._perm_vars[key] = var
            ttk.Checkbutton(
                pf,
                text=PERMISSION_LABELS[key],
                variable=var,
                onvalue=1,
                offvalue=0,
            ).grid(row=i // 2, column=i % 2, sticky="w", padx=14, pady=3)

        dept_box = ttk.LabelFrame(content, text=" Department Permissions (per role) ")
        dept_box.pack(fill="x", padx=15, pady=4)
        header_row = ttk.Frame(dept_box)
        header_row.pack(fill="x", padx=10, pady=6)
        ttk.Label(header_row, text="Selected role:").pack(side="left")
        self.lbl_selected_role = ttk.Label(header_row, text="None")
        self.lbl_selected_role.pack(side="left", padx=(4, 0))
        self.lbl_role_dept_status = ttk.Label(
            dept_box,
            text="Select a role and departments to view department permission status.",
            foreground="blue",
        )
        self.lbl_role_dept_status.pack(fill="x", padx=10, pady=(0, 4))

        dept_selector = ttk.Frame(dept_box)
        dept_selector.pack(fill="both", padx=10, pady=4)
        canvas = tk.Canvas(dept_selector, height=180)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(dept_selector, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")
        canvas.configure(yscrollcommand=scrollbar.set)
        self.dept_check_frame = ttk.Frame(canvas)
        self.dept_check_frame_id = canvas.create_window((0, 0), window=self.dept_check_frame, anchor="nw")
        self.dept_check_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(self.dept_check_frame_id, width=e.width))
        self._build_department_checklist()

        dept_perm_sel = ttk.Frame(dept_box)
        dept_perm_sel.pack(fill="x", padx=10, pady=8)
        for i, key in enumerate(DEPT_PERMISSION_KEYS):
            var = tk.IntVar(value=0)
            self._dept_perm_vars[key] = var
            ttk.Checkbutton(
                dept_perm_sel,
                text=DEPT_PERMISSION_LABELS[key],
                variable=var,
                onvalue=1,
                offvalue=0,
            ).grid(row=i // 2, column=i % 2, sticky="w", padx=14, pady=3)

        ttk.Button(dept_box, text="Save to selected departments", command=self.save_department_role_permissions).pack(
            side="right", padx=10, pady=8
        )

        grid_frame = ttk.LabelFrame(content, text=" Roles List ")
        grid_frame.pack(fill="both", expand=True, padx=15, pady=8)

        self.status_lbl = ttk.Label(grid_frame, text="Loading roles...")
        self.status_lbl.pack(anchor="w", padx=8, pady=4)

        wrap = ttk.Frame(grid_frame)
        wrap.pack(fill="both", expand=True, padx=5, pady=5)

        scroll_y = ttk.Scrollbar(wrap, orient="vertical")
        scroll_y.pack(side="right", fill="y")

        self.tree = ttk.Treeview(
            wrap,
            columns=self.ROLE_COLS,
            show="headings",
            yscrollcommand=scroll_y.set,
            selectmode="browse",
            height=14,
        )
        self.tree.pack(side="left", fill="both", expand=True)
        scroll_y.config(command=self.tree.yview)

        headers = {"role_id": "ID", "role_name": "Role", "description": "Description", "permissions": "Permissions"}
        headers["departments"] = "Departments"
        headers["dept_permissions"] = "Dept Permissions"
        for col in self.ROLE_COLS:
            self.tree.heading(col, text=headers[col])
            if col == "permissions":
                w = 220
            elif col == "departments":
                w = 220
            elif col == "dept_permissions":
                w = 140
            else:
                w = 140 if col == "description" else 90
            self.tree.column(col, width=w, anchor="w")

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", lambda _e: self.edit_role())

    def refresh_data(self):
        self.load_roles()

    def _perms_summary(self, row):
        parts = [PERMISSION_LABELS[k].split()[0] for k in PERMISSION_KEYS if row.get(k)]
        return ", ".join(parts) if parts else "none"

    def _get_permissions_dict(self):
        return {k: self._perm_vars[k].get() for k in PERMISSION_KEYS}

    def _build_department_checklist(self):
        for widget in self.dept_check_frame.winfo_children():
            widget.destroy()
        self.dept_vars = {}
        for i, dept_name in enumerate(self.dept_names):
            var = tk.BooleanVar(value=False)
            self.dept_vars[dept_name] = var
            var.trace_add("write", lambda *_args: self._load_selected_role_department_permissions())
            ttk.Checkbutton(
                self.dept_check_frame,
                text=dept_name,
                variable=var,
                onvalue=True,
                offvalue=False,
            ).grid(row=i // 2, column=i % 2, sticky="w", padx=10, pady=3)

    def _get_selected_departments(self):
        return [name for name, var in self.dept_vars.items() if var.get()]

    def _get_department_permissions_dict(self):
        return {k: self._dept_perm_vars[k].get() for k in DEPT_PERMISSION_KEYS}

    def _update_selected_role_label(self):
        if self.selected_role_name:
            self.lbl_selected_role.config(text=self.selected_role_name)
        else:
            self.lbl_selected_role.config(text="None")

    def _set_department_permission_checkboxes(self, permissions):
        # `permissions` may be a dict mapping permission_key->bool or permission_key->None (mixed)
        for k, var in self._dept_perm_vars.items():
            val = permissions.get(k)
            # Treat None (mixed) as unchecked in the UI; status label will indicate mixed state
            var.set(1 if val else 0)

    def _load_selected_role_department_permissions(self):
        if not self.selected_role_name:
            self.lbl_role_dept_status.config(
                text="Select a role to view department permissions."
            )
            self._set_department_permission_checkboxes({})
            return

        departments = self._get_selected_departments()
        if not departments:
            self.lbl_role_dept_status.config(
                text="Select departments to preview current permission status."
            )
            self._set_department_permission_checkboxes({})
            return
        # fetch_department_permissions now returns a mapping: { department: {perm_key: bool} }
        per_dept = fetch_department_permissions(self.selected_role_name, departments)
        # Aggregate across selected departments to determine common/mixed permissions
        aggregated = {}
        mixed_keys = []
        for k in DEPT_PERMISSION_KEYS:
            vals = [per_dept.get(d, {}).get(k, False) for d in departments]
            if all(vals):
                aggregated[k] = True
            elif any(vals):
                aggregated[k] = False
                mixed_keys.append(k)
            else:
                aggregated[k] = False

        self._set_department_permission_checkboxes(aggregated)

        if mixed_keys:
            mixed_labels = [DEPT_PERMISSION_LABELS[k] for k in mixed_keys]
            self.lbl_role_dept_status.config(
                text=f"Mixed permissions across selected departments: {', '.join(mixed_labels)}"
            )
        else:
            enabled = [DEPT_PERMISSION_LABELS[k] for k, v in aggregated.items() if v]
            if enabled:
                self.lbl_role_dept_status.config(
                    text=f"Active permissions for {self.selected_role_name}: {', '.join(enabled)}"
                )
            else:
                self.lbl_role_dept_status.config(
                    text=f"No active department permissions set for {self.selected_role_name} on selected departments."
                )

    def load_roles(self):
        if not hasattr(self, "tree"):
            return
        self.tree.delete(*self.tree.get_children())
        roles = fetch_all_roles()
        if not roles:
            self.status_lbl.config(text="No roles found. Add a role above.")
            return
        dept_summaries = fetch_role_department_summaries()
        for r in roles:
            self.tree.insert(
                "",
                "end",
                iid=str(r["role_id"]),
                values=(
                    r["role_id"],
                    r["role_name"],
                    r.get("description", ""),
                    self._perms_summary(r),
                    dept_summaries.get(r["role_name"], {}).get("departments", ""),
                    dept_summaries.get(r["role_name"], {}).get("dept_permissions", "None"),
                ),
            )
        self.status_lbl.config(text=f"Loaded {len(roles)} role(s).")

    def _on_select(self, _event=None):
        sel = self.tree.selection()
        if sel:
            self.selected_role_id = int(sel[0])
            values = self.tree.item(sel[0], "values")
            if values and len(values) > 1:
                self.selected_role_name = str(values[1])
            else:
                self.selected_role_name = None
            self._update_selected_role_label()
            self._reset_department_permission_controls()
            self._load_selected_role_department_permissions()
        else:
            self.selected_role_id = None
            self.selected_role_name = None
            self._update_selected_role_label()
            self._reset_department_permission_controls()
            self._load_selected_role_department_permissions()

    def _reset_department_permission_controls(self):
        for var in self.dept_vars.values():
            var.set(False)
        for var in self._dept_perm_vars.values():
            var.set(0)

    def add_role(self):
        name = self.ent_role.get().strip().lower()
        if not name:
            messagebox.showwarning("Validation", "Role name ထည့်ပါ။")
            return
        if insert_role(name, self.ent_desc.get().strip(), self._get_permissions_dict()):
            messagebox.showinfo("Success", f"Role '{name}' created.")
            self.ent_role.delete(0, tk.END)
            self.ent_desc.delete(0, tk.END)
            for v in self._perm_vars.values():
                v.set(0)
            self.load_roles()

    def save_department_role_permissions(self):
        if not self.selected_role_name:
            messagebox.showwarning("Select", "Select a role from the list first.")
            return
        departments = self._get_selected_departments()
        if not departments:
            messagebox.showwarning("Validation", "Select at least one department.")
            return
        permissions = self._get_department_permissions_dict()
        if save_department_permissions(self.selected_role_name, departments, permissions):
            messagebox.showinfo(
                "Success",
                f"Permissions saved for role '{self.selected_role_name}' and {len(departments)} department(s).",
            )
            self._load_selected_role_department_permissions()

    def edit_role(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "ပြင်ရန် role ရွေးချယ်ပါ။")
            return

        values = self.tree.item(sel[0], "values")
        if not values or len(values) < 4:
            messagebox.showerror("Error", "Could not determine selected role.")
            return

        row = {
            "role_id": int(values[0]),
            "role_name": values[1],
            "description": values[2],
        }

        role_data = fetch_all_roles()
        matching = next((r for r in role_data if str(r["role_id"]) == sel[0]), None)
        if not matching:
            messagebox.showerror("Error", "Could not load selected role.")
            return
        row.update(matching)

        win = tk.Toplevel(self)
        win.title(f"Edit Role — {row['role_name']}")
        win.geometry("500x400")
        win.grab_set()

        container = ScrollableFrame(win)
        container.pack(fill="both", expand=True)
        content = container.scrollable_frame
        content.columnconfigure(1, weight=1)

        ttk.Label(content, text="Role name:").grid(row=0, column=0, sticky="w", padx=10, pady=6)
        e_name = ttk.Entry(content, width=38)
        e_name.insert(0, row["role_name"])
        e_name.grid(row=0, column=1, padx=10, pady=6)
        if row["role_name"] in ("admin", "user"):
            e_name.config(state="readonly")

        ttk.Label(content, text="Description:").grid(row=1, column=0, sticky="w", padx=10, pady=6)
        e_desc = ttk.Entry(content, width=38)
        e_desc.insert(0, row.get("description") or "")
        e_desc.grid(row=1, column=1, padx=10, pady=6)

        edit_vars = {}
        ttk.Label(content, text="Permissions:").grid(row=2, column=0, sticky="nw", padx=10, pady=6)
        pf = ttk.Frame(content)
        pf.grid(row=2, column=1, sticky="w", padx=10, pady=6)
        for key in PERMISSION_KEYS:
            var = tk.IntVar(value=1 if row.get(key) else 0)
            edit_vars[key] = var
            ttk.Checkbutton(pf, text=PERMISSION_LABELS[key], variable=var, onvalue=1, offvalue=0).pack(
                anchor="w", pady=2
            )

        score_value = tk.IntVar(value=sum(v.get() for v in edit_vars.values()))
        score_text = ttk.Label(content, text=f"Permission Score: {score_value.get()}/{len(PERMISSION_KEYS)}")
        score_text.grid(row=3, column=0, sticky="w", padx=10, pady=(0, 6))
        score_bar = ttk.Progressbar(content, length=280, maximum=len(PERMISSION_KEYS), variable=score_value)
        score_bar.grid(row=3, column=1, sticky="w", padx=10, pady=(0, 6))

        def update_permission_score(*_args):
            count = sum(v.get() for v in edit_vars.values())
            score_value.set(count)
            score_text.config(text=f"Permission Score: {count}/{len(PERMISSION_KEYS)}")

        for var in edit_vars.values():
            var.trace_add("write", update_permission_score)

        ttk.Label(content, text="Departments:").grid(row=4, column=0, sticky="nw", padx=10, pady=6)
        dept_selector_frame = ttk.Frame(content)
        dept_selector_frame.grid(row=4, column=1, sticky="w", padx=10, pady=6)

        canvas = tk.Canvas(dept_selector_frame, height=120, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(dept_selector_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        dept_check_frame = ttk.Frame(canvas)
        dept_frame_id = canvas.create_window((0, 0), window=dept_check_frame, anchor="nw")
        dept_check_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfig(dept_frame_id, width=e.width),
        )

        dept_selection_vars = {}
        for i, dept_name in enumerate(self.dept_names):
            var = tk.BooleanVar(value=False)
            dept_selection_vars[dept_name] = var
            ttk.Checkbutton(
                dept_check_frame,
                text=dept_name,
                variable=var,
                onvalue=True,
                offvalue=False,
            ).grid(row=i // 2, column=i % 2, sticky="w", padx=10, pady=2)

        ttk.Label(content, text="Department Permissions:").grid(row=5, column=0, sticky="nw", padx=10, pady=6)
        dpf = ttk.Frame(content)
        dpf.grid(row=5, column=1, sticky="w", padx=10, pady=6)
        dept_edit_vars = {}
        for i, key in enumerate(DEPT_PERMISSION_KEYS):
            var = tk.IntVar(value=0)
            dept_edit_vars[key] = var
            ttk.Checkbutton(
                dpf,
                text=DEPT_PERMISSION_LABELS[key],
                variable=var,
                onvalue=1,
                offvalue=0,
            ).grid(row=i // 2, column=i % 2, sticky="w", padx=10, pady=2)

        def load_department_permissions(*_args):
            departments = [name for name, var in dept_selection_vars.items() if var.get()]
            if not departments:
                for k in DEPT_PERMISSION_KEYS:
                    dept_edit_vars[k].set(0)
                return
            per_dept = fetch_department_permissions(row["role_name"], departments)
            # Aggregate: set checkbox if permission is True for all selected departments
            for k in DEPT_PERMISSION_KEYS:
                vals = [per_dept.get(d, {}).get(k, False) for d in departments]
                dept_edit_vars[k].set(1 if all(vals) else 0)

        for var in dept_selection_vars.values():
            var.trace_add("write", load_department_permissions)

        def save():
            perms = {k: edit_vars[k].get() for k in PERMISSION_KEYS}
            if update_role(row["role_id"], e_name.get().strip().lower(), e_desc.get().strip(), perms):
                messagebox.showinfo(
                    "Success",
                    "Role updated. Users must re-login to apply new permissions.",
                    parent=win,
                )
                win.destroy()
                self.load_roles()

        def save_department_permissions_for_role():
            departments = [name for name, var in dept_selection_vars.items() if var.get()]
            if not departments:
                messagebox.showwarning(
                    "Validation",
                    "Select at least one department before saving department permissions.",
                    parent=win,
                )
                return
            perms = {k: dept_edit_vars[k].get() for k in DEPT_PERMISSION_KEYS}
            if save_department_permissions(row["role_name"], departments, perms):
                messagebox.showinfo(
                    "Success",
                    f"Department permissions saved for role '{row['role_name']}' and {len(departments)} department(s).",
                    parent=win,
                )

        button_frame = ttk.Frame(content)
        button_frame.grid(row=6, column=1, sticky="e", padx=10, pady=4)
        ttk.Button(button_frame, text="Update Role", command=save).pack(side="left", padx=4)
        ttk.Button(button_frame, text="Save Department Permissions", command=save_department_permissions_for_role).pack(side="left", padx=4)

    def remove_role(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "ဖျက်ရန် role ရွေးချယ်ပါ။")
            return
        roles_map = {str(r["role_id"]): r for r in fetch_all_roles()}
        row = roles_map.get(sel[0])
        if row and delete_role(row["role_id"], row["role_name"]):
            messagebox.showinfo("Success", "Role deleted.")
            self.selected_role_id = None
            self.load_roles()
