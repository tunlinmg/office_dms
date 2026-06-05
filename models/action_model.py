# models/action_model.py
from config import get_db_connection
from tkinter import messagebox
from models.user_model import apply_department_sql
from models.activity_log_model import log_activity


def _ensure_reference_columns(cursor):
    # Add ref_table and ref_id columns to action_entry if they don't exist
    try:
        cursor.execute("ALTER TABLE action_entry ADD COLUMN ref_table VARCHAR(50) DEFAULT NULL")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE action_entry ADD COLUMN ref_id INT DEFAULT NULL")
    except Exception:
        pass


def insert_action(data, current_user=None):
    """Insert an action entry.

    Expected data: (action_type, action_process, sub_action, remark, ref_table, ref_id)
    The last two fields are optional (can be None) and will be stored in `ref_table`/`ref_id`.
    current_user: the logged-in user dict (for activity logging)
    """
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        # Ensure columns exist for referencing letters
        _ensure_reference_columns(cursor)

        # Prepare insert statement depending on whether references provided
        if len(data) >= 6 and data[4] is not None and data[5] is not None:
            query = "INSERT INTO action_entry (action_type, action_process, sub_action, remark, ref_table, ref_id) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(query, data)
        else:
            query = "INSERT INTO action_entry (action_type, action_process, sub_action, remark) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, data[:4])
        conn.commit()
        if current_user:
            action_type = data[0] if len(data) > 0 else ""
            log_activity(
                current_user.get("user_id"), current_user.get("username"),
                "INSERT", f"Created action: {action_type}",
            )
        return True
    except Exception as e:
        messagebox.showerror("Model Error", str(e))
        return False
    finally:
        conn.close()


def _fetch_latest_action_status(cursor, ref_table, ref_id):
    try:
        cursor.execute(
            "SELECT action_process, action_type, sub_action FROM action_entry WHERE ref_table = %s AND ref_id = %s ORDER BY file_id DESC LIMIT 1",
            (ref_table, ref_id),
        )
        row = cursor.fetchone()
        if row:
            proc, act_type, sub_act = row
            parts = [str(proc or "")]
            if act_type:
                parts.append(str(act_type))
            if sub_act:
                parts.append(str(sub_act))
            return " | ".join([p for p in parts if p])
    except Exception:
        pass
    return ""


def fetch_letters(current_user=None):
    """Fetch recent letters from inletter and outletter for selection.

    Returns list of tuples: (display_text, table_name, file_id, action_status)
    """
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        results = []
        _ensure_reference_columns(cursor)

        # Inletters
        try:
            query = "SELECT file_id, title, letter_date FROM inletter WHERE 1=1"
            params = []
            if current_user:
                query, params = apply_department_sql(current_user, query, params, column="owner_department")
            query += " ORDER BY file_id DESC LIMIT 200"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            for r in rows:
                fid, title, ldate = r[0], (r[1] or "")[:120], (r[2] or "")
                status = _fetch_latest_action_status(cursor, "inletter", fid)
                disp = f"Inletter {fid} - {title} ({ldate})"
                results.append((disp, "inletter", fid, status))
        except Exception:
            pass

        # Outletters
        try:
            query = "SELECT file_id, title, letter_date FROM outletter WHERE 1=1"
            params = []
            if current_user:
                query, params = apply_department_sql(current_user, query, params, column="owner_department")
            query += " ORDER BY file_id DESC LIMIT 200"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            for r in rows:
                fid, title, ldate = r[0], (r[1] or "")[:120], (r[2] or "")
                status = _fetch_latest_action_status(cursor, "outletter", fid)
                disp = f"Outletter {fid} - {title} ({ldate})"
                results.append((disp, "outletter", fid, status))
        except Exception:
            pass

        return results
    except Exception as e:
        messagebox.showerror("Model Error", str(e))
        return []
    finally:
        conn.close()