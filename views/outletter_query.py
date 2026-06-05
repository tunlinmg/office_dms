# views/outletter_query.py
import tkinter as tk
from tkinter import ttk, messagebox
import mysql.connector
from config import get_db_connection
from models.user_model import apply_department_sql

# matplotlib imports for charts
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import Counter

class OutLetterQuery(ttk.Frame):
    """ထွက်စာများကို ရှာဖွေရန်နှင့် UI Grid ဖြင့် စနစ်တကျ ပြသရန် View Frame"""
    
    def __init__(self, parent, current_user):
        super().__init__(parent)
        self.current_user = current_user
        self._build_ui()
        self.refresh_data()  # စာမျက်နှာစဖွင့်ချိန်တွင် ဒေတာများကို အလိုအလျောက် ဆွဲတင်ရန်

    def _build_ui(self):
        """ရှာဖွေရေး Filter များနှင့် ဇယား (Treeview) UI တည်ဆောက်ခြင်း"""
        # Create main scrollable container with single scrollbar
        self.main_canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self.vscrollbar = ttk.Scrollbar(self, orient="vertical", command=self.main_canvas.yview)
        self.main_canvas.configure(yscrollcommand=self.vscrollbar.set)

        self.vscrollbar.pack(side="right", fill="y")
        self.main_canvas.pack(side="left", fill="both", expand=True)

        # Create content frame inside canvas
        self.content_frame = ttk.Frame(self.main_canvas)
        self.content_window = self.main_canvas.create_window((0, 0), window=self.content_frame, anchor="nw")

        # Configure canvas scrolling
        def on_frame_configure(event):
            self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))

        def on_canvas_configure(event):
            self.main_canvas.itemconfig(self.content_window, width=event.width)

        self.content_frame.bind("<Configure>", on_frame_configure)
        self.main_canvas.bind("<Configure>", on_canvas_configure)

        # Mouse wheel scrolling
        def _on_mousewheel(event):
            self.main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self.main_canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # ===== Top Search Filter Panel =====
        filter_frame = ttk.LabelFrame(self.content_frame, text=" ထွက်စာ ရှာဖွေခြင်း Filter ", padding=12)
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
        btn_search.grid(row=1, column=5, padx=10, pady=5)
        
        btn_clear = ttk.Button(filter_frame, text="Reset", command=self._clear_filters)
        btn_clear.grid(row=1, column=6, padx=5, pady=5)

        # Charts Toggle Button
        btn_charts = ttk.Button(filter_frame, text="📊 ဂရဖ်များ", command=self._toggle_charts)
        btn_charts.grid(row=1, column=7, padx=5, pady=5)

        # ===== Table Display Area (Treeview with Scrollbars) =====
        table_frame = ttk.LabelFrame(self.content_frame, text=" ထွက်စာ ဇယား ", padding=5)
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

        # Scrollbars Integration (horizontal only for treeview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        hsb.grid(row=1, column=0, sticky="ew")

        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        # ===== Charts Panel (initially hidden) =====
        self.charts_visible = False
        self.charts_frame = ttk.LabelFrame(self.content_frame, text=" ထွက်စာ စာရင်းအင်းဂရပ်များ ", padding=10)

        # Store chart canvas references for cleanup
        self._chart_canvases = []

    def _toggle_charts(self):
        """ဂရဖ်များကို ပြသခြင်း/ဖျောက်ထားခြင်း"""
        if self.charts_visible:
            # Hide charts
            self.charts_frame.pack_forget()
            self.charts_visible = False
        else:
            # Show charts
            self._build_charts_panel()
            self.charts_frame.pack(side="top", fill="x", padx=10, pady=5)
            self.charts_visible = True
            self._refresh_charts()

    def _build_charts_panel(self):
        """ဂရဖ်များပြသရန် Panel တည်ဆောက်ခြင်း"""
        # Clear existing charts
        for widget in self.charts_frame.winfo_children():
            widget.destroy()
        self._chart_canvases.clear()

    def _refresh_charts(self):
        """ဂရဖ်များကို ဒေတာနှင့်အတူ ပြန်လည်တည်ဆောက်ခြင်း"""
        # Clear existing charts
        for widget in self.charts_frame.winfo_children():
            widget.destroy()
        self._chart_canvases.clear()

        # Get data for charts from database
        conn = get_db_connection()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            query, params = self.build_outletter_query()
            cursor.execute(query, params)
            rows = cursor.fetchall()

            if not rows:
                ttk.Label(self.charts_frame, text="ဒေတာမရှိပါ").pack(pady=20)
                return

            # Extract data for charts
            letter_types = [row[2] for row in rows if row[2]]  # letter_type
            depts_to = [row[4] for row in rows if row[4]]      # dept_to
            owner_depts = [row[5] for row in rows if row[5]]   # owner_dept

            # Create a frame for charts grid
            charts_container = ttk.Frame(self.charts_frame)
            charts_container.pack(fill="x", expand=True)

            # Chart 1: Letter Type Distribution (Bar Chart)
            if letter_types:
                chart1_frame = ttk.Frame(charts_container)
                chart1_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
                self._create_bar_chart(
                    chart1_frame,
                    "စာအမျိုးအစား ဖြန့်ကျက်မှု",
                    letter_types,
                    "စာအမျိုးအစား",
                    "အရေအတွက်",
                    "#9C27B0"
                )

            # Chart 2: Department To Distribution (Horizontal Bar Chart)
            if depts_to:
                chart2_frame = ttk.Frame(charts_container)
                chart2_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
                self._create_horizontal_bar_chart(
                    chart2_frame,
                    "လိပ်မူ/မိတ္တူဌာန",
                    depts_to,
                    "ဌာန",
                    "အရေအတွက်",
                    "#00BCD4"
                )

            # Chart 3: Owner Department Distribution (Horizontal Bar Chart)
            if owner_depts:
                chart3_frame = ttk.Frame(charts_container)
                chart3_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
                self._create_horizontal_bar_chart(
                    chart3_frame,
                    "တာဝန်ခံဌာန",
                    owner_depts,
                    "ဌာန",
                    "အရေအတွက်",
                    "#FF5722"
                )

            # Chart 4: Monthly Distribution (if date data available)
            letter_dates = [row[1] for row in rows if row[1]]
            if letter_dates:
                chart4_frame = ttk.Frame(charts_container)
                chart4_frame.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
                self._create_monthly_chart(
                    chart4_frame,
                    "လအလိုက် ထွက်စာ",
                    letter_dates
                )

            # Configure grid weights
            charts_container.grid_columnconfigure(0, weight=1)
            charts_container.grid_columnconfigure(1, weight=1)

        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", f"ဂရဖ်ဒေတာရယူခြင်း မအောင်မြင်ပါ-\n{str(e)}")
        finally:
            conn.close()

    def _create_bar_chart(self, parent, title, data, xlabel, ylabel, color):
        """Bar Chart ဖန်တီးခြင်း"""
        frame = ttk.LabelFrame(parent, text=f" {title} ", padding=5)
        frame.pack(fill="both", expand=True)

        fig = Figure(figsize=(4, 3), dpi=80)
        ax = fig.add_subplot(111)

        counter = Counter(data)
        labels = list(counter.keys())
        values = list(counter.values())

        bars = ax.bar(labels, values, color=color, alpha=0.8, edgecolor='white', linewidth=0.5)
        
        ax.set_xlabel(xlabel, fontsize=8)
        ax.set_ylabel(ylabel, fontsize=8)
        ax.tick_params(axis='x', rotation=45, labelsize=7)
        ax.tick_params(axis='y', labelsize=7)

        # Add value labels on bars
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                    str(val), ha='center', va='bottom', fontsize=7, fontweight='bold')

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self._chart_canvases.append(canvas)

    def _create_horizontal_bar_chart(self, parent, title, data, ylabel, xlabel, color):
        """Horizontal Bar Chart ဖန်တီးခြင်း"""
        frame = ttk.LabelFrame(parent, text=f" {title} ", padding=5)
        frame.pack(fill="both", expand=True)

        fig = Figure(figsize=(4, max(2.5, len(set(data)) * 0.4)), dpi=80)
        ax = fig.add_subplot(111)

        counter = Counter(data)
        # Sort by value descending
        sorted_items = sorted(counter.items(), key=lambda x: x[1], reverse=True)
        labels = [item[0] for item in sorted_items]
        values = [item[1] for item in sorted_items]

        y_pos = range(len(labels))
        bars = ax.barh(y_pos, values, color=color, alpha=0.8, edgecolor='white', linewidth=0.5)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=7)
        ax.set_xlabel(xlabel, fontsize=8)
        ax.tick_params(axis='x', labelsize=7)

        # Add value labels on bars
        for bar, val in zip(bars, values):
            ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                    str(val), ha='left', va='center', fontsize=7, fontweight='bold')

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self._chart_canvases.append(canvas)

    def _create_monthly_chart(self, parent, title, dates):
        """လအလိုက် ဖြန့်ကျက်မှု Chart ဖန်တီးခြင်း"""
        frame = ttk.LabelFrame(parent, text=f" {title} ", padding=5)
        frame.pack(fill="both", expand=True)

        fig = Figure(figsize=(4, 3), dpi=80)
        ax = fig.add_subplot(111)

        # Extract year-month from dates
        monthly_data = []
        for d in dates:
            if hasattr(d, 'strftime'):
                monthly_data.append(d.strftime('%Y-%m'))
            elif isinstance(d, str):
                monthly_data.append(d[:7] if len(d) >= 7 else d)
            else:
                monthly_data.append(str(d)[:7])

        counter = Counter(monthly_data)
        # Sort by month
        sorted_items = sorted(counter.items(), key=lambda x: x[0])
        labels = [item[0] for item in sorted_items]
        values = [item[1] for item in sorted_items]

        ax.plot(labels, values, marker='o', color='#E91E63', linewidth=2, markersize=6)
        ax.fill_between(labels, values, alpha=0.3, color='#E91E63')

        ax.set_xlabel("လ", fontsize=8)
        ax.set_ylabel("အရေအတွက်", fontsize=8)
        ax.tick_params(axis='x', rotation=45, labelsize=7)
        ax.tick_params(axis='y', labelsize=7)

        # Add value labels on points
        for i, (label, val) in enumerate(zip(labels, values)):
            ax.annotate(str(val), (i, val), textcoords="offset points",
                       xytext=(0, 10), ha='center', fontsize=7, fontweight='bold')

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self._chart_canvases.append(canvas)

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

            # Refresh charts if visible
            if self.charts_visible:
                self._refresh_charts()

        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", f"ထွက်စာများ ရှာဖွေရယူခြင်း မအောင်မြင်ပါ-\n{str(e)}")
        finally:
            conn.close()