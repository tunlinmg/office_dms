# models/activity_log_model.py
import logging
import mysql.connector
from config import get_db_connection

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        filename="dms_errors.log",
        level=logging.ERROR,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def log_activity(user_id, username, action, detail=""):
    """Insert a single activity-log row. Fail silently so it never breaks the caller."""
    conn = get_db_connection()
    if not conn:
        return
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO user_activity_log (user_id, username, action, detail) VALUES (%s, %s, %s, %s)",
            (user_id, username, action, detail),
        )
        conn.commit()
    except Exception:
        logger.exception("Failed to write activity log for user %s", username)
    finally:
        conn.close()


def fetch_activity_logs(limit=500):
    """Return the most recent activity-log rows (newest first)."""
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT log_id, user_id, username, action, detail, created_at "
            "FROM user_activity_log ORDER BY created_at DESC LIMIT %s",
            (limit,),
        )
        return cursor.fetchall()
    except Exception:
        logger.exception("Failed to fetch activity logs")
        return []
    finally:
        conn.close()