# views/dept_view.py
import tkinter as tk
from tkinter import ttk, messagebox
from models.dept_model import insert_dept

class DeptView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        frame = ttk.LabelFrame(self, text=" ဌာနဆိုင်ရာအချက်အလက်သွင်းခြင်း (Department Entry) ")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ttk.Label(frame, text="Department Name:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.ent_name = ttk.Entry(frame, width=40); self.ent_name.grid(row=0, column=1, padx=10, pady=5)
        
        ttk.Label(frame, text="Department Type:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.cb_type = ttk.Combobox(frame, values=["Gov (လွှတ်တော်/အစိုးရအဖွဲ့/ကော်မတီ/တရားရေး)", "NonGov"], width=38); self.cb_type.grid(row=1, column=1, padx=10, pady=5)
        
        ttk.Label(frame, text="Department Level:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.cb_lvl = ttk.Combobox(frame, values=["ဝန်ကြီးဌာန (၁)", "ဦးစီးဌာန (၂)", "ဌာနခွဲ (၃)", "တိုင်းဒေသကြီး/ပြည်နယ် (၁)", "ခရိုင် (၂)", "မြို့နယ် (၃)"], width=38)
        self.cb_lvl.grid(row=2, column=1, padx=10, pady=5)
        
        ttk.Label(frame, text="Address:").grid(row=3, column=0, sticky="nw", padx=10, pady=5)
        self.txt_addr = tk.Text(frame, width=40, height=3); self.txt_addr.grid(row=3, column=1, padx=10, pady=5)
        
        ttk.Label(frame, text="Email (*@*):").grid(row=4, column=0, sticky="w", padx=10, pady=5)
        self.ent_email = ttk.Entry(frame, width=40); self.ent_email.grid(row=4, column=1, padx=10, pady=5)
        
        ttk.Label(frame, text="Phone Number:").grid(row=5, column=0, sticky="w", padx=10, pady=5)
        self.ent_phone = ttk.Entry(frame, width=40); self.ent_phone.grid(row=5, column=1, padx=10, pady=5)
        
        ttk.Label(frame, text="မှတ်ချက်:").grid(row=6, column=0, sticky="nw", padx=10, pady=5)
        self.txt_remark = tk.Text(frame, width=40, height=3); self.txt_remark.grid(row=6, column=1, padx=10, pady=5)
        
        ttk.Button(frame, text="Save Department", command=self.save_data).grid(row=7, column=1, sticky="e", padx=10, pady=10)
        
    def save_data(self):
        data = (self.ent_name.get(), self.cb_type.get(), self.cb_lvl.get(), self.txt_addr.get("1.0", tk.END).strip(),
                self.ent_email.get(), self.ent_phone.get(), self.txt_remark.get("1.0", tk.END).strip())
        if insert_dept(data):
            messagebox.showinfo("Success", "ဌာနဆိုင်ရာ အချက်အလက်များ သိမ်းဆည်းပြီးပါပြီ။")