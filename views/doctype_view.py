# views/doctype_view.py
import tkinter as tk
from tkinter import ttk, messagebox
from models.doctype_model import insert_doctype

class DoctypeView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        frame = ttk.LabelFrame(self, text=" စာရွက်စာတမ်းအမျိုးအစားသတ်မှတ်ခြင်း (Document Type) ")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ttk.Label(frame, text="Document Type:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.cb_doc = ttk.Combobox(frame, values=["none", "စာချုပ်တို", "ပေးမိန့်", "စည်းသွား", "မှတ်ချက်"], width=28)
        self.cb_doc.grid(row=0, column=1, padx=10, pady=5); self.cb_doc.current(0)
        
        ttk.Label(frame, text="မှတ်ချက်:").grid(row=1, column=0, sticky="nw", padx=10, pady=5)
        self.txt_remark = tk.Text(frame, width=50, height=6); self.txt_remark.grid(row=1, column=1, padx=10, pady=5)
        
        ttk.Button(frame, text="Save Doc Type", command=self.save_data).grid(row=2, column=1, sticky="e", padx=10, pady=10)
        
    def save_data(self):
        data = (self.cb_doc.get(), self.txt_remark.get("1.0", tk.END).strip())
        if insert_doctype(data):
            messagebox.showinfo("Success", "Document Type တည်ဆောက်ပြီးပါပြီ။")

