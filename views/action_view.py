# views/action_view.py
import tkinter as tk
from tkinter import ttk, messagebox
from models.action_model import insert_action

class ActionView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        frame = ttk.LabelFrame(self, text=" လုပ်ငန်းဆောင်ရွက်မှုမှတ်တမ်း (Action Entry & Process) ")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ttk.Label(frame, text="Action Type:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.cb_act = ttk.Combobox(frame, values=["none", "သက်ဆိုင်ရာဌာနသို့လွဲပေးခြင်း", "တင်ပြစာရေးခြင်း", "အကြောင်းပြန်ခြင်း"], width=35)
        self.cb_act.grid(row=0, column=1, padx=10, pady=5); self.cb_act.current(0)
        self.cb_act.bind("<<ComboboxSelected>>", self.update_sub_actions)
        
        ttk.Label(frame, text="Action Process:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.cb_proc = ttk.Combobox(frame, values=["ဆောင်ရွက်ရန်ကျန်", "ဆောင်ရွက်ဆဲ", "ဆောင်ရွက်ပြီး"], width=35)
        self.cb_proc.grid(row=1, column=1, padx=10, pady=5); self.cb_proc.current(0)
        
        ttk.Label(frame, text="Sub Action:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.cb_sub = ttk.Combobox(frame, values=[], width=35); self.cb_sub.grid(row=2, column=1, padx=10, pady=5)
        
        ttk.Label(frame, text="မှတ်ချက်:").grid(row=3, column=0, sticky="nw", padx=10, pady=5)
        self.txt_remark = tk.Text(frame, width=50, height=5); self.txt_remark.grid(row=3, column=1, padx=10, pady=5)
        
        ttk.Button(frame, text="Save Action", command=self.save_data).grid(row=4, column=1, sticky="e", padx=10, pady=10)
        
    def update_sub_actions(self, event):
        # Action Type ပေါ်မူတည်၍ Sub Action များကို ပြောင်းလဲပေးခြင်း
        act_type = self.cb_act.get()
        if act_type == "တင်ပြစာရေးခြင်း":
            self.cb_sub.config(values=["သက်ဆိုင်ရာလူကြီးမှတ်ချက်များ"])
        elif act_type == "အကြောင်းပြန်ခြင်း":
            self.cb_sub.config(values=["မရှိကြောင်းပြန်ခြင်း", "ဆောင်ရွက်ပြီးစီးမှုပြန်ကြားခြင်း", "အောက်ဌာနအကြောင်းကြားခြင်း"])
        else:
            self.cb_sub.config(values=[])
        self.cb_sub.set("")

    def save_data(self):
        data = (self.cb_act.get(), self.cb_proc.get(), self.cb_sub.get(), self.txt_remark.get("1.0", tk.END).strip())
        if insert_action(data):
            messagebox.showinfo("Success", "လုပ်ဆောင်ချက် လုပ်ငန်းစဉ် သိမ်းဆည်းပြီးပါပြီ။")