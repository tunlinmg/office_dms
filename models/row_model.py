# models/row_model.py
from config import get_db_connection
from models.user_model import apply_department_sql
from tkinter import messagebox

TABLE_REGISTRY = {
    "inletter": {
        "label": "ဝင်စာ (Inletter)",
        "pk": "file_id",
        "columns": [
            ("file_id", "File ID"),
            ("letter_date", "Letter Date"),
            ("send_date", "Send Date"),
            ("letter_type", "Letter Type"),
            ("title", "Title"),
            ("dept_from", "Dept From"),
            ("recipient", "Recipient"),
            ("security_lvl", "Security"),
            ("urgency_lvl", "Urgency"),
            ("casefile_no", "Casefile No"),
            ("attachment_path", "Attachment"),
            ("remark", "Remark"),
            ("owner_department", "Owner Dept"),
        ],
    },
    "outletter": {
        "label": "ထွက်စာ (Outletter)",
        "pk": "file_id",
        "columns": [
            ("file_id", "File ID"),
            ("letter_date", "Letter Date"),
            ("letter_type", "Letter Type"),
            ("title", "Title"),
            ("dept_to", "Dept To"),
            ("security_lvl", "Security"),
            ("urgency_lvl", "Urgency"),
            ("casefile_no", "Casefile No"),
            ("attachment_path", "Attachment"),
            ("remark", "Remark"),
            ("owner_department", "Owner Dept"),
        ],
    },
    "doc_type": {
        "label": "စာတမ်းအမျိုးအစား (Doc Type)",
        "pk": "file_id",
        "columns": [
            ("file_id", "File ID"),
            ("doc_type", "Doc Type"),
            ("remark", "Remark"),
        ],
    },
    "action_entry": {
        "label": "လုပ်ငန်းစဉ် (Action)",
        "pk": "file_id",
        "columns": [
            ("file_id", "File ID"),
            ("action_type", "Action Type"),
            ("action_process", "Process"),
            ("sub_action", "Sub Action"),
            ("remark", "Remark"),
        ],
    },
    "department": {
        "label": "ဌာန (Department)",
        "pk": "file_id",
        "columns": [
            ("file_id", "File ID"),
            ("dept_name", "Dept Name"),
            ("dept_type", "Dept Type"),
            ("dept_level", "Dept Level"),
            ("address", "Address"),
            ("email", "Email"),
            ("phone", "Phone"),
            ("remark", "Remark"),
        ],
    },
}


def get_table_options():
    return [(key, meta["label"]) for key, meta in TABLE_REGISTRY.items()]


def _get_meta(table_name):
    if table_name not in TABLE_REGISTRY:
        raise ValueError(f"Unknown table: {table_name}")
    return TABLE_REGISTRY[table_name]


def fetch_rows(table_name, current_user=None):
    meta = _get_meta(table_name)
    col_names = [c[0] for c in meta["columns"]]
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cols = ", ".join(col_names)
        query = f"SELECT {cols} FROM {table_name} WHERE 1=1"
        params = []
        if table_name in ("inletter", "outletter") and current_user:
            query, params = apply_department_sql(current_user, query, params)
        query += f" ORDER BY {meta['pk']} DESC"
        cursor.execute(query, params)
        return cursor.fetchall()
    except Exception as e:
        messagebox.showerror("Model Error", str(e))
        return []
    finally:
        conn.close()


def update_row(table_name, pk_value, values):
    meta = _get_meta(table_name)
    pk = meta["pk"]
    editable = [c[0] for c in meta["columns"] if c[0] != pk]
    if len(values) != len(editable):
        messagebox.showerror("Model Error", "Column count mismatch.")
        return False
    conn = get_db_connection()
    if not conn:
        return False
    try:
        set_clause = ", ".join(f"{col}=%s" for col in editable)
        query = f"UPDATE {table_name} SET {set_clause} WHERE {pk}=%s"
        cursor = conn.cursor()
        cursor.execute(query, (*values, pk_value))
        conn.commit()
        return True
    except Exception as e:
        messagebox.showerror("Model Error", str(e))
        return False
    finally:
        conn.close()


def delete_row(table_name, pk_value):
    meta = _get_meta(table_name)
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {table_name} WHERE {meta['pk']} = %s", (pk_value,))
        conn.commit()
        return True
    except Exception as e:
        messagebox.showerror("Model Error", str(e))
        return False
    finally:
        conn.close()
