import tkinter as tk
from tkinter import ttk, messagebox
from models.doctype_model import (
    insert_doctype,
    fetch_all_doctypes,
    update_doctype,
    delete_doctype,
)


class DoctypeView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.tree = None
        self.selected_id = None
        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        form_frame = ttk.LabelFrame(self, text=" စာရွက်စာတမ်းအမျိုးအစားသတ်မှတ်ခြင်း (Document Type) ")
        form_frame.pack(fill="x", padx=20, pady=(20, 10))

        ttk.Label(form_frame, text="Document Type:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.cb_doc = ttk.Entry(form_frame, width=33)
        self.cb_doc.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(form_frame, text="မှတ်ချက်:").grid(row=1, column=0, sticky="nw", padx=10, pady=5)
        self.txt_remark = tk.Text(form_frame, width=25, height=6)
        self.txt_remark.grid(row=1, column=1, padx=10, pady=5)

        ttk.Button(form_frame, text="Save Doc Type", command=self.save_data).grid(
            row=2, column=1, sticky="e", padx=10, pady=10
        )

        action_frame = ttk.Frame(form_frame)
        action_frame.grid(row=3, column=1, sticky="e", padx=10, pady=(0, 8))
        ttk.Button(action_frame, text="Refresh", command=self.refresh_data).pack(side="left", padx=4)
        ttk.Button(action_frame, text="Update Selected", command=self.update_data).pack(side="left", padx=4)
        ttk.Button(action_frame, text="Delete Selected", command=self.delete_data).pack(side="left", padx=4)
        ttk.Button(action_frame, text="View Selected", command=self.view_selected).pack(side="left", padx=4)

        self.table_frame = ttk.LabelFrame(self, text="Saved Document Types")
        self.table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self._build_treeview()

    def _build_treeview(self):
        if self.tree:
            self.tree.destroy()

        list_frame = ttk.Frame(self.table_frame)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical")
        scrollbar.pack(side="right", fill="y")

        self.tree = ttk.Treeview(
            list_frame,
            columns=("id", "doctype", "remark"),
            show="headings",
            yscrollcommand=scrollbar.set,
            height=10,
        )
        self.tree.heading("id", text="ID")
        self.tree.heading("doctype", text="Document Type")
        self.tree.heading("remark", text="Remark")

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("doctype", width=180, anchor="w")
        self.tree.column("remark", width=360, anchor="w")

        self.tree.pack(fill="both", expand=True)
        scrollbar.config(command=self.tree.yview)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def refresh_data(self):
        if not self.tree:
            self._build_treeview()

        self.tree.delete(*self.tree.get_children())
        doc_types = fetch_all_doctypes()
        if not doc_types:
            return

        for doc in doc_types:
            # doc expected as (id, doc_type, remark)
            self.tree.insert("", tk.END, iid=str(doc[0]), values=doc)

    def _on_select(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            self.selected_id = None
            return
        self.selected_id = int(sel[0])
        values = self.tree.item(sel[0], "values")
        if values:
            # populate form for quick edit
            try:
                self.cb_doc.set(values[1])
                self.txt_remark.delete("1.0", tk.END)
                self.txt_remark.insert("1.0", values[2] if len(values) > 2 else "")
            except Exception:
                pass

    def get_selected_id(self):
        if not self.selected_id:
            messagebox.showwarning("Select", "Select a row first.")
            return None
        return self.selected_id

    def update_data(self):
        doc_id = self.get_selected_id()
        if not doc_id:
            return
        doc_type = self.cb_doc.get().strip()
        remark = self.txt_remark.get("1.0", tk.END).strip()
        if not doc_type or doc_type == "none":
            messagebox.showwarning("Validation", "Please select a valid document type.")
            return
        if update_doctype(doc_id, (doc_type, remark)):
            messagebox.showinfo("Success", "Document Type updated.")
            self.refresh_data()

    def delete_data(self):
        doc_id = self.get_selected_id()
        if not doc_id:
            return
        if not messagebox.askyesno("Confirm", "Delete selected document type?"):
            return
        if delete_doctype(doc_id):
            messagebox.showinfo("Success", "Document Type deleted.")
            self.txt_remark.delete("1.0", tk.END)
            self.cb_doc.current(0)
            self.selected_id = None
            self.refresh_data()

    def view_selected(self):
        doc_id = self.get_selected_id()
        if not doc_id:
            return
        values = self.tree.item(str(doc_id), "values")
        if not values:
            messagebox.showinfo("Details", "No details available.")
            return
        messagebox.showinfo("Document Type Details", f"ID: {values[0]}\nType: {values[1]}\nRemark: {values[2]}")

    def save_data(self):
        doc_type = self.cb_doc.get().strip()
        remark = self.txt_remark.get("1.0", tk.END).strip()
        if not doc_type or doc_type == "none":
            messagebox.showwarning("Validation", "Please select a valid document type.")
            return

        if insert_doctype((doc_type, remark)):
            messagebox.showinfo("Success", "Document Type တည်ဆောက်ပြီးပါပြီ။")
            self.txt_remark.delete("1.0", tk.END)
            self.cb_doc.current(0)
            self.refresh_data()
