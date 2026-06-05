# views/role_management.py
import tkinter as tk
from tkinter import ttk, messagebox
from models.row_model import TABLE_REGISTRY, get_table_options, fetch_rows, update_row, delete_row
from models.role_model import user_can


class RoleManagementView(ttk.Frame):
    def __init__(self, parent, current_user):
        super().__init__(parent)
        self.current_user = current_user
        self.current_table = "inletter"
        self.setup_ui()
        self.load_rows()

    def setup_ui(self):
        top = ttk.LabelFrame(self, text=" စာရင်းအတန်းစီမံခန့်ခွဲမှု (Row Management) ")
        top.pack(fill="x", padx=15, pady=10)

        ttk.Label(top, text="Table:").pack(side="left", padx=10, pady=8)
        labels = [label for _, label in get_table_options()]
        keys = [key for key, _ in get_table_options()]
        self.table_map = dict(zip(labels, keys))
        self.cb_table = ttk.Combobox(top, values=labels, width=40, state="readonly")
        self.cb_table.pack(side="left", padx=5, pady=8)
        self.cb_table.set(labels[0])
        self.cb_table.bind("<<ComboboxSelected>>", self.on_table_change)

        ttk.Button(top, text="Refresh", command=self.load_rows).pack(side="left", padx=5)
        # Show Edit button only to users with edit permission
        if user_can(self.current_user, "can_edit_rows"):
            ttk.Button(top, text="Edit Selected", command=self.edit_row).pack(side="left", padx=5)
        if user_can(self.current_user, "can_delete_rows"):
            ttk.Button(top, text="Delete Selected", command=self.remove_row).pack(side="left", padx=5)

        self.grid_frame = ttk.LabelFrame(self, text=" Data Rows ")
        self.grid_frame.pack(fill="both", expand=True, padx=15, pady=5)

        self.scroll_y = ttk.Scrollbar(self.grid_frame, orient="vertical")
        self.scroll_x = ttk.Scrollbar(self.grid_frame, orient="horizontal")
        self.tree = ttk.Treeview(
            self.grid_frame,
            show="headings",
            yscrollcommand=self.scroll_y.set,
            xscrollcommand=self.scroll_x.set,
        )
        self.scroll_y.pack(side="right", fill="y")
        self.scroll_x.pack(side="bottom", fill="x")
        self.scroll_y.config(command=self.tree.yview)
        self.scroll_x.config(command=self.tree.xview)
        self.tree.pack(fill="both", expand=True)

    def refresh_data(self):
        """Reload rows when this screen is opened from the dashboard."""
        self.load_rows()

    def on_table_change(self, _event=None):
        label = self.cb_table.get()
        self.current_table = self.table_map.get(label, "inletter")
        self.load_rows()

    def _rebuild_columns(self):
        meta = TABLE_REGISTRY[self.current_table]
        col_ids = [c[0] for c in meta["columns"]]
        self.tree["columns"] = col_ids
        for col_id, heading in meta["columns"]:
            self.tree.heading(col_id, text=heading)
            width = 80 if col_id.endswith("_id") or col_id == "file_id" else 120
            if col_id in ("title", "address", "remark", "attachment_path", "dept_to"):
                width = 200
            self.tree.column(col_id, width=width, anchor="w")
        return meta

    def load_rows(self):
        if not hasattr(self, "tree"):
            return
        self._rebuild_columns()
        self.tree.delete(*self.tree.get_children())
        for row in fetch_rows(self.current_table, self.current_user):
            self.tree.insert("", "end", values=row, iid=str(row[0]))

    def _get_selected_pk(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Selection", "အတန်းတစ်ခု ရွေးချယ်ပါ။")
            return None
        return self.tree.item(sel[0], "values")[0]

    def edit_row(self):
        # Prevent direct edit if the user lacks edit permission
        if not user_can(self.current_user, "can_edit_rows"):
            messagebox.showwarning("Permission", "You do not have permission to edit rows.")
            return
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Selection", "ပြင်ရန် အတန်းတစ်ခု ရွေးချယ်ပါ။")
            return
        values = self.tree.item(sel[0], "values")
        meta = TABLE_REGISTRY[self.current_table]
        pk = meta["pk"]
        editable = [(c, h) for c, h in meta["columns"] if c != pk]

        win = tk.Toplevel(self)
        win.title(f"Edit Row - {meta['label']}")
        win.geometry("520x400")
        win.grab_set()

        entries = []
        for i, (col_id, heading) in enumerate(editable):
            ttk.Label(win, text=f"{heading}:").grid(row=i, column=0, sticky="nw", padx=10, pady=5)
            val = values[i + 1] if values[i + 1] is not None else ""
            if col_id in ("remark", "address", "title", "dept_to"):
                ent = tk.Text(win, width=50, height=3)
                ent.insert("1.0", str(val))
                ent.grid(row=i, column=1, padx=10, pady=5)
            else:
                ent = ttk.Entry(win, width=50)
                ent.insert(0, str(val))
                ent.grid(row=i, column=1, padx=10, pady=5)
            entries.append((col_id, ent))

        def save():
            new_vals = []
            for col_id, ent in entries:
                if isinstance(ent, tk.Text):
                    new_vals.append(ent.get("1.0", tk.END).strip())
                else:
                    new_vals.append(ent.get().strip())
            if update_row(self.current_table, values[0], new_vals):
                messagebox.showinfo("Success", "အတန်း ပြင်ဆင်ပြီးပါပြီ။")
                win.destroy()
                self.load_rows()

        ttk.Button(win, text="Save Changes", command=save).grid(
            row=len(editable), column=1, sticky="e", padx=10, pady=15
        )

    def remove_row(self):
        pk_value = self._get_selected_pk()
        if pk_value is None:
            return
        if not messagebox.askyesno("Confirm", f"ID {pk_value} ကို ဖျက်ရန် သေချာပါသလား?"):
            return
        if delete_row(self.current_table, pk_value):
            messagebox.showinfo("Success", "အတန်း ဖျက်ပြီးပါပြီ။")
            self.load_rows()


# Backward-compatible alias
RowManageView = RoleManagementView
