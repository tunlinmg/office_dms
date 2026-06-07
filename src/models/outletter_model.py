# models/outletter_model.py
import logging
from config import get_db_connection
from src.models.user_model import apply_department_sql
from src.models.activity_log_model import log_activity

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(filename="dms_errors.log", level=logging.ERROR, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def insert_outletter(data, current_user=None):
    """Insert a new outletter record into the database."""
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
        if current_user:
            title = data[2] if len(data) > 2 else ""
            log_activity(
                current_user.get("user_id"), current_user.get("username"),
                "INSERT", f"Created outletter: {title}",
            )
        return True
    except Exception as e:
        logger.exception("Could not insert outletter")
        return False
    finally:
        conn.close()


def fetch_outletters(current_user):
    """Fetch all outletter records visible to the current user."""
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
        logger.exception("Could not fetch outletters")
        return []
    finally:
        conn.close()


def fetch_outletter_by_id(file_id):
    """Fetch a single outletter record by its primary key."""
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        query = """SELECT file_id, letter_date, letter_type, title, dept_to,
                          security_lvl, urgency_lvl, casefile_no,
                          attachment_path, remark, owner_department
                   FROM outletter WHERE file_id = %s"""
        cursor.execute(query, (file_id,))
        return cursor.fetchone()
    except Exception as e:
        logger.exception("Could not fetch outletter ID %s", file_id)
        return None
    finally:
        conn.close()


def update_outletter(file_id, data, current_user=None):
    """Update an existing outletter record."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        query = """UPDATE outletter SET
                    letter_date = %s, letter_type = %s, title = %s,
                    dept_to = %s, security_lvl = %s, urgency_lvl = %s,
                    casefile_no = %s, attachment_path = %s, remark = %s,
                    owner_department = %s
                   WHERE file_id = %s"""
        cursor.execute(query, data + (file_id,))
        conn.commit()
        if current_user:
            title = data[2] if len(data) > 2 else ""
            log_activity(
                current_user.get("user_id"), current_user.get("username"),
                "UPDATE", f"Updated outletter ID={file_id}: {title}",
            )
        return True
    except Exception as e:
        logger.exception("Could not update outletter ID %s", file_id)
        return False
    finally:
        conn.close()


def delete_outletter(file_id, current_user=None):
    """Delete an outletter record by its primary key."""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM outletter WHERE file_id = %s", (file_id,))
        conn.commit()
        if current_user:
            log_activity(
                current_user.get("user_id"), current_user.get("username"),
                "DELETE", f"Deleted outletter ID={file_id}",
            )
        return True
    except Exception as e:
        logger.exception("Could not delete outletter ID %s", file_id)
        return False
    finally:
        conn.close()