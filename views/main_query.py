# views/main_query.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
from models.user_model import is_admin, get_user_department

# Views များမှ UI Class များကို တိုက်ရိုက်ချိတ်ဆက်ခေါ်ယူခြင်း
from .inletter_query import InLetterQuery
from .outletter_query import OutLetterQuery

class MainQueryView(ttk.Frame):
    """ဝင်စာနှင့် ထွက်စာ ရှာဖွေရေးစာမျက်နှာနှစ်ခုလုံးကို Tab စနစ်ဖြင့် စုစည်းပေးသော View Class"""
    
    def __init__(self, parent, current_user=None):
        super().__init__(parent)
        self.current_user = current_user or {}
        self.setup_ui()

    def setup_ui(self):
        # စာမျက်နှာအပေါ်ဆုံးတွင် ခေါင်းစဉ်နှင့် ဌာနအချက်အလက်ပြသရန် Header Frame
        header_frame = ttk.Frame(self)
        header_frame.pack(fill="x", padx=15, pady=10)

        lbl_header = ttk.Label(header_frame, text="စာရွက်စာတမ်းများ ရှာဖွေစစ်ဆေးခြင်း", font=("Segoe UI", 14, "bold"))
        lbl_header.pack(side="left")

        # Admin ဟုတ်မဟုတ်အပေါ်မူတည်ပြီး ဌာနအချက်အလက်ပြသခြင်း
        dept_hint = "All Departments (Admin Mode)" if is_admin(self.current_user) else f"Department: {get_user_department(self.current_user)}"
        lbl_dept = ttk.Label(header_frame, text=dept_hint, font=("Segoe UI", 10, "italic"), foreground="gray")
        lbl_dept.pack(side="right", padx=10)

        # Tab Control (Notebook) အား တည်ဆောက်ခြင်း
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=15, pady=5)

        # ----------------------------------------------------
        # Tab 1: ဝင်စာများ ရှာဖွေရန် (Inletters)
        # ----------------------------------------------------
        # inletter_query.py မှ UI Class အား ခေါ်ယူအသုံးပြုခြင်း
        self.tab_inletter = InLetterQuery(self.notebook, self.current_user)
        self.notebook.add(self.tab_inletter, text="  ဝင်စာများ ရှာဖွေရန် (In-Letters)  ")

        # ----------------------------------------------------
        # Tab 2: ထွက်စာများ ရှာဖွေရန် (Outletters)
        # ----------------------------------------------------
        # outletter_query.py မှ UI Class အား ခေါ်ယူအသုံးပြုခြင်း
        self.tab_outletter = OutLetterQuery(self.notebook, self.current_user)
        self.notebook.add(self.tab_outletter, text="  ထွက်စာများ ရှာဖွေရန် (Out-Letters)  ")

    def refresh_data(self):
        """စာမျက်နှာများအားလုံးကို အချက်အလက်သစ် ပြန်လည်ဆွဲယူခိုင်းခြင်း (Refresh)"""
        if hasattr(self.tab_inletter, 'refresh_data'):
            self.tab_inletter.refresh_data()
        if hasattr(self.tab_outletter, 'refresh_data'):
            self.tab_outletter.refresh_data()