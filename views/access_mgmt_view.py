# views/access_mgmt_view.py
# User Management (MVC View) — includes Email & Department
import tkinter as tk
from tkinter import ttk, messagebox

from models.user_model import fetch_all_users, insert_user, update_user, delete_user
from models.role_model import get_role_names
from models.dept_model import fetch_department_names


class AccessMgmtView(ttk.Frame):
    """User registration / management screen with a clean split layout."""

    USER_COLS = ("user_id", "username", "full_name", "email", "department", "role", "is_active", "created_at")

    def __init__(self, parent, current_user):
        super().__init__(parent)
        self.current_user = current_user
        self.selected_id = None
        self.dept_names = fetch_department_names() or ["General Office"]
        self.active_var = tk.IntVar(value=1)
        self._build_ui()
        self.load_users()

    def _build_ui(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=12, pady=(12, 8))

        ttk.Label(toolbar, text="User Management", font=("Segoe UI", 14, "bold")).pack(side="left")
        button_frame = ttk.Frame(toolbar)
        button_frame.pack(side="right")

        ttk.Button(button_frame, text="Refresh", command=self.load_users).pack(side="left", padx=4)
        ttk.Button(button_frame, text="Load Selected", command=self.populate_form_from_selection).pack(side="left", padx=4)
        ttk.Button(button_frame, text="Delete", command=self.remove_user).pack(side="left", padx=4)

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

        list_frame = ttk.LabelFrame(self.scrollable_frame, text="Users")
        list_frame.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        self.status_label = ttk.Label(list_frame, text="")
        self.status_label.pack(anchor="w", padx=8, pady=(8, 4))

        table_frame = ttk.Frame(list_frame)
        table_frame.pack(fill="both", expand=True, padx=8, pady=6)

        table_scrollbar = ttk.Scrollbar(table_frame, orient="vertical")
        table_scrollbar.pack(side="right", fill="y")

        self.tree = ttk.Treeview(
            table_frame,
            columns=self.USER_COLS,
            show="headings",
            yscrollcommand=table_scrollbar.set,
            selectmode="browse",
            height=12,
        )
        self.tree.pack(side="left", fill="both", expand=True)
        table_scrollbar.config(command=self.tree.yview)

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
        for col in self.USER_COLS:
            self.tree.heading(col, text=headers[col])
            self.tree.column(col, width=110, anchor="center")
        self.tree.column("email", width=180)
        self.tree.column("department", width=150)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        detail_panel = ttk.LabelFrame(self.scrollable_frame, text="User Details")
        detail_panel.pack(fill="x", padx=12, pady=(0, 12))
        detail_panel.columnconfigure(1, weight=1)
        detail_panel.columnconfigure(3, weight=1)

        ttk.Label(detail_panel, text="Username:").grid(row=0, column=0, sticky="e", padx=8, pady=6)
        self.ent_user = ttk.Entry(detail_panel)
        self.ent_user.grid(row=0, column=1, sticky="we", padx=8, pady=6)

        ttk.Label(detail_panel, text="Password:").grid(row=0, column=2, sticky="e", padx=8, pady=6)
        self.ent_pass = ttk.Entry(detail_panel, show="*")
        self.ent_pass.grid(row=0, column=3, sticky="we", padx=8, pady=6)

        ttk.Label(detail_panel, text="Full Name:").grid(row=1, column=0, sticky="e", padx=8, pady=6)
        self.ent_name = ttk.Entry(detail_panel)
        self.ent_name.grid(row=1, column=1, sticky="we", padx=8, pady=6)

        ttk.Label(detail_panel, text="Email:").grid(row=1, column=2, sticky="e", padx=8, pady=6)
        self.ent_email = ttk.Entry(detail_panel)
        self.ent_email.grid(row=1, column=3, sticky="we", padx=8, pady=6)

        ttk.Label(detail_panel, text="Department:").grid(row=2, column=0, sticky="e", padx=8, pady=6)
        self.cb_dept = ttk.Combobox(detail_panel, values=self.dept_names)
        self.cb_dept.grid(row=2, column=1, sticky="we", padx=8, pady=6)
        if self.dept_names:
            self.cb_dept.set(self.dept_names[0])

        ttk.Label(detail_panel, text="Role:").grid(row=2, column=2, sticky="e", padx=8, pady=6)
        self.cb_role = ttk.Combobox(detail_panel, values=get_role_names(), state="readonly")
        self.cb_role.grid(row=2, column=3, sticky="we", padx=8, pady=6)
        self.cb_role.set("user")

        self.active_checkbox = ttk.Checkbutton(detail_panel, text="Active account", variable=self.active_var)
        self.active_checkbox.grid(row=3, column=0, columnspan=2, sticky="w", padx=8, pady=(4, 10))

        self.selected_label = ttk.Label(detail_panel, text="No user selected", foreground="#4b5563")
        self.selected_label.grid(row=3, column=2, columnspan=2, sticky="w", padx=8, pady=(4, 10))

        actions = ttk.Frame(detail_panel)
        actions.grid(row=4, column=0, columnspan=4, pady=(0, 10), padx=8, sticky="w")
        ttk.Button(actions, text="Add User", command=self.add_user).pack(side="left", padx=4)
        ttk.Button(actions, text="Update User", command=self.update_user).pack(side="left", padx=4)
        ttk.Button(actions, text="Clear", command=self.clear_form).pack(side="left", padx=4)
        

    def refresh_data(self):
        self.load_users()

    def load_users(self):
        self.dept_names = fetch_department_names() or self.dept_names
        self.cb_dept.config(values=self.dept_names)
        self.cb_role.config(values=get_role_names())
        self.tree.delete(*self.tree.get_children())
        users = fetch_all_users()
        if not users:
            self.status_label.config(text="No users in database.")
            return
        for user in users:
            created = user.get("created_at", "")
            if hasattr(created, "strftime"):
                created = created.strftime("%Y-%m-%d %H:%M")
            else:
                created = str(created) if created else ""
            self.tree.insert(
                "",
                "end",
                iid=str(user["user_id"]),
                values=(
                    user["user_id"],
                    user["username"],
                    user["full_name"],
                    user.get("email", ""),
                    user.get("department", ""),
                    user["role"],
                    "Yes" if user["is_active"] else "No",
                    created,
                ),
            )
        self.status_label.config(text=f"{len(users)} user(s) loaded.")

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "ရွေးချယ်ပါ။")
            return None
        return int(sel[0])

    def _on_select(self, _event=None):
        self.populate_form_from_selection()

    def clear_form(self):
        self.selected_id = None
        self.selected_label.config(text="No user selected")
        self.ent_user.delete(0, tk.END)
        self.ent_pass.delete(0, tk.END)
        self.ent_name.delete(0, tk.END)
        self.ent_email.delete(0, tk.END)
        self.active_var.set(1)
        if self.dept_names:
            self.cb_dept.set(self.dept_names[0])
        self.cb_role.config(values=get_role_names())
        self.cb_role.set("user")

    def populate_form_from_selection(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Select a user to load.")
            return
        values = self.tree.item(sel[0], "values")
        if not values:
            return
        self.selected_id = int(values[0])
        self.selected_label.config(text=f"Selected user ID: {self.selected_id}")
        self.ent_user.delete(0, tk.END)
        self.ent_user.insert(0, values[1])
        self.ent_name.delete(0, tk.END)
        self.ent_name.insert(0, values[2])
        self.ent_email.delete(0, tk.END)
        self.ent_email.insert(0, values[3] if len(values) > 3 else "")
        self.cb_dept.set(values[4] if len(values) > 4 and values[4] else (self.dept_names[0] if self.dept_names else ""))
        self.cb_role.set(values[5] if len(values) > 5 and values[5] else "user")
        self.active_var.set(1 if (len(values) > 6 and values[6] == "Yes") else 0)

    def add_user(self):
        username = self.ent_user.get().strip()
        password = self.ent_pass.get()
        full_name = self.ent_name.get().strip()
        email = self.ent_email.get().strip()
        department = self.cb_dept.get().strip()
        role = self.cb_role.get().strip().lower()
        if not username or len(password) < 4:
            messagebox.showwarning("Validation", "Username နှင့် Password (၄ လ+) ထည့်ပါ။")
            return
        if not department and role != "admin":
            messagebox.showwarning("Validation", "Department ထည့်ပါ။")
            return
        if insert_user(username, password, full_name, email, department, role, self.active_var.get()):
            messagebox.showinfo("Success", "User created.")
            self.clear_form()
            self.load_users()

    def update_user(self):
        if self.selected_id is None:
            messagebox.showwarning("Select", "Select a user first to update.")
            return
        username = self.ent_user.get().strip()
        password = self.ent_pass.get()
        full_name = self.ent_name.get().strip()
        email = self.ent_email.get().strip()
        department = self.cb_dept.get().strip()
        role = self.cb_role.get().strip().lower()
        if not username:
            messagebox.showwarning("Validation", "Username cannot be empty.")
            return
        if not department and role != "admin":
            messagebox.showwarning("Validation", "Department ထည့်ပါ။")
            return
        if update_user(
            self.selected_id,
            username,
            full_name,
            email,
            department,
            role,
            self.active_var.get(),
            password or None,
        ):
            messagebox.showinfo("Success", "User updated.")
            self.load_users()
            if self.tree.exists(str(self.selected_id)):
                self.tree.selection_set(str(self.selected_id))

    def remove_user(self):
        uid = self._selected_id()
        if uid is None:
            return
        if messagebox.askyesno("Confirm", f"Delete user {uid}?"):
            if delete_user(uid, self.current_user["user_id"]):
                messagebox.showinfo("Success", "Deleted.")
                self.selected_id = None
                self.clear_form()
                self.load_users()

UserMgmtView = AccessMgmtView
