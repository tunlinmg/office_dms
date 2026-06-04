# views/outletter_view.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkcalendar import DateEntry

from models.doctype_model import fetch_all_doctypes
from models.outletter_model import insert_outletter, fetch_outletters
from models.dept_model import fetch_department_names
from models.user_model import is_admin, get_user_department


class OutletterView(ttk.Frame):
    def __init__(self, parent, current_user=None):
        super().__init__(parent)
        self.current_user = current_user or {}
        self.attach_path = ""
        self.setup_ui()
        self.load_records()

    def setup_ui(self):
        dept_names = fetch_department_names() or ["General Office"]
        user_dept = get_user_department(self.current_user)
        admin = is_admin(self.current_user)

        # Main container with a single scrollbar
        main_canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        main_scrollbar = ttk.Scrollbar(self, orient="vertical", command=main_canvas.yview)
        main_canvas.configure(yscrollcommand=main_scrollbar.set)

        main_scrollbar.pack(side="right", fill="y")
        main_canvas.pack(side="left", fill="both", expand=True)

        # Frame inside canvas to hold all content
        content_frame = ttk.Frame(main_canvas)
        window_id = main_canvas.create_window((0, 0), window=content_frame, anchor="nw")

        def configure_canvas(event):
            main_canvas.configure(scrollregion=main_canvas.bbox("all"))
            main_canvas.itemconfig(window_id, width=event.width)

        content_frame.bind("<Configure>", configure_canvas)
        main_canvas.bind("<Configure>", configure_canvas)

        # Mouse wheel scrolling
        def _on_mousewheel(event):
            main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        main_canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # --- Form Section ---
        form_frame = ttk.LabelFrame(content_frame, text=" ထွက်စာစာရင်းသွင်းဖောင် (Out Letter Entry) ")
        form_frame.pack(fill="x", padx=15, pady=10)

        ttk.Label(form_frame, text="Letter Date:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.ent_date = DateEntry(form_frame, width=28, date_pattern="yyyy-mm-dd")
        self.ent_date.grid(row=0, column=1, padx=10, pady=5)

        # lettertype ကို doc_type table ကနေ combo box နဲ့ရွေးချယ်စေဖို့ ပြင်ဆင်ထားတာကို အမြန်ဆုံး ပြန်လည်တင်ပြပါမယ်။ ဒီလိုလုပ်ရတဲ့အကြောင်းကတော့ စာရွက်စာတမ်းအမျိုးအစားတွေကို အလွယ်တကူ ထပ်ထည့်နိုင်ဖို့နဲ့ အမျိုးအစားအသစ်တွေကို အလွယ်တကူ စီမံခန့်ခွဲနိုင်ဖို့ပါ။    
        ttk.Label(form_frame, text="Letter Type:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.ent_type = ttk.Combobox(form_frame, values=[dt[1] for dt in fetch_all_doctypes()], width=28) 
        self.ent_type.grid(row=1, column=1, padx=10, pady=5)
        self.ent_type.set("none")   
        
        ttk.Label(form_frame, text="Title / အကြောင်းအရာ:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.ent_title = ttk.Entry(form_frame, width=50)
        self.ent_title.grid(row=2, column=1, padx=10, pady=5)

        ttk.Label(form_frame, text="ပေးပို့ဌာန လိပ်မူ/မိတ္တူ:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.cb_dept = ttk.Combobox(form_frame, values=["Ministry List", "Other"], width=28)
        self.cb_dept.grid(row=3, column=1, padx=10, pady=5)

        ttk.Label(form_frame, text="Owner Department:").grid(row=4, column=0, sticky="w", padx=10, pady=5)
        self.cb_owner_dept = ttk.Combobox(form_frame, values=dept_names, width=28)
        self.cb_owner_dept.grid(row=4, column=1, padx=10, pady=5)
        if admin:
            self.cb_owner_dept.set(dept_names[0] if dept_names else "")
        else:
            self.cb_owner_dept.set(user_dept)
            self.cb_owner_dept.config(state="readonly")

        ttk.Label(form_frame, text="လုံခြုံရေးအဆင့်အတန်း:").grid(row=5, column=0, sticky="w", padx=10, pady=5)
        self.cb_sec = ttk.Combobox(
            form_frame, values=["ရိုးရိုး", "ကန့်သတ်", "အတွင်းရေး", "လျှို့ဝှက်", "ထိပ်တန်းလျှို့ဝှက်"], width=28
        )
        self.cb_sec.grid(row=5, column=1, padx=10, pady=5)
        self.cb_sec.current(0)

        ttk.Label(form_frame, text="အရေးကြီးအဆင့်အတန်း:").grid(row=6, column=0, sticky="w", padx=10, pady=5)
        self.cb_urg = ttk.Combobox(form_frame, values=["ရိုးရိုး", "အရေးကြီး", "အမြန်", "ချက်ချင်း"], width=28)
        self.cb_urg.grid(row=6, column=1, padx=10, pady=5)
        self.cb_urg.current(0)

        ttk.Label(form_frame, text="ဖိုင်တွဲအမှတ်/Casefile:").grid(row=7, column=0, sticky="w", padx=10, pady=5)
        self.ent_case = ttk.Entry(form_frame, width=30)
        self.ent_case.grid(row=7, column=1, padx=10, pady=5)

        ttk.Label(form_frame, text="Attachment:").grid(row=8, column=0, sticky="w", padx=10, pady=5)
        ttk.Button(form_frame, text="Browse...", command=self.browse).grid(row=8, column=1, sticky="w", padx=10, pady=5)
        self.lbl_file = ttk.Label(form_frame, text="No file attached")
        self.lbl_file.grid(row=8, column=1, padx=120, pady=5)

        ttk.Label(form_frame, text="မှတ်ချက်:").grid(row=9, column=0, sticky="nw", padx=10, pady=5)
        self.txt_remark = tk.Text(form_frame, width=50, height=3)
        self.txt_remark.grid(row=9, column=1, padx=10, pady=5)

        ttk.Button(form_frame, text="Save Out Letter", command=self.save_data).grid(row=10, column=1, sticky="e", padx=10, pady=10)

        # --- Hint Label ---
        hint = "Admin: all departments  |  Staff: only your department's outletters"
        if not admin and user_dept:
            hint = f"Your department: {user_dept} — you only see outletters for this department."
        ttk.Label(content_frame, text=hint, font=("Segoe UI", 9), foreground="#475569").pack(anchor="w", padx=20)

        # --- List Section ---
        list_frame = ttk.LabelFrame(content_frame, text=" Outletters (department-filtered) ")
        list_frame.pack(fill="both", expand=True, padx=15, pady=10)

        cols = ("file_id", "letter_date", "title", "dept_to", "owner_department")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings", height=8)
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)
        for c, h in zip(cols, ["ID", "Date", "Title", "Dept To", "Department"]):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=120 if c != "title" else 200)

        # --- Footer Section ---
        footer_frame = ttk.Frame(content_frame)
        footer_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        # Separator line
        separator = ttk.Separator(footer_frame, orient="horizontal")
        separator.pack(fill="x", pady=(10, 5))
        
        # Footer content
        footer_inner = ttk.Frame(footer_frame)
        footer_inner.pack(fill="x")
        
        # Left side - Record count
        self.lbl_record_count = ttk.Label(footer_inner, text="Total Records: 0", font=("Segoe UI", 9))
        self.lbl_record_count.pack(side="left", padx=5)
        
        # Right side - System info
        footer_info = ttk.Label(
            footer_inner, 
            text="DMS - Document Management System | Outletter Module", 
            font=("Segoe UI", 9), 
            foreground="#64748b"
        )
        footer_info.pack(side="right", padx=5)

    def refresh_data(self):
        self.load_records()

    def load_records(self):
        self.tree.delete(*self.tree.get_children())
        records = fetch_outletters(self.current_user)
        for row in records:
            self.tree.insert("", "end", values=row)
        # Update footer record count
        self.lbl_record_count.config(text=f"Total Records: {len(records)}")

    def browse(self):
        fn = filedialog.askopenfilename()
        if fn:
            self.attach_path = fn
            self.lbl_file.config(text=fn.replace("\\", "/").split("/")[-1])

    def save_data(self):
        owner_dept = self.cb_owner_dept.get().strip()
        if not owner_dept:
            messagebox.showwarning("Validation", "Owner Department ထည့်ပါ။")
            return
        if not is_admin(self.current_user):
            owner_dept = get_user_department(self.current_user)
            if not owner_dept:
                messagebox.showwarning("Validation", "Your account has no department assigned.")
                return

        data = (
            self.ent_date.get(),
            self.ent_type.get(),
            self.ent_title.get(),
            self.cb_dept.get(),
            self.cb_sec.get(),
            self.cb_urg.get(),
            self.ent_case.get(),
            self.attach_path,
            self.txt_remark.get("1.0", tk.END).strip(),
            owner_dept,
        )
        if insert_outletter(data):
            messagebox.showinfo("Success", "ထွက်စာ သိမ်းဆည်းပြီးပါပြီ။")
            self.load_records()
