# views/action_view.py
import tkinter as tk
from tkinter import ttk, messagebox
from models.action_model import insert_action, fetch_letters


class ActionView(ttk.Frame):
    def __init__(self, parent, current_user=None):
        super().__init__(parent)
        self.current_user = current_user
        self.letter_map = {}
        self.setup_ui()
        
    def setup_ui(self):
        frame = ttk.LabelFrame(self, text=" လုပ်ငန်းဆောင်ရွက်မှုမှတ်တမ်း (Action Entry & Process) ")
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Letter selection (choose an inletter or outletter to attach action)
        ttk.Label(frame, text="Select Letter:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.cb_letter = ttk.Combobox(frame, values=[], width=60, state="readonly")
        self.cb_letter.grid(row=0, column=1, padx=10, pady=5)
        self._populate_letters()

        ttk.Label(frame, text="Action Type:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.cb_act = ttk.Combobox(frame, values=["none", "သက်ဆိုင်ရာဌာနသို့လွဲပေးခြင်း", "တင်ပြစာရေးခြင်း", "အကြောင်းပြန်ခြင်း"], width=30)
        self.cb_act.grid(row=1, column=1, padx=10, pady=5); self.cb_act.current(0)
        self.cb_act.bind("<<ComboboxSelected>>", self.update_sub_actions)
        
        ttk.Label(frame, text="Action Process:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.cb_proc = ttk.Combobox(frame, values=["ဆောင်ရွက်ရန်ကျန်", "ဆောင်ရွက်ဆဲ", "ဆောင်ရွက်ပြီး"], width=30)
        self.cb_proc.grid(row=2, column=1, padx=10, pady=5); self.cb_proc.current(0)
        
        ttk.Label(frame, text="Sub Action:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.cb_sub = ttk.Combobox(frame, values=[], width=30); self.cb_sub.grid(row=3, column=1, padx=10, pady=5)
        
        ttk.Label(frame, text="မှတ်ချက်:").grid(row=4, column=0, sticky="nw", padx=10, pady=5)
        self.txt_remark = tk.Text(frame, width=25, height=5); self.txt_remark.grid(row=4, column=1, padx=10, pady=5)

        ttk.Button(frame, text="Save Action", command=self.save_data).grid(row=5, column=1, sticky="e", padx=10, pady=10)
        # Datasheet frame showing recent letters (inletter/outletter)
        ds_frame = ttk.LabelFrame(self, text=" Letters Datasheet ")
        ds_frame.pack(fill="both", expand=True, padx=20, pady=(0,20))

        self.ds_scroll_y = ttk.Scrollbar(ds_frame, orient="vertical")
        self.ds_scroll_x = ttk.Scrollbar(ds_frame, orient="horizontal")
        self.ds_tree = ttk.Treeview(
            ds_frame,
            columns=("source", "file_id", "display", "status"),
            show="headings",
            yscrollcommand=self.ds_scroll_y.set,
            xscrollcommand=self.ds_scroll_x.set,
            height=8,
        )
        self.ds_scroll_y.pack(side="right", fill="y")
        self.ds_scroll_x.pack(side="bottom", fill="x")
        self.ds_scroll_y.config(command=self.ds_tree.yview)
        self.ds_scroll_x.config(command=self.ds_tree.xview)
        self.ds_tree.pack(fill="both", expand=True)

        self.ds_tree.heading("source", text="Source")
        self.ds_tree.heading("file_id", text="File ID")
        self.ds_tree.heading("display", text="Title / Summary")
        self.ds_tree.heading("status", text="Current Action")
        self.ds_tree.column("source", width=100, anchor="w")
        self.ds_tree.column("file_id", width=70, anchor="center")
        self.ds_tree.column("display", width=450, anchor="w")
        self.ds_tree.column("status", width=250, anchor="w")

        # Bind selection to populate the letter combobox
        self.ds_tree.bind("<<TreeviewSelect>>", self._on_datasheet_select)
        # populate datasheet
        self._populate_datasheet()
        
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
        # Determine selected letter reference
        selected = self.cb_letter.get()
        ref_table = None
        ref_id = None
        if selected:
            mapped = self.letter_map.get(selected)
            if mapped:
                ref_table, ref_id = mapped

        data = (
            self.cb_act.get(),
            self.cb_proc.get(),
            self.cb_sub.get(),
            self.txt_remark.get("1.0", tk.END).strip(),
            ref_table,
            ref_id,
        )
        if insert_action(data):
            messagebox.showinfo("Success", "လုပ်ဆောင်ချက် လုပ်ငန်းစဉ် သိမ်းဆည်းပြီးပါပြီ။")
            # Refresh letter list to show recent actions if needed
            self._populate_letters()

    def _populate_letters(self):
        try:
            rows = fetch_letters(self.current_user)
            display = [r[0] for r in rows]
            self.letter_map = {r[0]: (r[1], r[2]) for r in rows}
            self.cb_letter.config(values=display)
            if display:
                self.cb_letter.set(display[0])
            # also refresh datasheet
            self._populate_datasheet(rows)
        except Exception:
            self.letter_map = {}
            self.cb_letter.config(values=[])

    def _populate_datasheet(self, rows=None):
        try:
            if rows is None:
                rows = fetch_letters(self.current_user)
            # clear
            for item in self.ds_tree.get_children():
                self.ds_tree.delete(item)
            for r in rows:
                disp, src, fid, status = r[0], r[1], r[2], r[3] if len(r) > 3 else ""
                self.ds_tree.insert("", "end", values=(src, fid, disp, status))
        except Exception:
            pass

    def _on_datasheet_select(self, event):
        sel = self.ds_tree.selection()
        if not sel:
            return
        vals = self.ds_tree.item(sel[0], "values")
        if not vals:
            return
        disp = vals[2]
        # set combobox to the selected display string if present
        try:
            if disp in self.letter_map:
                self.cb_letter.set(disp)
        except Exception:
            pass