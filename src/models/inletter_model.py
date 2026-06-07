# models/inletter_model.py
import logging
from config import get_db_connection
from src.models.user_model import apply_department_sql
from src.models.activity_log_model import log_activity

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(filename="dms_errors.log", level=logging.ERROR, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def insert_inletter(data, current_user=None):
    """Insert a new inletter record into the database."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        query = """INSERT INTO inletter (
            letter_date, send_date, letter_type, title, dept_from, recipient,
            security_lvl, urgency_lvl, casefile_no, attachment_path, remark, owner_department
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        cursor.execute(query, data)
        conn.commit()
        if current_user:
            title = data[2] if len(data) > 2 else ""
            log_activity(
                current_user.get("user_id"), current_user.get("username"),
                "INSERT", f"Created inletter: {title}",
            )
        return True
    except Exception as e:
        logger.exception("Could not insert inletter")
        return False
    finally:
        conn.close()


def fetch_inletters(current_user):
    """Fetch all inletter records visible to the current user."""
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        query = """SELECT file_id, letter_date, send_date, letter_type, title,
                          dept_from, recipient, owner_department
                   FROM inletter WHERE 1=1"""
        params = []
        query, params = apply_department_sql(current_user, query, params)
        query += " ORDER BY file_id DESC"
        cursor.execute(query, params)
        return cursor.fetchall()
    except Exception as e:
        logger.exception("Could not fetch inletters")
        return []
    finally:
        conn.close()


def fetch_inletter_by_id(file_id):
    """Fetch a single inletter record by its primary key."""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        query = """SELECT file_id, letter_date, send_date, letter_type, title,
                          dept_from, recipient, security_lvl, urgency_lvl,
                          casefile_no, attachment_path, remark, owner_department
                   FROM inletter WHERE file_id = %s"""
        cursor.execute(query, (file_id,))
        return cursor.fetchone()
    except Exception as e:
        logger.exception("Could not fetch inletter ID %s", file_id)
        return None
    finally:
        conn.close()


def update_inletter(file_id, data, current_user=None):
    """Update an existing inletter record."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        query = """UPDATE inletter SET
                    letter_date = %s, send_date = %s, letter_type = %s,
                    title = %s, dept_from = %s, recipient = %s,
                    security_lvl = %s, urgency_lvl = %s, casefile_no = %s,
                    attachment_path = %s, remark = %s, owner_department = %s
                   WHERE file_id = %s"""
        cursor.execute(query, data + (file_id,))
        conn.commit()
        if current_user:
            title = data[2] if len(data) > 2 else ""
            log_activity(
                current_user.get("user_id"), current_user.get("username"),
                "UPDATE", f"Updated inletter ID={file_id}: {title}",
            )
        return True
    except Exception as e:
        logger.exception("Could not update inletter ID %s", file_id)
        return False
    finally:
        conn.close()


def delete_inletter(file_id, current_user=None):
    """Delete an inletter record by its primary key."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM inletter WHERE file_id = %s", (file_id,))
        conn.commit()
        if current_user:
            log_activity(
                current_user.get("user_id"), current_user.get("username"),
                "DELETE", f"Deleted inletter ID={file_id}",
            )
        return True
    except Exception as e:
        logger.exception("Could not delete inletter ID %s", file_id)
        return False
    finally:
        conn.close()