# models/doctype_model.py
from config import get_db_connection
from tkinter import messagebox

def insert_doctype(data):
    conn = get_db_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        query = "INSERT INTO doc_type (doc_type, remark) VALUES (%s, %s)"
        cursor.execute(query, data)
        conn.commit()
        return True
    except Exception as e:
        messagebox.showerror("Model Error", str(e))
        return False
    finally:
        conn.close()