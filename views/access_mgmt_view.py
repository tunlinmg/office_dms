# views/access_mgmt_view.py
# User Management (MVC View) — includes Email & Department
import tkinter as tk
from tkinter import ttk, messagebox

from models.user_model import fetch_all_users, insert_user, update_user, update_user_role, delete_user
from models.role_model import get_role_names
from models.dept_model import fetch_department_names


class AccessMgmtView(ttk.Frame):
    """User registration / management screen."""

    USER_COLS = ("user_id", "username", "full_name", "email", "department", "role", "is_active", "created_at")

    def __init__(self, parent, current_user):
        super().__init__(parent)
        self.current_user = current_user
        self.selected_id = None
        self.dept_names = fetch_department_names() or ["General Office"]
        self.setup_ui()
        self.load_users()

    def setup_ui(self):
        top = ttk.LabelFrame(self, text=" User Management ")
        top.pack(fill="x", padx=15, pady=10)

        toolbar = ttk.Frame(top)
        toolbar.pack(fill="x", padx=10, pady=8)

        ttk.Label(toolbar, text="Assign role:").pack(side="left", padx=(0, 4))
        self.cb_role = ttk.Combobox(toolbar, values=get_role_names(), width=14, state="readonly")
        self.cb_role.pack(side="left", padx=4)
        self.cb_role.set("user")

        for text, cmd in [
            ("Refresh", self.load_users),
            ("Edit Selected", self.edit_user),
            ("Assign Role", self.assign_role),
            ("Delete Selected", self.remove_user),
        ]:
            ttk.Button(toolbar, text=text, command=cmd).pack(side="left", padx=4)

        add = ttk.LabelFrame(self, text=" Register New User ")
        add.pack(fill="x", padx=15, pady=4)
        row = ttk.Frame(add)
        row.pack(fill="x", padx=10, pady=8)

        ttk.Label(row, text="Username").grid(row=0, column=0, padx=4, pady=3)
        self.ent_user = ttk.Entry(row, width=14)
        self.ent_user.grid(row=0, column=1, padx=4, pady=3)

        ttk.Label(row, text="Password").grid(row=0, column=2, padx=4, pady=3)
        self.ent_pass = ttk.Entry(row, width=14, show="*")
        self.ent_pass.grid(row=0, column=3, padx=4, pady=3)

        ttk.Label(row, text="Full Name").grid(row=0, column=4, padx=4, pady=3)
        self.ent_name = ttk.Entry(row, width=16)
        self.ent_name.grid(row=0, column=5, padx=4, pady=3)

        ttk.Label(row, text="Email").grid(row=1, column=0, padx=4, pady=3)
        self.ent_email = ttk.Entry(row, width=14)
        self.ent_email.grid(row=1, column=1, padx=4, pady=3)

        ttk.Label(row, text="Department").grid(row=1, column=2, padx=4, pady=3)
        self.cb_dept = ttk.Combobox(row, values=self.dept_names, width=20)
        self.cb_dept.grid(row=1, column=3, columnspan=2, padx=4, pady=3, sticky="w")
        if self.dept_names:
            self.cb_dept.set(self.dept_names[0])

        ttk.Button(row, text="Add User", command=self.add_user).grid(row=1, column=5, padx=8, pady=3)

        grid = ttk.LabelFrame(self, text=" Users List ")
        grid.pack(fill="both", expand=True, padx=15, pady=8)

        self.status = ttk.Label(grid, text="")
        self.status.pack(anchor="w", padx=8, pady=4)

        wrap = ttk.Frame(grid)
        wrap.pack(fill="both", expand=True, padx=5, pady=5)
        sy = ttk.Scrollbar(wrap, orient="vertical")
        sy.pack(side="right", fill="y")
        self.tree = ttk.Treeview(wrap, columns=self.USER_COLS, show="headings", yscrollcommand=sy.set, height=14)
        self.tree.pack(side="left", fill="both", expand=True)
        sy.config(command=self.tree.yview)

        headers = {
            "user_id": "ID",
            "username": "Username",
            "full_name": "Full Name",
            "email": "Email",
            "department": "Department",
            "role": "Role",
            "is_active": "Active",
            "created_at": "Created",
        }
        for c in self.USER_COLS:
            self.tree.heading(c, text=headers[c])
            self.tree.column(c, width=110, anchor="center")
        self.tree.column("email", width=150)
        self.tree.column("department", width=130)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Double-1>", lambda _e: self.edit_user())

    def refresh_data(self):
        self.load_users()

    def load_users(self):
        self.dept_names = fetch_department_names() or self.dept_names
        self.cb_dept.config(values=self.dept_names)
        self.cb_role.config(values=get_role_names())
        self.tree.delete(*self.tree.get_children())
        users = fetch_all_users()
        if not users:
            self.status.config(text="No users in database.")
            return
        for u in users:
            created = u.get("created_at", "")
            if hasattr(created, "strftime"):
                created = created.strftime("%Y-%m-%d %H:%M")
            else:
                created = str(created) if created else ""
            self.tree.insert(
                "",
                "end",
                iid=str(u["user_id"]),
                values=(
                    u["user_id"],
                    u["username"],
                    u["full_name"],
                    u.get("email", ""),
                    u.get("department", ""),
                    u["role"],
                    "Yes" if u["is_active"] else "No",
                    created,
                ),
            )
        self.status.config(text=f"{len(users)} user(s) loaded.")

    def _selected_id(self):
        if self.selected_id:
            return self.selected_id
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "ရွေးချယ်ပါ။")
            return None
        return int(sel[0])

    def _on_select(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            return
        self.selected_id = int(sel[0])
        vals = self.tree.item(sel[0], "values")
        if len(vals) > 5:
            self.cb_role.set(vals[5])

    def assign_role(self):
        uid = self._selected_id()
        if uid is None:
            return
        role = self.cb_role.get().strip().lower()
        if update_user_role(uid, role):
            messagebox.showinfo("Success", f"User {uid} → role '{role}'")
            self.load_users()
            if self.tree.exists(str(uid)):
                self.tree.selection_set(str(uid))

    def add_user(self):
        u = self.ent_user.get().strip()
        p = self.ent_pass.get()
        n = self.ent_name.get().strip()
        email = self.ent_email.get().strip()
        dept = self.cb_dept.get().strip()
        role = self.cb_role.get().strip().lower()
        if not u or len(p) < 4:
            messagebox.showwarning("Validation", "Username နှင့် Password (၄ လ+) ထည့်ပါ။")
            return
        if not dept and role != "admin":
            messagebox.showwarning("Validation", "Department ထည့်ပါ။")
            return
        if insert_user(u, p, n, email, dept, role, 1):
            messagebox.showinfo("Success", "User created.")
            self.ent_user.delete(0, tk.END)
            self.ent_pass.delete(0, tk.END)
            self.ent_name.delete(0, tk.END)
            self.ent_email.delete(0, tk.END)
            self.load_users()

    def edit_user(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "ပြင်ရန် user ရွေးပါ။")
            return
        vals = self.tree.item(sel[0], "values")
        uid = int(vals[0])

        win = tk.Toplevel(self)
        win.title(f"Edit User #{uid}")
        win.geometry("460x360")
        win.grab_set()

        ttk.Label(win, text="Username:").grid(row=0, column=0, sticky="w", padx=10, pady=6)
        e_user = ttk.Entry(win, width=36)
        e_user.insert(0, vals[1])
        e_user.grid(row=0, column=1, padx=10, pady=6)

        ttk.Label(win, text="Full Name:").grid(row=1, column=0, sticky="w", padx=10, pady=6)
        e_name = ttk.Entry(win, width=36)
        e_name.insert(0, vals[2])
        e_name.grid(row=1, column=1, padx=10, pady=6)

        ttk.Label(win, text="Email:").grid(row=2, column=0, sticky="w", padx=10, pady=6)
        e_email = ttk.Entry(win, width=36)
        e_email.insert(0, vals[3] if len(vals) > 3 else "")
        e_email.grid(row=2, column=1, padx=10, pady=6)

        ttk.Label(win, text="Department:").grid(row=3, column=0, sticky="w", padx=10, pady=6)
        cb_dept = ttk.Combobox(win, values=self.dept_names, width=34)
        cb_dept.set(vals[4] if len(vals) > 4 else "")
        cb_dept.grid(row=3, column=1, padx=10, pady=6)

        ttk.Label(win, text="Role:").grid(row=4, column=0, sticky="w", padx=10, pady=6)
        cb = ttk.Combobox(win, values=get_role_names(), state="readonly", width=34)
        cb.set(vals[5] if len(vals) > 5 else "user")
        cb.grid(row=4, column=1, padx=10, pady=6)

        ttk.Label(win, text="Active:").grid(row=5, column=0, sticky="w", padx=10, pady=6)
        v_active = tk.IntVar(value=1 if (len(vals) > 6 and vals[6] == "Yes") else 0)
        ttk.Checkbutton(win, text="Enabled", variable=v_active, onvalue=1, offvalue=0).grid(
            row=5, column=1, sticky="w", padx=10
        )

        ttk.Label(win, text="New Password:").grid(row=6, column=0, sticky="w", padx=10, pady=6)
        e_pass = ttk.Entry(win, width=36, show="*")
        e_pass.grid(row=6, column=1, padx=10, pady=6)

        def save():
            if update_user(
                uid,
                e_user.get().strip(),
                e_name.get().strip(),
                e_email.get().strip(),
                cb_dept.get().strip(),
                cb.get().strip().lower(),
                v_active.get(),
                e_pass.get() or None,
            ):
                messagebox.showinfo("Success", "Updated.", parent=win)
                win.destroy()
                self.load_users()

        ttk.Button(win, text="Save", command=save).grid(row=7, column=1, sticky="e", padx=10, pady=12)

    def remove_user(self):
        uid = self._selected_id()
        if uid is None:
            return
        if messagebox.askyesno("Confirm", f"Delete user {uid}?"):
            if delete_user(uid, self.current_user["user_id"]):
                messagebox.showinfo("Success", "Deleted.")
                self.selected_id = None
                self.load_users()


UserMgmtView = AccessMgmtView
