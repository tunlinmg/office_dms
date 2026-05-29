# models/action_model.py
from config import get_db_connection
from tkinter import messagebox

def insert_action(data):
    conn = get_db_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        query = "INSERT INTO action_entry (action_type, action_process, sub_action, remark) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, data)
        conn.commit()
        return True
    except Exception as e:
        messagebox.showerror("Model Error", str(e))
        return False
    finally:
        conn.close()