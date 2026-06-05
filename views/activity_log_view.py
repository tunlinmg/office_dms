# views/activity_log_view.py
# User Activity Log (MVC View) — read-only list of user actions
import tkinter as tk
from tkinter import ttk

from models.activity_log_model import fetch_activity_logs


class ActivityLogView(ttk.Frame):
    """Read-only view showing recent user activity log entries."""

    LOG_COLS = ("log_id", "username", "action", "detail", "created_at")

    def __init__(self, parent, current_user):
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
            text="User Activity Log",
            font=("Segoe UI", 14, "bold"),
        ).pack(side="left")

        ttk.Button(
            toolbar,
            text="Refresh",
            command=self.refresh_data,
        ).pack(side="right", padx=4)

        # Table
        table_frame = ttk.Frame(self)
        table_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical")
        y_scroll.pack(side="right", fill="y")

        x_scroll = ttk.Scrollbar(table_frame, orient="horizontal")
        x_scroll.pack(side="bottom", fill="x")

        self.tree = ttk.Treeview(
            table_frame,
            columns=self.LOG_COLS,
            show="headings",
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set,
            selectmode="browse",
            height=20,
        )
        self.tree.pack(fill="both", expand=True)
        y_scroll.config(command=self.tree.yview)
        x_scroll.config(command=self.tree.xview)

        headers = {
            "log_id": "ID",
            "username": "Username",
            "action": "Action",
            "detail": "Detail",
            "created_at": "Timestamp",
        }
        widths = {
            "log_id": 60,
            "username": 130,
            "action": 200,
            "detail": 400,
            "created_at": 160,
        }
        for col in self.LOG_COLS:
            self.tree.heading(col, text=headers[col])
            self.tree.column(col, width=widths.get(col, 120), anchor="center")
        self.tree.column("detail", anchor="w")

        self.status_label = ttk.Label(self, text="")
        self.status_label.pack(anchor="w", padx=12, pady=(0, 8))

    # ------------------------------------------------------------------ data
    def refresh_data(self):
        self.tree.delete(*self.tree.get_children())
        logs = fetch_activity_logs()
        if not logs:
            self.status_label.config(text="No activity log entries found.")
            return
        for row in logs:
            ts = row.get("created_at", "")
            if hasattr(ts, "strftime"):
                ts = ts.strftime("%Y-%m-%d %H:%M:%S")
            else:
                ts = str(ts) if ts else ""
            self.tree.insert(
                "",
                "end",
                iid=str(row["log_id"]),
                values=(
                    row["log_id"],
                    row.get("username", ""),
                    row.get("action", ""),
                    row.get("detail", ""),
                    ts,
                ),
            )
        self.status_label.config(text=f"{len(logs)} log entries loaded.")