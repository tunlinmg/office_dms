# views/dashboard.py
# Controller: routes sidebar navigation to the correct View frame (MVC)
import importlib
import logging
import tkinter as tk
from tkinter import ttk, messagebox

from src.views.inletter_view import InletterView
from src.views.outletter_view import OutletterView
from src.views.doctype_view import DoctypeView
from src.views.action_view import ActionView
from src.views.dept_view import DeptView
from src.views.main_query import MainQueryView
from src.views.access_mgmt_view import AccessMgmtView
from src.views.role_mgmt_view import RoleMgmtView
from src.views.role_management import RoleManagementView
from src.views.settings_view import SettingsView
from src.views.module_settings_view import ModuleSettingsView
from src.models.role_model import user_can
from src.models.user_model import is_admin
from src.models.activity_log_model import log_activity
from src.models.module_manager import get_all_modules

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        filename="dms_errors.log",
        level=logging.ERROR,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

# ယခု ဖိုင်အသစ်များမှ Class များကို Import လုပ်ထားပါသည်
from src.views.inletter_query import InLetterQuery
from src.views.outletter_query import OutLetterQuery
from src.views.activity_log_view import ActivityLogView


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
        self._optional_modules = {}
        self._dynamic_modules = {}

        self.title("Office Document Management System (DMS)")
        self.geometry("1100x780")
        self.minsize(900, 650)

        self._load_optional_modules()
        self._load_dynamic_modules()
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
        
        # Configure custom scrollbar style for sidebar
        style.configure("Sidebar.Vertical.TScrollbar",
                        background="#475569",
                        troughcolor="#1e293b",
                        bordercolor="#1e293b",
                        arrowcolor="#94a3b8",
                        width=12)
        style.map("Sidebar.Vertical.TScrollbar",
                  background=[("active", "#64748b"), ("pressed", "#334155")])

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
                command=lambda: self.switch_view(ActivityLogView),
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
                command=lambda: self.switch_view(AccessMgmtView),
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
                command=lambda: self.switch_view(RoleMgmtView),
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
                command=lambda: self.switch_view(SettingsView),
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

    # ------------------------------------------------------------------ dynamic module loading
    def _load_optional_modules(self):
        """Dynamically load optional add-on modules from the modules/ folder.

        Each module should expose a MODULE_INFO dict with:
            key, label, title, subtitle, view_class
        If modules/ is empty or files are missing, silently skip.
        """
        try:
            from modules import MODULE_REGISTRY
            self._optional_modules = MODULE_REGISTRY
        except (ImportError, ModuleNotFoundError, AttributeError):
            self._optional_modules = {}

    def _load_dynamic_modules(self):
        """Query the database for active modules and load them via importlib.

        Fetches all modules from modules_registry where status=1,
        then uses importlib.import_module to dynamically load each file
        from the modules/ folder. Successfully loaded view classes are
        stored in self._dynamic_modules keyed by module_name.
        If no modules are registered or active, silently skip.
        """
        try:
            all_modules = get_all_modules()
            for mod in all_modules:
                if mod.get("status") != 1:
                    continue
                file_name = mod.get("file_name", "")
                module_name = mod.get("module_name", "")
                if not file_name or not module_name:
                    continue
                py_module_name = file_name.rsplit(".", 1)[0]
                try:
                    imported = importlib.import_module(f"modules.{py_module_name}")
                    view_class = getattr(imported, "ModuleView", None) or getattr(imported, "ActionView", None)
                    if view_class:
                        self._dynamic_modules[module_name] = view_class
                except (ImportError, ModuleNotFoundError, AttributeError) as e:
                    logger.warning("Could not load dynamic module '%s': %s", module_name, e)
        except Exception as e:
            logger.exception("Error loading dynamic modules")

    # ------------------------------------------------------------------ sidebar
    def _build_sidebar(self, parent):
        sidebar = tk.Frame(parent, bg=self.SIDEBAR_BG, width=self.SIDEBAR_WIDTH)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Header section (fixed at top)
        header_frame = tk.Frame(sidebar, bg=self.SIDEBAR_BG)
        header_frame.pack(side="top", fill="x")

        tk.Label(
            header_frame,
            text="DMS",
            font=("Segoe UI", 18, "bold"),
            bg=self.SIDEBAR_BG,
            fg=self.SIDEBAR_FG,
        ).pack(anchor="w", padx=20, pady=(24, 4))

        tk.Label(
            header_frame,
            text="Navigation",
            font=("Segoe UI", 9),
            bg=self.SIDEBAR_BG,
            fg="#94a3b8",
        ).pack(anchor="w", padx=20, pady=(0, 16))

        # Scrollable section for navigation buttons
        scroll_container = tk.Frame(sidebar, bg=self.SIDEBAR_BG)
        scroll_container.pack(side="top", fill="both", expand=True)

        # Create canvas
        self.sidebar_canvas = tk.Canvas(
            scroll_container,
            bg=self.SIDEBAR_BG,
            highlightthickness=0,
            borderwidth=0,
        )

        # Create scrollbar with custom style
        scrollbar = ttk.Scrollbar(
            scroll_container,
            orient="vertical",
            command=self.sidebar_canvas.yview,
            style="Sidebar.Vertical.TScrollbar",
        )

        # Create scrollable frame inside canvas
        self.scrollable_frame = tk.Frame(self.sidebar_canvas, bg=self.SIDEBAR_BG)
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.sidebar_canvas.configure(scrollregion=self.sidebar_canvas.bbox("all")),
        )

        # Create window inside canvas for the scrollable frame
        self.sidebar_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.sidebar_canvas.configure(yscrollcommand=scrollbar.set)

        # Pack scrollbar first (on right), then canvas (fills remaining space)
        scrollbar.pack(side="right", fill="y")
        self.sidebar_canvas.pack(side="left", fill="both", expand=True)

        # Bind mouse wheel to canvas
        def _on_mousewheel(event):
            self.sidebar_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.sidebar_canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Add navigation buttons to scrollable frame
        for item in self._get_nav_items():
            btn = tk.Button(
                self.scrollable_frame,
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

        # Dynamic modules from database (active modules)
        if self._dynamic_modules:
            tk.Label(
                self.scrollable_frame,
                text="Modules",
                font=("Segoe UI", 9),
                bg=self.SIDEBAR_BG,
                fg="#94a3b8",
            ).pack(anchor="w", padx=20, pady=(16, 8))

            for mod_key, view_class in self._dynamic_modules.items():
                mod_btn = tk.Button(
                    self.scrollable_frame,
                    text=f"  {mod_key}",
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
                    command=lambda k=mod_key: self._show_dynamic_module(k),
                )
                mod_btn.pack(fill="x", padx=8, pady=2)
                mod_btn.bind("<Enter>", lambda e, b=mod_btn: self._on_nav_enter(b))
                mod_btn.bind("<Leave>", lambda e, b=mod_btn, k=mod_key: self._on_nav_leave(b, k))
                self._nav_buttons[mod_key] = mod_btn

    # ------------------------------------------------------------------ MVC nav registry
    def _get_nav_items(self):
        """Navigation map: key -> View class"""
        items = [
            {"key": "inletter", "label": "  Inletter", "title": "ဝင်စာရင်းသွင်းဖောင်", "subtitle": "Inletter Entry"},
            {"key": "outletter", "label": "  Outletter", "title": "ထွက်စာရင်းသွင်းဖောင်", "subtitle": "Outletter Entry"},
            {"key": "doctype", "label": "  Doc Type", "title": "စာရွက်စာတမ်းအမျိုးအစား", "subtitle": "Document Type"},
            {"key": "action", "label": "  Action", "title": "လုပ်ငန်းစဉ်မှတ်တမ်း", "subtitle": "Action & Process"},
            {"key": "department", "label": "  Department", "title": "ဌာနဆိုင်ရာမှတ်တမ်း", "subtitle": "Department Entry"},

            {"key": "query", "label": "  Query / Report", "title": "စာရှာဖွေ / Report", "subtitle": "Search & Export"},
            {"key": "inletter_query", "label": "  Inletter Query", "title": "ဝင်စာ ရှာဖွေခြင်း", "subtitle": "Search Inletters"},
            {"key": "outletter_query", "label": "  Outletter Query", "title": "ထွက်စာ ရှာဖွေခြင်း", "subtitle": "Search Outletters"},

            {"key": "rows", "label": "  Row Management", "title": "စာရင်းအတန်းစီမံခန့်ခွဲမှု", "subtitle": "Edit & Delete Rows"},
        ]
        if user_can(self.current_user, "can_manage_roles"):
            items.append({
                "key": "roles",
                "label": "  Role Management",
                "title": "Role စီမံခန့်ခွဲမှု",
                "subtitle": "Define roles & permissions",
            })
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
            items.append({
                "key": "module_settings",
                "label": "  Module Settings",
                "title": "Module Management",
                "subtitle": "Register, activate, or remove modules",
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
            "query": (MainQueryView, {"current_user": self.current_user}),
            "inletter_query": (InLetterQuery, {"current_user": self.current_user}),
            "outletter_query": (OutLetterQuery, {"current_user": self.current_user}),
            "rows": (RoleManagementView, {"current_user": self.current_user}),
            "users": (AccessMgmtView, {"current_user": self.current_user}),
            "roles": (RoleMgmtView, {"current_user": self.current_user}),
            "user_logs": (ActivityLogView, {"current_user": self.current_user}),
            "settings": (SettingsView, {"current_user": self.current_user, "on_navigate": self.switch_view}),
            "module_settings": (ModuleSettingsView, {"current_user": self.current_user}),
        }
        # Also check dynamic modules loaded from database
        if key in self._dynamic_modules:
            return (self._dynamic_modules[key], {"current_user": self.current_user})
        return factories.get(key)

    # ------------------------------------------------------------------ controller actions
    def switch_view(self, view_class):
        """Destroy the current content frame and dynamically pack a new view.
        
        This method handles navigation from sub-views (like SettingsView) to other views.
        It properly passes on_navigate callback to views that need nested navigation.
        
        Args:
            view_class: The view class to instantiate (e.g., ModuleSettingsView, SettingsView).
        """
        self._clear_content()
        
        # Determine the nav key for this view class
        view_class_name = view_class.__name__
        nav_mapping = {
            "ModuleSettingsView": "module_settings",
            "SettingsView": "settings",
            "AccessMgmtView": "users",
            "RoleMgmtView": "roles",
            "ActivityLogView": "user_logs",
        }
        nav_key = nav_mapping.get(view_class_name)
        
        # Update navigation state if this is a known nav item
        if nav_key and nav_key in self._nav_buttons:
            self._active_key = nav_key
            self._highlight_nav(nav_key)
            # Update page title and subtitle
            meta = next((i for i in self._get_nav_items() if i["key"] == nav_key), None)
            if meta:
                self.page_title.config(text=meta["title"])
                self.page_subtitle.config(text=meta["subtitle"])
        
        # Prepare kwargs - SettingsView needs on_navigate for nested navigation
        # This allows the "Module Setting" button inside SettingsView to navigate
        view_kwargs = {"current_user": self.current_user}
        if view_class_name == "SettingsView":
            view_kwargs["on_navigate"] = self.switch_view
        
        # Create and pack the view with proper kwargs
        view_frame = view_class(self.content_container, **view_kwargs)
        view_frame.pack(fill="both", expand=True)

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
        if hasattr(view_frame, "refresh_data"):
            view_frame.after_idle(view_frame.refresh_data)

    def _show_optional_module(self, key):
        """Load an optional module view into the content area."""
        mod_info = self._optional_modules.get(key)
        if not mod_info:
            return
        self._active_key = key
        self._highlight_nav(key)
        self.page_title.config(text=mod_info.get("title", ""))
        self.page_subtitle.config(text=mod_info.get("subtitle", ""))
        self._clear_content()
        view_class = mod_info.get("view_class")
        if view_class:
            view_frame = view_class(self.content_container, self.current_user)
            view_frame.pack(fill="both", expand=True)

    def _show_dynamic_module(self, key):
        """Load a dynamically imported module view into the content area."""
        view_class = self._dynamic_modules.get(key)
        if not view_class:
            return
        self._active_key = key
        self._highlight_nav(key)
        self.page_title.config(text=key)
        self.page_subtitle.config(text="Dynamic Module")
        self._clear_content()
        view_frame = view_class(self.content_container, self.current_user)
        view_frame.pack(fill="both", expand=True)

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
            from src.views.login_view import LoginWindow
            import config

            config.init_db()
            login = LoginWindow()
            login.mainloop()
            if login.user:
                app = MainDashboard(login.user)
                app.mainloop()