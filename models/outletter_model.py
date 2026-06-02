# models/outletter_model.py
from config import get_db_connection
from models.user_model import apply_department_sql
from tkinter import messagebox


def insert_outletter(data):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        query = """INSERT INTO outletter (
            letter_date, letter_type, title, dept_to, security_lvl, urgency_lvl,
            casefile_no, attachment_path, remark, owner_department
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(query, data)
        conn.commit()
        return True
    except Exception as e:
        messagebox.showerror("Model Error", str(e))
        return False
    finally:
        conn.close()


def fetch_outletters(current_user):
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        query = """SELECT file_id, letter_date, letter_type, title, dept_to, owner_department
                   FROM outletter WHERE 1=1"""
        params = []
        query, params = apply_department_sql(current_user, query, params)
        query += " ORDER BY file_id DESC"
        cursor.execute(query, params)
        return cursor.fetchall()
    except Exception as e:
        messagebox.showerror("Model Error", str(e))
        return []
    finally:
        conn.close()
