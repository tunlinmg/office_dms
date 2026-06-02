import tkinter as tk
from tkinter import ttk

# main_canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
# main_scrollbar = ttk.Scrollbar(self, orient="vertical", command=main_canvas.yview)
# main_canvas.configure(yscrollcommand=main_scrollbar.set)

# main_scrollbar.pack(side="right", fill="y")
# main_canvas.pack(side="left", fill="both", expand=True)

# # Frame inside canvas to hold all content
# content_frame = ttk.Frame(main_canvas)
# window_id = main_canvas.create_window((0, 0), window=content_frame, anchor="nw")

# def configure_canvas(event):
#     main_canvas.configure(scrollregion=main_canvas.bbox("all"))
#     main_canvas.itemconfig(window_id, width=event.width)

# content_frame.bind("<Configure>", configure_canvas)
# main_canvas.bind("<Configure>", configure_canvas)

# # Mouse wheel scrolling
# def _on_mousewheel(event):
#     main_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

# main_canvas.bind_all("<MouseWheel>", _on_mousewheel)

# --- Form Section ---
root = tk.Tk()
root.geometry("600x400")
root.columnconfigure(0, weight=1)

form_frame = ttk.LabelFrame(root, text="ထွက်စာစာရင်းသွင်းဖောင် (Out Letter Entry)")
form_frame.grid(row=0, column=0, padx=5, pady=5)
form_frame.columnconfigure(0, weight=1, uniform="input")
form_frame.columnconfigure(1, weight=1, uniform="input")

dateLabel = ttk.Label(form_frame, text="Letter Date:")
dateLabel.grid(row=0, column=0, padx=5, pady=5)

dateEntry = ttk.Entry(form_frame,)
dateEntry.grid(row=0, column=1, padx=5, pady=5, stick="w")

letterTypeLabel = ttk.Label(form_frame, text="Letter Type:")
letterTypeLabel.grid(row=1, column=0,padx=5, pady=5)

letterTypeEntry = ttk.Entry(form_frame,)
letterTypeEntry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

ttk.Label(form_frame, text="Title / အကြောင်းအရာ:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
ent_title = ttk.Entry(form_frame,)
ent_title.grid(row=2, column=1, padx=5, pady=5)

ttk.Label(form_frame, text="ပေးပို့ဌာန လိပ်မူ/မိတ္တူ:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
cb_dept = ttk.Combobox(form_frame, values=["Ministry List", "Other"],)
cb_dept.grid(row=3, column=1, padx=10, pady=5)

ttk.Label(form_frame, text="Owner Department:").grid(row=4, column=0, sticky="w", padx=10, pady=5)
cb_owner_dept = ttk.Combobox(form_frame,)
cb_owner_dept.grid(row=4, column=1, padx=10, pady=5)
# if admin:
#     cb_owner_dept.set(dept_names[0] if dept_names else "")
# else:
#     cb_owner_dept.set(user_dept)
#     cb_owner_dept.config(state="readonly")

ttk.Label(form_frame, text="လုံခြုံရေးအဆင့်အတန်း:").grid(row=5, column=0, sticky="w", padx=10, pady=5)
cb_sec = ttk.Combobox(
    form_frame, values=["ရိုးရိုး", "ကန့်သတ်", "အတွင်းရေး", "လျှို့ဝှက်", "ထိပ်တန်းလျှို့ဝှက်"],
)
cb_sec.grid(row=5, column=1, padx=10, pady=5)
cb_sec.current(0)

ttk.Label(form_frame, text="အရေးကြီးအဆင့်အတန်း:").grid(row=6, column=0, sticky="w", padx=10, pady=5)
cb_urg = ttk.Combobox(form_frame, values=["ရိုးရိုး", "အရေးကြီး", "အမြန်", "ချက်ချင်း"],)
cb_urg.grid(row=6, column=1, padx=10, pady=5)
cb_urg.current(0)

ttk.Label(form_frame, text="ဖိုင်တွဲအမှတ်/Casefile:").grid(row=7, column=0, sticky="w", padx=10, pady=5)
ent_case = ttk.Entry(form_frame,)
ent_case.grid(row=7, column=1, padx=10, pady=5)

ttk.Label(form_frame, text="Attachment:").grid(row=8, column=0, sticky="w", padx=10, pady=5)
ttk.Button(form_frame, text="Browse...").grid(row=8, column=1, sticky="w", padx=10, pady=5)
lbl_file = ttk.Label(form_frame, text="No file attached")
lbl_file.grid(row=8, column=1, padx=120, pady=5)

ttk.Label(form_frame, text="မှတ်ချက်:").grid(row=9, column=0, sticky="nw", padx=10, pady=5)
txt_remark = tk.Text(form_frame, height=3)
txt_remark.grid(row=9, column=1, padx=10, pady=5)

ttk.Button(form_frame, text="Save Out Letter",).grid(row=10, column=1, sticky="e", padx=10, pady=10)

# --- Hint Label ---
hint = "Admin: all departments  |  Staff: only your department's outletters"
# if not admin and user_dept:
#     hint = f"Your department: {user_dept} — you only see outletters for this department."
ttk.Label(root, text=hint, font=("Segoe UI", 9), foreground="#475569")
#.pack(anchor="w", padx=20)

# --- List Section ---
list_frame = ttk.LabelFrame(root, text=" Outletters (department-filtered) ")
#list_frame.pack(fill="both", expand=True, padx=15, pady=10)

cols = ("file_id", "letter_date", "title", "dept_to", "owner_department")
tree = ttk.Treeview(list_frame, columns=cols, show="headings", height=8)
tree.pack(fill="both", expand=True, padx=5, pady=5)
for c, h in zip(cols, ["ID", "Date", "Title", "Dept To", "Department"]):
    tree.heading(c, text=h)
    tree.column(c)

# --- Footer Section ---
footer_frame = ttk.Frame(root)
#footer_frame.pack(fill="x", padx=15, pady=(0, 10))

# Separator line
separator = ttk.Separator(footer_frame, orient="horizontal")
separator.pack(fill="x", pady=(10, 5))

# Footer content
footer_inner = ttk.Frame(footer_frame)
footer_inner.pack(fill="x")

# Left side - Record count
lbl_record_count = ttk.Label(footer_inner, text="Total Records: 0", font=("Segoe UI", 9))
lbl_record_count.pack(side="left", padx=5)

# Right side - System info
footer_info = ttk.Label(
    footer_inner, 
    text="DMS - Document Management System | Outletter Module", 
    font=("Segoe UI", 9), 
    foreground="#64748b"
)
footer_info.pack(side="right", padx=5)

root.mainloop()