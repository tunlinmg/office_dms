# views/inletter_query.py
import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from config import get_db_connection
from models.user_model import apply_department_sql

# 1. Dashboard က လှမ်းခေါ်မည့် Class နာမည်ကို တိကျစွာ သတ်မှတ်ခြင်း
class InLetterQuery(ttk.Frame):
    """ဝင်စာများကို ရှာဖွေရန်နှင့် UI Grid ဖြင့် ပြသရန် View Frame"""
    
    def __init__(self, parent, current_user):
        super().__init__(parent)
        self.current_user = current_user
        self._build_ui()
        self.refresh_data()  # စဖွင့်ချင်း ဒေတာအလိုအလျောက် ဆွဲတင်ရန်

    def _build_ui(self):
        """ရှာဖွေရေး Entry များနှင့် ဒေတာပြသရန် Treeview UI တည်ဆောက်ခြင်း"""
        # Top Search Filter Panel
        filter_frame = ttk.LabelFrame(self, text=" ဝင်စာ ရှာဖွေခြင်း Filter ", padding=12)
        filter_frame.pack(side="top", fill="x", padx=10, pady=10)

        # File ID Filter
        ttk.Label(filter_frame, text="စာ ID:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.ent_file_id = ttk.Entry(filter_frame, width=15)
        self.ent_file_id.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Letter Type Filter
        ttk.Label(filter_frame, text="စာအမျိုးအစား:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.ent_type = ttk.Entry(filter_frame, width=20)
        self.ent_type.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        # Title Filter
        ttk.Label(filter_frame, text="အကြောင်းအရာ:").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.ent_title = ttk.Entry(filter_frame, width=25)
        self.ent_title.grid(row=0, column=5, padx=5, pady=5, sticky="w")

        # Buttons
        btn_search = ttk.Button(filter_frame, text="ရှာဖွေရန်", command=self.refresh_data)
        btn_search.grid(row=0, column=6, padx=10, pady=5)
        
        btn_clear = ttk.Button(filter_frame, text="Reset", command=self._clear_filters)
        btn_clear.grid(row=0, column=7, padx=5, pady=5)

        # Table Display Area (Treeview)
        table_frame = ttk.Frame(self)
        table_frame.pack(side="top", fill="both", expand=True, padx=10, pady=5)

        columns = ("file_id", "letter_date", "send_date", "letter_type", "title", "security_lvl", "urgency_lvl", "dept_from", "owner_dept")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        
        # Heading Definitions
        self.tree.heading("file_id", text="စာ ID")
        self.tree.heading("letter_date", text="စာပါရက်စွဲ")
        self.tree.heading("send_date", text="ပေးပို့ရက်စွဲ")
        self.tree.heading("letter_type", text="စာအမျိုးအစား")
        self.tree.heading("title", text="အကြောင်းအရာ")
        self.tree.heading("security_lvl", text="လုံခြုံမှုအဆင့်")
        self.tree.heading("urgency_lvl", text="အရေးကြီးမှုအဆင့်")
        self.tree.heading("dept_from", text="ပေးပို့သည့်ဌာန")
        self.tree.heading("owner_dept", text="တာဝန်ခံဌာန")

        # Column Widths
        self.tree.column("file_id", width=60, anchor="center")
        self.tree.column("letter_date", width=90, anchor="center")
        self.tree.column("send_date", width=90, anchor="center")
        self.tree.column("letter_type", width=100, anchor="w")
        self.tree.column("title", width=250, anchor="w")
        self.tree.column("security_lvl", width=90, anchor="center")
        self.tree.column("urgency_lvl", width=90, anchor="center")
        self.tree.column("dept_from", width=120, anchor="w")
        self.tree.column("owner_dept", width=120, anchor="w")

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

    def _clear_filters(self):
        """ရှာဖွေရေး အကွက်များကို ရှင်းလင်းခြင်း"""
        self.ent_file_id.delete(0, tk.END)
        self.ent_type.delete(0, tk.END)
        self.ent_title.delete(0, tk.END)
        self.refresh_data()

    def build_inletter_query(self, file_id=None, letter_type=None, title=None):
        """Database Query စာသားအား သုံးစွဲသူ Permission အလိုက် တည်ဆောက်ခြင်း"""
        query = (
            "SELECT file_id, letter_date, send_date, letter_type, title, "
            "security_lvl, urgency_lvl, dept_from, owner_department FROM inletter WHERE 1=1"
        )
        params = []
        # သုံးစွဲသူရဲ့ ဌာနအလိုက် SQL ဝင်ခွင့်ကို စစ်ထုတ်ပေးခြင်း
        query, params = apply_department_sql(self.current_user, query, params)

        if file_id:
            query += " AND file_id = %s"
            params.append(file_id)
        if letter_type:
            query += " AND letter_type LIKE %s"
            params.append(f"%{letter_type}%")
        if title:
            query += " AND title LIKE %s"
            params.append(f"%{title}%")
            
        return query, params

    def refresh_data(self):
        """Database ထဲမှ အချက်အလက်များကို ဆွဲထုတ်၍ Treeview ဇယားထဲသို့ ထည့်သွင်းခြင်း"""
        # Treeview ကို အရင်ရှင်းထုတ်ခြင်း
        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = get_db_connection()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            
            # UI Entry များမှ Filter တန်ဖိုးများကို ယူခြင်း
            f_id = self.ent_file_id.get().strip()
            l_type = self.ent_type.get().strip()
            ttl = self.ent_title.get().strip()

            query, params = self.build_inletter_query(file_id=f_id if f_id else None, 
                                                      letter_type=l_type if l_type else None, 
                                                      title=ttl if ttl else None)
            query += " ORDER BY file_id DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()

            for r in rows:
                self.tree.insert("", "end", values=r)

        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", f"အချက်အလက်ရှာဖွေရယူခြင်း မအောင်မြင်ပါ-\n{str(e)}")
        finally:
            conn.close()