# views/dashboard.py
# Controller: routes sidebar navigation to the correct View frame (MVC)
import tkinter as tk
from tkinter import ttk, messagebox

from views.inletter_view import InletterView
from views.outletter_view import OutletterView
from views.doctype_view import DoctypeView
from views.action_view import ActionView
from views.dept_view import DeptView
from views.main_query import MainQueryView
from views.access_mgmt_view import AccessMgmtView
from views.role_mgmt_view import RoleMgmtView
from views.role_management import RoleManagementView
from views.settings_view import SettingsView
from models.role_model import user_can
from models.user_model import is_admin
from models.activity_log_model import log_activity

# ယခု ဖိုင်အသစ်များမှ Class များကို Import လုပ်ထားပါသည်
from views.inletter_query import InLetterQuery
from views.outletter_query import OutLetterQuery
from views.activity_log_view import ActivityLogView


class MainDashboard(tk.Tk):
    """Main window controller — sidebar nav loads View frames on demand."""

    SIDEBAR_WIDTH = 240
    SIDEBAR_BG = "#1e293b"
    SIDEBAR_ACTIVE = "#334155"
    SIDEBAR_HOVER = "#475569"
    SIDEBAR_FG = "#f8fafc"
    CONTENT_BG = "#f1f5f9"

    def __init__(self, current_user):
        super().__init__()
        self.current_user = current_user
        self.role = current_user.get("role", "user")
        self._active_key = None
        self._nav_buttons = {}

        self.title("Office Document Management System (DMS)")
        self.geometry("1100x780")
        self.minsize(900, 650)

        self._setup_styles()
        self._build_layout()
        self.show_view("inletter")

    # ------------------------------------------------------------------ styles
    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Content.TFrame", background=self.CONTENT_BG)
        style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), background=self.CONTENT_BG)
        style.configure("SubHeader.TLabel", font=("Segoe UI", 10), background=self.CONTENT_BG, foreground="#475569")

    # ------------------------------------------------------------------ layout
    def _build_layout(self):
        self.configure(bg=self.CONTENT_BG)

        # Top header bar (spans full width above sidebar + content)
        self.header = tk.Frame(self, bg="#ffffff", height=56)
        self.header.pack(side="top", fill="x")
        self.header.pack_propagate(False)

        tk.Label(
            self.header,
            text="ရုံးသုံးစာရွက်စာတမ်းစီမံခန့်ခွဲမှုစနစ်",
            font=("Segoe UI", 14, "bold"),
            bg="#ffffff",
            fg="#0f172a",
        ).pack(side="left", padx=20, pady=12)

        name = self.current_user.get("full_name") or self.current_user.get("username")
        # Right-side header group: user label, Users and Roles quick buttons, Logout
        right_group = tk.Frame(self.header, bg="#ffffff")
        right_group.pack(side="right", padx=12, pady=8)

        tk.Label(
            right_group,
            text=f"{name}  ·  {self.role}",
            font=("Segoe UI", 10),
            bg="#ffffff",
            fg="#64748b",
        ).pack(side="left", padx=(0, 12), pady=6)

        # Quick-access: User activity log (visible to permitted admin account users)
        if user_can(self.current_user, "can_view_user_logs"):
            tk.Button(
                right_group,
                text="User Logs",
                font=("Segoe UI", 9),
                bg="#7c3aed",
                fg="white",
                activebackground="#6d28d9",
                activeforeground="white",
                relief="flat",
                padx=8,
                pady=4,
                cursor="hand2",
                command=lambda: self.show_view("user_logs"),
            ).pack(side="left", padx=(0, 8), pady=6)

        # Quick-access: User Management (visible to permitted users)
        if user_can(self.current_user, "can_manage_users"):
            tk.Button(
                right_group,
                text="Users",
                font=("Segoe UI", 9),
                bg="#059669",
                fg="white",
                activebackground="#047857",
                activeforeground="white",
                relief="flat",
                padx=8,
                pady=4,
                cursor="hand2",
                command=lambda: self.show_view("users"),
            ).pack(side="left", padx=(0, 8), pady=6)

        # Quick-access: Role Management (visible to permitted users)
        if user_can(self.current_user, "can_manage_roles"):
            tk.Button(
                right_group,
                text="Roles",
                font=("Segoe UI", 9),
                bg="#2563eb",
                fg="white",
                activebackground="#1e40af",
                activeforeground="white",
                relief="flat",
                padx=8,
                pady=4,
                cursor="hand2",
                command=lambda: self.show_view("roles"),
            ).pack(side="left", padx=(0, 8), pady=6)

        # Quick-access: Settings (admin only)
        if is_admin(self.current_user):
            tk.Button(
                right_group,
                text="Settings",
                font=("Segoe UI", 9),
                bg="#0f172a",
                fg="white",
                activebackground="#111827",
                activeforeground="white",
                relief="flat",
                padx=8,
                pady=4,
                cursor="hand2",
                command=lambda: self.show_view("settings"),
            ).pack(side="left", padx=(0, 8), pady=6)

        tk.Button(
            right_group,
            text="Logout",
            font=("Segoe UI", 9),
            bg="#ef4444",
            fg="white",
            activebackground="#dc2626",
            activeforeground="white",
            relief="flat",
            padx=12,
            pady=4,
            cursor="hand2",
            command=self.logout,
        ).pack(side="left", padx=(8, 0), pady=6)

        # Body: sidebar (left) + main content (right)
        body = tk.Frame(self, bg=self.CONTENT_BG)
        body.pack(side="top", fill="both", expand=True)

        self._build_sidebar(body)

        self.content_wrapper = ttk.Frame(body, style="Content.TFrame")
        self.content_wrapper.pack(side="left", fill="both", expand=True)

        # Page title inside content area
        title_bar = ttk.Frame(self.content_wrapper, style="Content.TFrame")
        title_bar.pack(side="top", fill="x", padx=24, pady=(16, 0))
        self.page_title = ttk.Label(title_bar, text="", style="Header.TLabel")
        self.page_title.pack(side="left")
        self.page_subtitle = ttk.Label(title_bar, text="", style="SubHeader.TLabel")
        self.page_subtitle.pack(side="left", padx=(12, 0))

        # Container cleared and repopulated when navigation changes
        self.content_container = ttk.Frame(self.content_wrapper, style="Content.TFrame")
        self.content_container.pack(side="top", fill="both", expand=True, padx=16, pady=16)

    def _build_sidebar(self, parent):
        sidebar = tk.Frame(parent, bg=self.SIDEBAR_BG, width=self.SIDEBAR_WIDTH)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(
            sidebar,
            text="DMS",
            font=("Segoe UI", 18, "bold"),
            bg=self.SIDEBAR_BG,
            fg=self.SIDEBAR_FG,
        ).pack(anchor="w", padx=20, pady=(24, 4))

        tk.Label(
            sidebar,
            text="Navigation",
            font=("Segoe UI", 9),
            bg=self.SIDEBAR_BG,
            fg="#94a3b8",
        ).pack(anchor="w", padx=20, pady=(0, 16))

        for item in self._get_nav_items():
            btn = tk.Button(
                sidebar,
                text=item["label"],
                font=("Segoe UI", 10),
                bg=self.SIDEBAR_BG,
                fg=self.SIDEBAR_FG,
                activebackground=self.SIDEBAR_ACTIVE,
                activeforeground=self.SIDEBAR_FG,
                relief="flat",
                anchor="w",
                padx=20,
                pady=10,
                cursor="hand2",
                command=lambda k=item["key"]: self.show_view(k),
            )
            btn.pack(fill="x", padx=8, pady=2)
            btn.bind("<Enter>", lambda e, b=btn: self._on_nav_enter(b))
            btn.bind("<Leave>", lambda e, b=btn, k=item["key"]: self._on_nav_leave(b, k))
            self._nav_buttons[item["key"]] = btn

    # ------------------------------------------------------------------ MVC nav registry
    def _get_nav_items(self):
        """Navigation map: key -> View class"""
        items = [
            {"key": "inletter", "label": "  Inletter", "title": "ဝင်စာရင်းသွင်းဖောင်", "subtitle": "Inletter Entry"},
            {"key": "outletter", "label": "  Outletter", "title": "ထွက်စာရင်းသွင်းဖောင်", "subtitle": "Outletter Entry"},
            {"key": "doctype", "label": "  Doc Type", "title": "စာရွက်စာတမ်းအမျိုးအစား", "subtitle": "Document Type"},
            {"key": "action", "label": "  Action", "title": "လုပ်ငန်းစဉ်မှတ်တမ်း", "subtitle": "Action & Process"},
            {"key": "department", "label": "  Department", "title": "ဌာနဆိုင်ရာမှတ်တမ်း", "subtitle": "Department Entry"},
            
            # ပြင်ဆင်ချက် - Key များ ထပ်မနေစေရန် သီးခြားစီ ခွဲထုတ်သတ်မှတ်ပေးလိုက်ပါသည်
            {"key": "query", "label": "  Query / Report", "title": "စာရှာဖွေ / Report", "subtitle": "Search & Export"},
            {"key": "inletter_query", "label": "  Inletter Query", "title": "ဝင်စာ ရှာဖွေခြင်း", "subtitle": "Search Inletters"},
            {"key": "outletter_query", "label": "  Outletter Query", "title": "ထွက်စာ ရှာဖွေခြင်း", "subtitle": "Search Outletters"},
            
            {"key": "rows", "label": "  Row Management", "title": "စာရင်းအတန်းစီမံခန့်ခွဲမှု", "subtitle": "Edit & Delete Rows"},
        ]
        # `users` is moved to the top header quick-access buttons; keep view factory mapping.
        if user_can(self.current_user, "can_manage_roles"):
            items.append({
                "key": "roles",
                "label": "  Role Management",
                "title": "Role စီမံခန့်ခွဲမှု",
                "subtitle": "Define roles & permissions",
            })
        # Include Users in nav registry so header 'Users' quick-button works
        if user_can(self.current_user, "can_manage_users"):
            items.append({
                "key": "users",
                "label": "  Users",
                "title": "User Management",
                "subtitle": "Add / Edit Users",
            })
        if user_can(self.current_user, "can_view_user_logs"):
            items.append({
                "key": "user_logs",
                "label": "  User Activity Log",
                "title": "User Activity Log",
                "subtitle": "View user actions & history",
            })
        if is_admin(self.current_user):
            items.append({
                "key": "settings",
                "label": "  System Settings",
                "title": "System Settings",
                "subtitle": "Backup, Restore, or Delete Database",
            })
        return items

    def _get_view_factory(self, key):
        """Return (ViewClass, kwargs) for the given navigation key."""
        factories = {
            "inletter": (InletterView, {"current_user": self.current_user}),
            "outletter": (OutletterView, {"current_user": self.current_user}),
            "doctype": (DoctypeView, {}),
            "action": (ActionView, {}),
            "department": (DeptView, {}),
            
            # ပြင်ဆင်ချက် - Sidebar ခလုတ်တစ်ခုချင်းစီအလိုက် သက်ဆိုင်ရာ View Class များကို မှန်ကန်စွာ ညွှန်းပေးထားပါသည်
            "query": (MainQueryView, {"current_user": self.current_user}),
            "inletter_query": (InLetterQuery, {"current_user": self.current_user}),
            "outletter_query": (OutLetterQuery, {"current_user": self.current_user}),
            
            "rows": (RoleManagementView, {"current_user": self.current_user}),
            "users": (AccessMgmtView, {"current_user": self.current_user}),
            "roles": (RoleMgmtView, {"current_user": self.current_user}),
            "user_logs": (ActivityLogView, {"current_user": self.current_user}),
            "settings": (SettingsView, {"current_user": self.current_user}),
        }
        return factories.get(key)

    # ------------------------------------------------------------------ controller actions
    def show_view(self, key):
        """Clear content container and load the selected View frame."""
        meta = next((i for i in self._get_nav_items() if i["key"] == key), None)
        factory = self._get_view_factory(key)
        if not meta or not factory:
            return

        view_class, kwargs = factory
        self._active_key = key
        self._highlight_nav(key)

        self.page_title.config(text=meta["title"])
        self.page_subtitle.config(text=meta["subtitle"])

        self._clear_content()
        view_frame = view_class(self.content_container, **kwargs)
        view_frame.pack(fill="both", expand=True)
        log_activity(
            self.current_user.get("user_id"), self.current_user.get("username"),
            "VIEW", f"Viewed page: {meta['title']} ({key})",
        )
        # Reload DB-backed lists each time the screen is opened (sidebar navigation)
        if hasattr(view_frame, "refresh_data"):
            view_frame.after_idle(view_frame.refresh_data)

    def _clear_content(self):
        for widget in self.content_container.winfo_children():
            widget.destroy()

    def _highlight_nav(self, active_key):
        for key, btn in self._nav_buttons.items():
            if key == active_key:
                btn.config(bg=self.SIDEBAR_ACTIVE, font=("Segoe UI", 10, "bold"))
            else:
                btn.config(bg=self.SIDEBAR_BG, font=("Segoe UI", 10))

    def _on_nav_enter(self, btn):
        if btn.cget("bg") != self.SIDEBAR_ACTIVE:
            btn.config(bg=self.SIDEBAR_HOVER)

    def _on_nav_leave(self, btn, key):
        if key == self._active_key:
            btn.config(bg=self.SIDEBAR_ACTIVE)
        else:
            btn.config(bg=self.SIDEBAR_BG)

    def logout(self):
        if messagebox.askyesno("Logout", "အကောင့်မှ ထွက်ရန် သေချာပါသလား?"):
            log_activity(
                self.current_user.get("user_id"), self.current_user.get("username"),
                "LOGOUT", f"User '{self.current_user.get('username')}' logged out",
            )
            self.destroy()
            from views.login_view import LoginWindow
            import config

            config.init_db()
            login = LoginWindow()
            login.mainloop()
            if login.user:
                app = MainDashboard(login.user)
                app.mainloop()