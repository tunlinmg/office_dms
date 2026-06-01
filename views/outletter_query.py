# views/outletter_query.py
import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from config import get_db_connection
from models.user_model import apply_department_sql

class OutLetterQuery(ttk.Frame):
    """ထွက်စာများကို ရှာဖွေရန်နှင့် UI Grid ဖြင့် စနစ်တကျ ပြသရန် View Frame"""
    
    def __init__(self, parent, current_user):
        super().__init__(parent)
        self.current_user = current_user
        self._build_ui()
        self.refresh_data()  # စာမျက်နှာစဖွင့်ချိန်တွင် ဒေတာများကို အလိုအလျောက် ဆွဲတင်ရန်

    def _build_ui(self):
        """ရှာဖွေရေး Filter များနှင့် ဇယား (Treeview) UI တည်ဆောက်ခြင်း"""
        # Outer scrollable container for page content
        canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        vscrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vscrollbar.set)

        vscrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        content_frame = ttk.Frame(canvas)
        content_window = canvas.create_window((0, 0), window=content_frame, anchor="nw")

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def on_canvas_configure(event):
            canvas.itemconfig(content_window, width=event.width)

        content_frame.bind("<Configure>", on_frame_configure)
        canvas.bind("<Configure>", on_canvas_configure)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Top Search Filter Panel
        filter_frame = ttk.LabelFrame(content_frame, text=" ထွက်စာ ရှာဖွေခြင်း Filter ", padding=12)
        filter_frame.pack(side="top", fill="x", padx=10, pady=10)

        # File ID Filter
        ttk.Label(filter_frame, text="စာ ID:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.ent_file_id = ttk.Entry(filter_frame, width=12)
        self.ent_file_id.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Doc Type / Letter Type Filter
        ttk.Label(filter_frame, text="စာအမျိုးအစား:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.ent_doc_type = ttk.Entry(filter_frame, width=15)
        self.ent_doc_type.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        # Date From Filter (YYYY-MM-DD)
        ttk.Label(filter_frame, text="မှ (ရက်စွဲ):").grid(row=0, column=4, padx=5, pady=5, sticky="w")
        self.ent_date_from = ttk.Entry(filter_frame, width=12)
        self.ent_date_from.grid(row=0, column=5, padx=5, pady=5, sticky="w")
        
        # Date To Filter (YYYY-MM-DD)
        ttk.Label(filter_frame, text="ထိ (ရက်စွဲ):").grid(row=0, column=6, padx=5, pady=5, sticky="w")
        self.ent_date_to = ttk.Entry(filter_frame, width=12)
        self.ent_date_to.grid(row=0, column=7, padx=5, pady=5, sticky="w")

        # Action Buttons
        btn_search = ttk.Button(filter_frame, text="ရှာဖွေရန်", command=self.refresh_data)
        btn_search.grid(row=0, column=8, padx=10, pady=5)
        
        btn_clear = ttk.Button(filter_frame, text="Reset", command=self._clear_filters)
        btn_clear.grid(row=0, column=9, padx=5, pady=5)

        # Table Display Area (Treeview with Scrollbars)
        table_frame = ttk.Frame(content_frame)
        table_frame.pack(side="top", fill="both", expand=True, padx=10, pady=5)

        # မှတ်ချက် - `send_date` ကို ဖယ်ရှားလိုက်ပါသည်
        columns = ("file_id", "letter_date", "letter_type", "title", "dept_to", "owner_dept")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        
        # Heading Definitions
        self.tree.heading("file_id", text="စာ ID")
        self.tree.heading("letter_date", text="စာပါရက်စွဲ")
        self.tree.heading("letter_type", text="စာအမျိုးအစား")
        self.tree.heading("title", text="အကြောင်းအရာ")
        self.tree.heading("dept_to", text="လိပ်မူ/မိတ္တူဌာန")
        self.tree.heading("owner_dept", text="တာဝန်ခံဌာန")

        # Column Width Settings
        self.tree.column("file_id", width=70, anchor="center")
        self.tree.column("letter_date", width=100, anchor="center")
        self.tree.column("letter_type", width=120, anchor="w")
        self.tree.column("title", width=280, anchor="w")
        self.tree.column("dept_to", width=150, anchor="w")
        self.tree.column("owner_dept", width=130, anchor="w")

        # Scrollbars Integration
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

    def _clear_filters(self):
        """ရှာဖွေရေး Entry Box များအားလုံးကို ရှင်းလင်းခြင်း"""
        self.ent_file_id.delete(0, tk.END)
        self.ent_doc_type.delete(0, tk.END)
        self.ent_date_from.delete(0, tk.END)
        self.ent_date_to.delete(0, tk.END)
        self.refresh_data()

    def build_outletter_query(self, file_id=None, date_from=None, date_to=None, doc_type=None):
        """Database Query စာသားအား လက်ရှိအသုံးပြုသူ၏ Permission အလိုက် စစ်ထုတ်တည်ဆောက်ခြင်း"""
        # မှတ်ချက် - SQL Statement ထဲမှ `send_date` အား ဖယ်ရှားလိုက်ပါသည်
        query = (
            "SELECT file_id, letter_date, letter_type, title, dept_to, owner_department "
            "FROM outletter WHERE 1=1"
        )
        params = []
        # လက်ရှိ User ရဲ့ ဝင်ရောက်ခွင့်ဌာနအလိုက် SQL ကို စစ်ထုတ်ပေးခြင်း
        query, params = apply_department_sql(self.current_user, query, params, column="dept_to")

        if file_id:
            query += " AND file_id = %s"
            params.append(file_id)
        if doc_type:
            query += " AND letter_type LIKE %s"
            params.append(f"%{doc_type}%")
        if date_from:
            query += " AND letter_date >= %s"
            params.append(date_from)
        if date_to:
            query += " AND letter_date <= %s"
            params.append(date_to)
            
        return query, params

    def refresh_data(self):
        """Database ထဲမှ ထွက်စာအချက်အလက်များကို ဆွဲထုတ်ပြီး Treeview ဇယားထဲသို့ ဖြည့်သွင်းခြင်း"""
        # ဇယားဟောင်းထဲမှ ဒေတာများကို အရင်ဖျက်ထုတ်ခြင်း
        for row in self.tree.get_children():
            self.tree.delete(row)

        conn = get_db_connection()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            
            # Entry များမှ တန်ဖိုးများကို ရယူခြင်း
            f_id = self.ent_file_id.get().strip()
            d_type = self.ent_doc_type.get().strip()
            d_from = self.ent_date_from.get().strip()
            d_to = self.ent_date_to.get().strip()

            query, params = self.build_outletter_query(
                file_id=f_id if f_id else None,
                doc_type=d_type if d_type else None,
                date_from=d_from if d_from else None,
                date_to=d_to if d_to else None
            )
            query += " ORDER BY file_id DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()

            # ဇယားထဲသို့ ဒေတာအသစ်များ တစ်တန်းချင်းထည့်သွင်းခြင်း
            for r in rows:
                self.tree.insert("", "end", values=r)

        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", f"ထွက်စာများ ရှာဖွေရယူခြင်း မအောင်မြင်ပါ-\n{str(e)}")
        finally:
            conn.close()