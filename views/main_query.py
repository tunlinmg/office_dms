# views/main_query.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
from config import get_db_connection
from models.user_model import apply_department_sql, is_admin, get_user_department


class MainQueryView(ttk.Frame):
    def __init__(self, parent, current_user=None):
        super().__init__(parent)
        self.current_user = current_user or {}
        self.setup_ui()

    def setup_ui(self):
        filter_frame = ttk.LabelFrame(self, text=" စာရှာဖွေရန် သတ်မှတ်ချက်များ (Search Filters) ")
        filter_frame.pack(fill="x", padx=15, pady=10)

        dept_hint = "All departments" if is_admin(self.current_user) else f"Dept: {get_user_department(self.current_user)}"
        ttk.Label(filter_frame, text=dept_hint, font=("Segoe UI", 9)).grid(row=0, column=4, padx=10, pady=5, sticky="e")

        ttk.Label(filter_frame, text="File ID:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.ent_id = ttk.Entry(filter_frame, width=15)
        self.ent_id.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        ttk.Label(filter_frame, text="Letter Type:").grid(row=0, column=2, padx=10, pady=5, sticky="w")
        self.ent_type = ttk.Entry(filter_frame, width=20)
        self.ent_type.grid(row=0, column=3, padx=10, pady=5, sticky="w")

        ttk.Label(filter_frame, text="အကြောင်းအရာ (Title):").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.ent_title = ttk.Entry(filter_frame, width=40)
        self.ent_title.grid(row=1, column=1, columnspan=3, padx=10, pady=5, sticky="w")

        btn_frame = ttk.Frame(filter_frame)
        btn_frame.grid(row=2, column=0, columnspan=4, pady=10)

        ttk.Button(btn_frame, text="ရှာဖွေရန် (Search)", command=self.search_data).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="စ်ပြန်စရန် (Reset)", command=self.reset_filters).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="CSV ဖြင့်ထုတ်ရန် (Export CSV)", command=self.export_to_csv).pack(side="left", padx=5)

        grid_frame = ttk.LabelFrame(self, text=" ရှာဖွေတွေ့ရှိသည့် ဝင်စာများ (Inletters — department filtered) ")
        grid_frame.pack(fill="both", expand=True, padx=15, pady=5)

        scroll_y = ttk.Scrollbar(grid_frame, orient="vertical")
        scroll_x = ttk.Scrollbar(grid_frame, orient="horizontal")

        columns = (
            "file_id", "letter_date", "send_date", "letter_type", "title",
            "security_lvl", "urgency_lvl", "dept_from", "owner_department",
        )
        self.tree = ttk.Treeview(
            grid_frame, columns=columns, show="headings",
            yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set,
        )

        scroll_y.pack(side="right", fill="y")
        scroll_x.pack(side="bottom", fill="x")
        scroll_y.config(command=self.tree.yview)
        scroll_x.config(command=self.tree.xview)

        headings = {
            "file_id": "File ID", "letter_date": "Letter Date", "send_date": "Send Date",
            "letter_type": "Letter Type", "title": "Title", "security_lvl": "Security",
            "urgency_lvl": "Urgency", "dept_from": "Dept From", "owner_department": "Department",
        }
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=100 if col != "title" else 200)

        self.tree.pack(fill="both", expand=True)
        self.load_all_data()

    def refresh_data(self):
        self.load_all_data()

    def _build_query(self):
        query = (
            "SELECT file_id, letter_date, send_date, letter_type, title, "
            "security_lvl, urgency_lvl, dept_from, owner_department FROM inletter WHERE 1=1"
        )
        params = []
        query, params = apply_department_sql(self.current_user, query, params)

        if self.ent_id.get().strip():
            query += " AND file_id = %s"
            params.append(self.ent_id.get().strip())
        if self.ent_type.get().strip():
            query += " AND letter_type LIKE %s"
            params.append(f"%{self.ent_type.get().strip()}%")
        if self.ent_title.get().strip():
            query += " AND title LIKE %s"
            params.append(f"%{self.ent_title.get().strip()}%")
        return query, params

    def load_all_data(self):
        self.tree.delete(*self.tree.get_children())
        conn = get_db_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            query, params = self._build_query()
            query += " ORDER BY file_id DESC"
            cursor.execute(query, params)
            for row in cursor.fetchall():
                self.tree.insert("", "end", values=row)
        except Exception as e:
            messagebox.showerror("Database Error", str(e))
        finally:
            conn.close()

    def search_data(self):
        self.load_all_data()

    def reset_filters(self):
        self.ent_id.delete(0, tk.END)
        self.ent_type.delete(0, tk.END)
        self.ent_title.delete(0, tk.END)
        self.load_all_data()

    def export_to_csv(self):
        if not self.tree.get_children():
            messagebox.showwarning("No Data", "ထုတ်ယူရန် အချက်အလက်မရှိပါ။")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if not file_path:
            return
        try:
            with open(file_path, mode="w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file)
                writer.writerow(
                    ["File ID", "Letter Date", "Send Date", "Letter Type", "Title",
                     "Security", "Urgency", "Dept From", "Department"]
                )
                for row_id in self.tree.get_children():
                    writer.writerow(self.tree.item(row_id)["values"])
            messagebox.showinfo("Success", "CSV exported successfully.")
        except Exception as e:
            messagebox.showerror("Export Error", str(e))
