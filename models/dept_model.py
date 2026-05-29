# models/dept_model.py
from config import get_db_connection
from tkinter import messagebox


def fetch_department_names():
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT dept_name FROM department WHERE dept_name IS NOT NULL "
            "AND dept_name != '' ORDER BY dept_name"
        )
        return [row[0] for row in cursor.fetchall()]
    except Exception:
        return []
    finally:
        conn.close()


def insert_dept(data):
    conn = get_db_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        query = "INSERT INTO department (dept_name, dept_type, dept_level, address, email, phone, remark) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(query, data)
        conn.commit()
        return True
    except Exception as e:
        messagebox.showerror("Model Error", str(e))
        return False
    finally:
        conn.close()