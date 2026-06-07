# views/inletter_view.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkcalendar import DateEntry

from src.models.doctype_model import fetch_all_doctypes
from src.models.inletter_model import insert_inletter, fetch_inletters, fetch_inletter_by_id, update_inletter, delete_inletter
from src.models.dept_model import fetch_department_names
from src.models.user_model import is_admin, get_user_department
from src.models.activity_log_model import log_activity


class InletterView(ttk.Frame):
    """Inletter (ဝင်စာ) management view — entry form, record list, and CRUD actions."""

    def __init__(self, parent, current_user=None):
        super().__init__(parent)
        self.current_user = current_user or {}  # logged-in user dict (used for permission checks)
        self.attach_path = ""                    # path of the currently attached file
        self.editing_id = None                   # set to file_id when updating; None means "insert" mode
        self.setup_ui()
        self.load_records()

    def setup_ui(self):
        """Build the entire UI: scrollable canvas → entry form → record list → action buttons → footer."""
        dept_names = fetch_department_names() or ["General Office"]
        user_dept = get_user_department(self.current_user)
        admin = is_admin(self.current_user)

        # Create a canvas with a single scrollbar for the whole page
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # Create a frame inside the canvas to hold all content
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.window_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda event: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.bind(
            "<Configure>",
            lambda event: self.canvas.itemconfig(self.window_id, width=event.width),
        )

        # Bind mouse wheel to scroll
        self.canvas.bind_all("<MouseWheel>", lambda event: self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))

        # Build the form inside the scrollable frame
        form_frame = ttk.LabelFrame(self.scrollable_frame, text=" ဝင်စာစာရင်းသွင်းဖောင် (Inletter Entry) ")
        form_frame.pack(fill="both", expand=True, padx=15, pady=10)

        frame = ttk.Frame(form_frame)
        frame.pack(fill="both", expand=True, padx=15, pady=15)

        ttk.Label(frame, text="Letter Date:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.ent_date = DateEntry(frame, width=30, date_pattern="yyyy-mm-dd")
        self.ent_date.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(frame, text="Send Date:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.ent_send = DateEntry(frame, width=30, date_pattern="yyyy-mm-dd")
        self.ent_send.grid(row=1, column=1, padx=10, pady=5)

        # lettertype ကို doc_type table ကနေ combo box နဲ့ရွေးချယ်စေဖို့ ပြင်ဆင်ထားတာကို အမြန်ဆုံး ပြန်လည်တင်ပြပါမယ်။ ဒီလိုလုပ်ရတဲ့အကြောင်းကတော့ စာရွက်စာတမ်းအမျိုးအစားတွေကို အလွယ်တကူ ထပ်ထည့်နိုင်ဖို့နဲ့ အမျိုးအစားအသစ်တွေကို အလွယ်တကူ စီမံခန့်ခွဲနိုင်ဖို့ပါ။    
        ttk.Label(frame, text="Letter Type:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        letter_types = [dt[1] for dt in fetch_all_doctypes()]
        if "none" not in letter_types:
            letter_types.insert(0, "none")

        self.ent_type = ttk.Combobox(frame, values=letter_types, width=30, state="readonly")
        self.ent_type.grid(row=2, column=1, padx=10, pady=5)
        self.ent_type.current(0)

        ttk.Label(frame, text="Title / အကြောင်းအရာ:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.txt_title = tk.Text(frame, width=25, height=3)
        self.txt_title.grid(row=3, column=1, padx=10, pady=5)

        ttk.Label(frame, text="ပေးပို့ဌာန:").grid(row=4, column=0, sticky="w", padx=10, pady=5)
        self.cb_dept = ttk.Combobox(frame, values=["Ministry List", "Department List", "Other"], width=30)
        self.cb_dept.grid(row=4, column=1, padx=10, pady=5)

        ttk.Label(frame, text="လက်ခံသူ:").grid(row=5, column=0, sticky="w", padx=10, pady=5)
        self.ent_rec = ttk.Entry(frame, width=33)
        self.ent_rec.grid(row=5, column=1, padx=10, pady=5)

        ttk.Label(frame, text="Owner Department:").grid(row=6, column=0, sticky="w", padx=10, pady=5)
        self.cb_owner_dept = ttk.Combobox(frame, values=dept_names, width=30)
        self.cb_owner_dept.grid(row=6, column=1, padx=10, pady=5)
        if admin:
            self.cb_owner_dept.set(dept_names[0] if dept_names else "")
        else:
            self.cb_owner_dept.set(user_dept)
            self.cb_owner_dept.config(state="readonly")

        ttk.Label(frame, text="လုံခြုံရေးအဆင့်အတန်း:").grid(row=7, column=0, sticky="w", padx=10, pady=5)
        self.cb_sec = ttk.Combobox(
            frame, values=["ရိုးရိုး", "ကန့်သတ်", "အတွင်းရေး", "လျှို့ဝှက်", "ထိပ်တန်းလျှို့ဝှက်"], width=30
        )
        self.cb_sec.grid(row=7, column=1, padx=10, pady=5)
        self.cb_sec.current(0)

        ttk.Label(frame, text="အရေးကြီးအဆင့်အတန်း:").grid(row=8, column=0, sticky="w", padx=10, pady=5)
        self.cb_urg = ttk.Combobox(frame, values=["ရိုးရိုး", "အရေးကြီး", "အမြန်", "ချက်ချင်း"], width=30)
        self.cb_urg.grid(row=8, column=1, padx=10, pady=5)
        self.cb_urg.current(0)

        ttk.Label(frame, text="ဖိုင်တွဲအမှတ်/Casefile:").grid(row=9, column=0, sticky="w", padx=10, pady=5)
        self.ent_case = ttk.Entry(frame, width=33)
        self.ent_case.grid(row=9, column=1, padx=10, pady=5)

        ttk.Label(frame, text="Attachment:").grid(row=10, column=0, padx=10, pady=5, sticky="w")
        ttk.Button(frame, text="Browse...", command=self.browse).grid(row=10, column=1, sticky="w", padx=(10,0), pady=5)
        self.lbl_file = ttk.Label(frame, text="No file attached")
        self.lbl_file.grid(row=10, column=1, padx=(120,0), pady=5)

        ttk.Label(frame, text="မှတ်ချက်:").grid(row=11, column=0, sticky="nw", padx=10, pady=5)
        self.txt_remark = tk.Text(frame, width=25, height=3)
        self.txt_remark.grid(row=11, column=1, padx=10, pady=5)

        ttk.Button(frame, text="Save Inletter", command=self.save_data).grid(row=12, column=1, sticky="e", padx=10, pady=10)

        hint = "Admin: all departments  |  Staff: only your department's inletters"
        if not admin and user_dept:
            hint = f"Your department: {user_dept} — you only see inletters for this department."
        ttk.Label(self.scrollable_frame, text=hint, font=("Segoe UI", 9), foreground="#475569").pack(anchor="w", padx=20)

        list_frame = ttk.LabelFrame(self.scrollable_frame, text=" Inletters (department-filtered) ")
        list_frame.pack(fill="both", expand=True, padx=15, pady=10)

        cols = ("file_id", "letter_date", "title", "dept_from", "recipient", "owner_department")
        self.tree = ttk.Treeview(list_frame, columns=cols, show="headings", height=8)
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)
        for c, h in zip(cols, ["ID", "Date", "Date_Reciept", "Lter_Type", "Title/Subject", "Department"]):
            self.tree.heading(c, text=h)
            self.tree.column(c, width=120 if c != "title" else 200)

        # --- Action buttons below the treeview ---
        # View:   open a read-only popup with all field details
        # Update: load the selected record into the form for editing, then Save to commit
        # Delete: confirm and delete the selected record from the database
        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(fill="x", padx=5, pady=(5, 5))
        ttk.Button(btn_frame, text="View", command=self.view_record, width=10).pack(side="left", padx=3)
        ttk.Button(btn_frame, text="Update", command=self.update_record, width=10).pack(side="left", padx=3)
        ttk.Button(btn_frame, text="Delete", command=self.delete_record, width=10).pack(side="left", padx=3)

        # Footer
        footer_frame = ttk.Frame(self.scrollable_frame)
        footer_frame.pack(fill="x", side="bottom", padx=15, pady=(5, 10))
        
        separator = ttk.Separator(footer_frame, orient="horizontal")
        separator.pack(fill="x", pady=(0, 5))
        
        footer_label = ttk.Label(
            footer_frame,
            text="© 2024 Document Management System (DMS) | Inletter Module",
            font=("Segoe UI", 8),
            foreground="#64748b"
        )
        footer_label.pack(side="left")
        
        version_label = ttk.Label(
            footer_frame,
            text="v1.0",
            font=("Segoe UI", 8),
            foreground="#94a3b8"
        )
        version_label.pack(side="right")

    def refresh_data(self):
        """Public refresh hook — called by the parent/dashboard after data changes."""
        self.load_records()

    def load_records(self):
        """Reload the treeview with the latest inletter records from the database."""
        self.tree.delete(*self.tree.get_children())
        for row in fetch_inletters(self.current_user):
            self.tree.insert("", "end", values=row)

    def browse(self):
        """Open a file dialog to select an attachment file."""
        fn = filedialog.askopenfilename()
        if fn:
            self.attach_path = fn
            self.lbl_file.config(text=fn.replace("\\", "/").split("/")[-1])

    def save_data(self):
        """Save (insert or update) the current form data.
        
        If self.editing_id is set, this performs an UPDATE on that record.
        Otherwise, it performs a new INSERT.
        After a successful save, the form is cleared and the list is refreshed.
        """
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
            self.ent_send.get(),
            self.ent_type.get(),
            self.txt_title.get("1.0", tk.END).strip(),
            self.cb_dept.get(),
            self.ent_rec.get(),
            self.cb_sec.get(),
            self.cb_urg.get(),
            self.ent_case.get(),
            self.attach_path,
            self.txt_remark.get("1.0", tk.END).strip(),
            owner_dept,
        )
        if self.editing_id:
            # UPDATE mode — editing_id holds the file_id of the record being edited
            if update_inletter(self.editing_id, data, self.current_user):
                messagebox.showinfo("Success", "ဝင်စာ ပြင်ဆင်ပြီးပါပြီ။")
                self.editing_id = None  # reset back to insert mode
                self.load_records()
                self._clear_form()
        else:
            # INSERT mode — create a brand-new record
            if insert_inletter(data, self.current_user):
                messagebox.showinfo("Success", "ဝင်စာ သိမ်းဆည်းပြီးပါပြီ။")
                self.load_records()
                self._clear_form()

    def _get_selected_id(self):
        """Return the file_id of the currently selected treeview row, or None if nothing is selected."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection", "စာရင်းမှတစ်ခု ရွေးချယ်ပါ။")
            return None
        values = self.tree.item(selected[0], "values")
        return values[0]  # first column is file_id

    def _clear_form(self):
        """Reset all form fields to their default/empty state."""
        self.ent_date.set_date(self.ent_date.get())
        self.ent_send.set_date(self.ent_send.get())
        self.ent_type.current(0)
        self.txt_title.delete("1.0", tk.END)
        self.cb_dept.set("")
        self.ent_rec.delete(0, tk.END)
        self.cb_sec.current(0)
        self.cb_urg.current(0)
        self.ent_case.delete(0, tk.END)
        self.attach_path = ""
        self.lbl_file.config(text="No file attached")
        self.txt_remark.delete("1.0", tk.END)

    def _populate_form(self, record):
        """Fill form fields with record data for editing.
        
        Args:
            record: tuple from fetch_inletter_by_id —
                    (file_id, letter_date, send_date, letter_type, title, dept_from,
                     recipient, security_lvl, urgency_lvl, casefile_no,
                     attachment_path, remark, owner_department)
        """
        file_id, letter_date, send_date, letter_type, title, dept_from, \
            recipient, security_lvl, urgency_lvl, casefile_no, \
            attachment_path, remark, owner_department = record

        self.ent_date.set_date(letter_date)
        self.ent_send.set_date(send_date)
        self.ent_type.set(letter_type or "none")
        self.txt_title.delete("1.0", tk.END)
        self.txt_title.insert("1.0", title or "")
        self.cb_dept.set(dept_from or "")
        self.ent_rec.delete(0, tk.END)
        self.ent_rec.insert(0, recipient or "")
        self.cb_owner_dept.set(owner_department or "")
        self.cb_sec.set(security_lvl or "ရိုးရိုး")
        self.cb_urg.set(urgency_lvl or "ရိုးရိုး")
        self.ent_case.delete(0, tk.END)
        self.ent_case.insert(0, casefile_no or "")
        self.attach_path = attachment_path or ""
        self.lbl_file.config(text=attachment_path.replace("\\", "/").split("/")[-1] if attachment_path else "No file attached")
        self.txt_remark.delete("1.0", tk.END)
        self.txt_remark.insert("1.0", remark or "")

    def view_record(self):
        """Open a read-only popup window showing all details of the selected inletter record."""
        file_id = self._get_selected_id()
        if not file_id:
            return
        record = fetch_inletter_by_id(file_id)
        if not record:
            messagebox.showerror("Error", "အချက်အလက် ရှာမရပါ။")
            return
        # Build a read-only detail popup (Toplevel window)
        win = tk.Toplevel(self)
        win.title(f"Inletter Detail — ID {file_id}")
        win.geometry("520x480")
        win.resizable(False, False)

        # Map each field label to its value from the fetched record
        fields = [
            ("File ID", record[0]),          # primary key
            ("Letter Date", record[1]),      # စာရွက်ရဲ့ ရက်စွဲ
            ("Send Date", record[2]),        # ပေးပို့ရက်စွဲ
            ("Letter Type", record[3]),      # စာရွက်အမျိုးအစား
            ("Title", record[4]),            # အကြောင်းအရာ
            ("Dept From", record[5]),        # ပေးပို့ဌာန
            ("Recipient", record[6]),        # လက်ခံသူ
            ("Security Level", record[7]),   # လုံခြုံရေးအဆင့်
            ("Urgency Level", record[8]),    # အရေးကြီးအဆင့်
            ("Casefile No", record[9]),      # ဖိုင်တွဲအမှတ်
            ("Attachment", record[10]),      # တွဲဖက်ဖိုင်
            ("Remark", record[11]),          # မှတ်ချက်
            ("Owner Department", record[12]),# ပိုင်ဆိုင်သည့်ဌာန
        ]
        for i, (label, value) in enumerate(fields):
            ttk.Label(win, text=label + ":", font=("Segoe UI", 10, "bold")).grid(
                row=i, column=0, sticky="w", padx=(15, 5), pady=3
            )
            ttk.Label(win, text=str(value or ""), font=("Segoe UI", 10)).grid(
                row=i, column=1, sticky="w", padx=(5, 15), pady=3
            )
        ttk.Button(win, text="Close", command=win.destroy).grid(
            row=len(fields), column=0, columnspan=2, pady=10
        )

    def update_record(self):
        """Load the selected record into the entry form for editing.
        
        Sets self.editing_id so that save_data() will perform an UPDATE
        instead of an INSERT. The user edits the fields and clicks
        'Save Inletter' to commit the changes.
        """
        file_id = self._get_selected_id()
        if not file_id:
            return
        record = fetch_inletter_by_id(file_id)
        if not record:
            messagebox.showerror("Error", "အချက်အလက် ရှာမရပါ။")
            return
        self.editing_id = file_id       # flag that we are in update mode
        self._populate_form(record)     # fill the form with existing data
        messagebox.showinfo("Update", "ဖောင်တွင် ပြင်ဆင်ပြီး Save Inletter နှိပ်ပါ။")

    def delete_record(self):
        """Confirm and delete the selected inletter record from the database.
        
        Shows a yes/no confirmation dialog before actually deleting.
        On success, refreshes the treeview list.
        """
        file_id = self._get_selected_id()
        if not file_id:
            return
        # Ask the user to confirm before deleting
        if not messagebox.askyesno("Confirm Delete", f"ID {file_id} ကို ဖျက်မှာ သေချာပါသလား？"):
            return
        if delete_inletter(file_id, self.current_user):
            messagebox.showinfo("Deleted", f"ID {file_id} ဖျက်ပြီးပါပြီ။")
            self.load_records()
