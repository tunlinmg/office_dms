# views/outletter_query.py
import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from config import get_db_connection
from models.user_model import apply_department_sql
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import Counter
import matplotlib.font_manager as fm

class OutLetterQuery(ttk.Frame):
    """ထွက်စာများကို ရှာဖွေရန်နှင့် UI Grid ဖြင့် စနစ်တကျ ပြသရန် View Frame"""
    
    def __init__(self, parent, current_user):
        super().__init__(parent)
        self.current_user = current_user
        self._build_ui()
        self.refresh_data()  # စာမျက်နှာစဖွင့်ချိန်တွင် ဒေတာများကို အလိုအလျောက် ဆွဲတင်ရန်

    def _build_ui(self):
        """ရှာဖွေရေး Filter များနှင့် ဇယား (Treeview) UI တည်ဆောက်ခြင်း"""
        # Top Search Filter Panel
        filter_frame = ttk.LabelFrame(self, text=" ထွက်စာ ရှာဖွေခြင်း Filter ", padding=12)
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
        table_frame = ttk.Frame(self)
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

        # Scale Bar (Up/Down)
        scale_frame = ttk.Frame(self)
        scale_frame.pack(side="bottom", fill="x", padx=10, pady=(0, 5))
        
        ttk.Label(scale_frame, text="အတိုးအလွှာ:").pack(side="left", padx=(0, 5))
        self.scale_var = tk.IntVar(value=100)
        self.scale_bar = ttk.Scale(scale_frame, from_=50, to=200, orient="horizontal", variable=self.scale_var, command=self._on_scale_change)
        self.scale_bar.pack(side="left", fill="x", expand=True, padx=5)
        self.scale_label = ttk.Label(scale_frame, text="100%")
        self.scale_label.pack(side="left", padx=(5, 0))
        
        # Up/Down Buttons
        btn_up = ttk.Button(scale_frame, text="▲ Up", command=self._scale_up)
        btn_up.pack(side="left", padx=(10, 2))
        btn_down = ttk.Button(scale_frame, text="▼ Down", command=self._scale_down)
        btn_down.pack(side="left", padx=2)

        # Graph Frame
        self.graph_frame = ttk.LabelFrame(self, text=" စာအမျိုးအစား ဇယား ", padding=10)
        self.graph_frame.pack(side="bottom", fill="x", padx=10, pady=5)

        # Action Buttons Frame
        action_frame = ttk.LabelFrame(self, text=" Actions ", padding=10)
        action_frame.pack(side="bottom", fill="x", padx=10, pady=10)

        btn_view = ttk.Button(action_frame, text="👁 View", command=self.action_view)
        btn_view.pack(side="left", padx=10)

        btn_edit = ttk.Button(action_frame, text="✏ Edit", command=self.action_edit)
        btn_edit.pack(side="left", padx=10)

        btn_delete = ttk.Button(action_frame, text="❌ Delete", command=self.action_delete)
        btn_delete.pack(side="left", padx=10)

    def _clear_filters(self):
        """ရှာဖွေရေး Entry Box များအားလုံးကို ရှင်းလင်းခြင်း"""
        self.ent_file_id.delete(0, tk.END)
        self.ent_doc_type.delete(0, tk.END)
        self.ent_date_from.delete(0, tk.END)
        self.ent_date_to.delete(0, tk.END)
        self.refresh_data()

    def get_selected_file_id(self):
        """Treeview မှ ရွေးချယ်ထားသော အတန်း၏ file_id ကို ပြန်ပေးခြင်း"""
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Warning", "ကျေးဇူးပြု၍ ဇယားထဲမှ အတန်းတစ်ခုကို ရွေးချယ်ပါ။")
            return None
        item_values = self.tree.item(selected_item, "values")
        return item_values[0] if item_values else None

    def action_view(self):
        """ရွေးချယ်ထားသော စာရင်းအချက်အလက်ကို ကြည့်ရှုရန်"""
        file_id = self.get_selected_file_id()
        if file_id:
            messagebox.showinfo("View Action", f"Viewing record with ID: {file_id}")

    def action_edit(self):
        """ရွေးချယ်ထားသော စာရင်းအချက်အလက်ကို ပြင်ဆင်ရန်"""
        file_id = self.get_selected_file_id()
        if file_id:
            messagebox.showinfo("Edit Action", f"Editing record with ID: {file_id}")

    def action_delete(self):
        """ရွေးချယ်ထားသော စာရင်းအချက်အလက်ကို ဖျက်သိမ်းရန်"""
        file_id = self.get_selected_file_id()
        if file_id:
            if messagebox.askyesno("Delete Action", f"Are you sure you want to delete record {file_id}?"):
                messagebox.showinfo("Delete Action", f"Deleting record with ID: {file_id}")

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
        
        self.draw_graph()

    def draw_graph(self):

        """Treeview ထဲမှ ဒေတာများဖြင့် စာအမျိုးအစား ဇယား ဆွဲခြင်း"""
        # ရှိပြီးသား widget များကို ဖျက်ခြင်း
        for widget in self.graph_frame.winfo_children():
            widget.destroy()

        # Treeview ထဲမှ ဒေတာများကို ရယူခြင်း
        items = self.tree.get_children()
        if not items:
            ttk.Label(self.graph_frame, text="No data for graph").pack()
            return

        letter_types = [self.tree.item(item, "values")[2] for item in items]
        counts = Counter(letter_types)

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(counts.keys(), counts.values())
        ax.set_title("စာအမျိုးအစား ဇယား")
        ax.set_xlabel("စာအမျိုးအစား")
        ax.set_ylabel("အရေအတွက်")
        
        # X-axis label များကို လှည့်ခြင်း
        plt.xticks(rotation=45, ha='right')
        plt.yticks()
        
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _on_scale_change(self, value):
        """Scale bar ပြောင်းလဲသည့်အခါ ချိန်ညှိခြင်း"""
        scale = int(float(value))
        self.scale_label.config(text=f"{scale}%")
        self._apply_scale(scale)

    def _scale_up(self):
        """Scale တိုးခြင်း"""
        current = self.scale_var.get()
        if current < 200:
            new_val = min(current + 10, 200)
            self.scale_var.set(new_val)
            self._on_scale_change(new_val)

    def _scale_down(self):
        """Scale လျှော့ခြင်း"""
        current = self.scale_var.get()
        if current > 50:
            new_val = max(current - 10, 50)
            self.scale_var.set(new_val)
            self._on_scale_change(new_val)

    def _apply_scale(self, scale):
        """Treeview စာလုံးအရွယ်အစားကို ချိန်ညှိခြင်း"""
        base_size = 9
        new_size = int(base_size * scale / 100)
        style = ttk.Style()
        style.configure("Treeview", font=("Pyidaungsu", new_size))
        style.configure("Treeview.Heading", font=("Pyidaungsu", new_size, "bold"))
