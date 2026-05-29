# views/role_mgmt_view.py
# Role Management — define roles and permissions (MVC View)
import tkinter as tk
from tkinter import ttk, messagebox

from models.role_model import (
    PERMISSION_KEYS,
    PERMISSION_LABELS,
    fetch_all_roles,
    insert_role,
    update_role,
    delete_role,
)


class RoleMgmtView(ttk.Frame):
    """Manage system roles and permission flags."""

    ROLE_COLS = ("role_id", "role_name", "description", "permissions")

    def __init__(self, parent, current_user=None):
        super().__init__(parent)
        self.current_user = current_user
        self.selected_role_id = None
        self._perm_vars = {}
        self.setup_ui()
        self.load_roles()

    def setup_ui(self):
        top = ttk.LabelFrame(self, text=" Role Management ")
        top.pack(fill="x", padx=15, pady=10)

        toolbar = ttk.Frame(top)
        toolbar.pack(fill="x", padx=10, pady=8)
        ttk.Button(toolbar, text="Refresh", command=self.load_roles).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Edit Selected", command=self.edit_role).pack(side="left", padx=4)
        ttk.Button(toolbar, text="Delete Selected", command=self.remove_role).pack(side="left", padx=4)

        add = ttk.LabelFrame(self, text=" Add New Role ")
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

        perm_box = ttk.LabelFrame(self, text=" Permissions for new role ")
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

        grid_frame = ttk.LabelFrame(self, text=" Roles List ")
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
        for col in self.ROLE_COLS:
            self.tree.heading(col, text=headers[col])
            w = 220 if col == "permissions" else (140 if col == "description" else 90)
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

    def load_roles(self):
        if not hasattr(self, "tree"):
            return
        self.tree.delete(*self.tree.get_children())
        roles = fetch_all_roles()
        if not roles:
            self.status_lbl.config(text="No roles found. Add a role above.")
            return
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
                ),
            )
        self.status_lbl.config(text=f"Loaded {len(roles)} role(s).")

    def _on_select(self, _event=None):
        sel = self.tree.selection()
        if sel:
            self.selected_role_id = int(sel[0])

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

        ttk.Label(win, text="Role name:").grid(row=0, column=0, sticky="w", padx=10, pady=6)
        e_name = ttk.Entry(win, width=38)
        e_name.insert(0, row["role_name"])
        e_name.grid(row=0, column=1, padx=10, pady=6)
        if row["role_name"] in ("admin", "user"):
            e_name.config(state="readonly")

        ttk.Label(win, text="Description:").grid(row=1, column=0, sticky="w", padx=10, pady=6)
        e_desc = ttk.Entry(win, width=38)
        e_desc.insert(0, row.get("description") or "")
        e_desc.grid(row=1, column=1, padx=10, pady=6)

        edit_vars = {}
        ttk.Label(win, text="Permissions:").grid(row=2, column=0, sticky="nw", padx=10, pady=6)
        pf = ttk.Frame(win)
        pf.grid(row=2, column=1, sticky="w", padx=10, pady=6)
        for key in PERMISSION_KEYS:
            var = tk.IntVar(value=1 if row.get(key) else 0)
            edit_vars[key] = var
            ttk.Checkbutton(pf, text=PERMISSION_LABELS[key], variable=var, onvalue=1, offvalue=0).pack(
                anchor="w", pady=2
            )

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

        ttk.Button(win, text="Save Permissions", command=save).grid(
            row=3, column=1, sticky="e", padx=10, pady=14
        )

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
