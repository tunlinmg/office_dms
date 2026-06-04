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

def fetch_all_doctypes():
    conn = get_db_connection()
    if not conn: return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT file_id AS id, doc_type, remark FROM doc_type ORDER BY file_id DESC")
        return cursor.fetchall()
    except Exception as e:
        messagebox.showerror("Model Error", str(e))
        return []
    finally:
        conn.close()

def fetch_doctype_by_id(doc_id):
    conn = get_db_connection()
    if not conn: return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT file_id AS id, doc_type, remark FROM doc_type WHERE file_id = %s", (doc_id,))
        return cursor.fetchone()
    except Exception as e:
        messagebox.showerror("Model Error", str(e))
        return None
    finally:
        conn.close()

def update_doctype(doc_id, data):
    """data: (doc_type, remark)"""
    conn = get_db_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE doc_type SET doc_type = %s, remark = %s WHERE file_id = %s", (data[0], data[1], doc_id))
        conn.commit()
        return True
    except Exception as e:
        messagebox.showerror("Model Error", str(e))
        return False
    finally:
        conn.close()

def delete_doctype(doc_id):
    conn = get_db_connection()
    if not conn: return False
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM doc_type WHERE file_id = %s", (doc_id,))
        conn.commit()
        return True
    except Exception as e:
        messagebox.showerror("Model Error", str(e))
        return False
    finally:
        conn.close()
