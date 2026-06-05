# views/inletter_query.py
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
        filter_frame = ttk.LabelFrame(self.content_frame, text=" ဝင်စာ ရှာဖွေခြင်း Filter ", padding=12)
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
        btn_search.grid(row=1, column=4, padx=10, pady=5, sticky="e")
        
        btn_clear = ttk.Button(filter_frame, text="Reset", command=self._clear_filters)
        btn_clear.grid(row=1, column=5, padx=5, pady=5, sticky="e")

        # Charts Toggle Button
        btn_charts = ttk.Button(filter_frame, text="📊 ဂရဖ်များ", command=self._toggle_charts)
        btn_charts.grid(row=1, column=6, padx=5, pady=5, sticky="e")

        # ===== Table Display Area (Treeview) =====
        table_frame = ttk.LabelFrame(self.content_frame, text=" ဝင်စာ ဇယား ", padding=5)
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

        # Scrollbars for treeview only (horizontal)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        hsb.grid(row=1, column=0, sticky="ew")

        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        # ===== Charts Panel (initially hidden) =====
        self.charts_visible = False
        self.charts_frame = ttk.LabelFrame(self.content_frame, text=" ဝင်စာ စာရင်းအင်းဂရပ်များ ", padding=10)

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
            query, params = self.build_inletter_query()
            cursor.execute(query, params)
            rows = cursor.fetchall()

            if not rows:
                ttk.Label(self.charts_frame, text="ဒေတာမရှိပါ").pack(pady=20)
                return

            # Extract data for charts
            letter_types = [row[3] for row in rows if row[3]]  # letter_type
            security_lvls = [row[5] for row in rows if row[5]]  # security_lvl
            urgency_lvls = [row[6] for row in rows if row[6]]  # urgency_lvl
            depts_from = [row[7] for row in rows if row[7]]     # dept_from
            owner_depts = [row[8] for row in rows if row[8]]    # owner_dept

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
                    "#4CAF50"
                )

            # Chart 2: Security Level Distribution (Pie Chart)
            if security_lvls:
                chart2_frame = ttk.Frame(charts_container)
                chart2_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
                self._create_pie_chart(
                    chart2_frame,
                    "လုံခြုံမှုအဆင့်",
                    security_lvls,
                    ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7"]
                )

            # Chart 3: Urgency Level Distribution (Pie Chart)
            if urgency_lvls:
                chart3_frame = ttk.Frame(charts_container)
                chart3_frame.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")
                self._create_pie_chart(
                    chart3_frame,
                    "အရေးကြီးမှုအဆင့်",
                    urgency_lvls,
                    ["#E74C3C", "#F39C12", "#27AE60", "#3498DB", "#9B59B6"]
                )

            # Chart 4: Department From Distribution (Horizontal Bar Chart)
            if depts_from:
                chart4_frame = ttk.Frame(charts_container)
                chart4_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
                self._create_horizontal_bar_chart(
                    chart4_frame,
                    "ပေးပို့သည့်ဌာန",
                    depts_from,
                    "ဌာန",
                    "အရေအတွက်",
                    "#2196F3"
                )

            # Chart 5: Owner Department Distribution (Horizontal Bar Chart)
            if owner_depts:
                chart5_frame = ttk.Frame(charts_container)
                chart5_frame.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
                self._create_horizontal_bar_chart(
                    chart5_frame,
                    "တာဝန်ခံဌာန",
                    owner_depts,
                    "ဌာန",
                    "အရေအတွက်",
                    "#FF9800"
                )

            # Configure grid weights
            charts_container.grid_columnconfigure(0, weight=1)
            charts_container.grid_columnconfigure(1, weight=1)
            charts_container.grid_columnconfigure(2, weight=1)

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

    def _create_pie_chart(self, parent, title, data, colors):
        """Pie Chart ဖန်တီးခြင်း"""
        frame = ttk.LabelFrame(parent, text=f" {title} ", padding=5)
        frame.pack(fill="both", expand=True)

        fig = Figure(figsize=(4, 3), dpi=80)
        ax = fig.add_subplot(111)

        counter = Counter(data)
        labels = list(counter.keys())
        values = list(counter.values())

        # Use provided colors, cycle if needed
        chart_colors = [colors[i % len(colors)] for i in range(len(labels))]

        wedges, texts, autotexts = ax.pie(
            values, labels=labels, autopct='%1.1f%%',
            colors=chart_colors, startangle=90,
            textprops={'fontsize': 7}
        )

        for autotext in autotexts:
            autotext.set_fontweight('bold')
            autotext.set_fontsize(6)

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

            # Refresh charts if visible
            if self.charts_visible:
                self._refresh_charts()

        except mysql.connector.Error as e:
            messagebox.showerror("Database Error", f"အချက်အလက်ရှာဖွေရယူခြင်း မအောင်မြင်ပါ-\n{str(e)}")
        finally:
            conn.close()