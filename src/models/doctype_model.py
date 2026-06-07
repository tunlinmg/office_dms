# models/doctype_model.py
import logging
from config import get_db_connection
from src.models.activity_log_model import log_activity

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(filename="dms_errors.log", level=logging.ERROR, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def insert_doctype(data, current_user=None):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        query = "INSERT INTO doc_type (doc_type, remark) VALUES (%s, %s)"
        cursor.execute(query, data)
        conn.commit()
        if current_user:
            doc_type = data[0] if len(data) > 0 else ""
            log_activity(
                current_user.get("user_id"), current_user.get("username"),
                "INSERT", f"Created doc type: {doc_type}",
            )
        return True
    except Exception as e:
        logger.exception("Could not insert doc type")
        return False
    finally:
        conn.close()


def fetch_all_doctypes():
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT file_id AS id, doc_type, remark FROM doc_type ORDER BY file_id DESC")
        return cursor.fetchall()
    except Exception as e:
        logger.exception("Could not fetch doc types")
        return []
    finally:
        conn.close()


def fetch_doctype_by_id(doc_id):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT file_id AS id, doc_type, remark FROM doc_type WHERE file_id = %s", (doc_id,))
        return cursor.fetchone()
    except Exception as e:
        logger.exception("Could not fetch doc type ID %s", doc_id)
        return None
    finally:
        conn.close()


def update_doctype(doc_id, data, current_user=None):
    """data: (doc_type, remark)"""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE doc_type SET doc_type = %s, remark = %s WHERE file_id = %s", (data[0], data[1], doc_id))
        conn.commit()
        if current_user:
            log_activity(
                current_user.get("user_id"), current_user.get("username"),
                "UPDATE", f"Updated doc type ID={doc_id}: {data[0]}",
            )
        return True
    except Exception as e:
        logger.exception("Could not update doc type ID %s", doc_id)
        return False
    finally:
        conn.close()


def delete_doctype(doc_id, current_user=None):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM doc_type WHERE file_id = %s", (doc_id,))
        conn.commit()
        if current_user:
            log_activity(
                current_user.get("user_id"), current_user.get("username"),
                "DELETE", f"Deleted doc type ID={doc_id}",
            )
        return True
    except Exception as e:
        logger.exception("Could not delete doc type ID %s", doc_id)
        return False
    finally:
        conn.close()