# models/module_manager.py
import logging
from config import get_db_connection

logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        filename="dms_errors.log",
        level=logging.ERROR,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def register_new_module(name, file_name, desc):
    """Insert a new module into the modules_registry table.

    Args:
        name: The display name of the module.
        file_name: The Python file name of the module.
        desc: A short description of the module.
    Returns:
        True on success, False on failure.
    """
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO modules_registry (module_name, file_name, status, description) "
            "VALUES (%s, %s, %s, %s)",
            (name, file_name, 1, desc),
        )
        conn.commit()
        return True
    except Exception as e:
        logger.exception("Could not register module '%s'", name)
        return False
    finally:
        conn.close()


def toggle_module_status(module_id, new_status):
    """Update the status of a module (1 for active, 0 for inactive).

    Args:
        module_id: The ID of the module to update.
        new_status: 1 for active, 0 for inactive.
    Returns:
        True on success, False on failure.
    """
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE modules_registry SET status = %s WHERE id = %s",
            (new_status, module_id),
        )
        conn.commit()
        return True
    except Exception as e:
        logger.exception("Could not toggle status for module ID %s", module_id)
        return False
    finally:
        conn.close()


def delete_module_from_registry(module_id):
    """Delete a module record from the registry.

    Args:
        module_id: The ID of the module to delete.
    Returns:
        True on success, False on failure.
    """
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM modules_registry WHERE id = %s",
            (module_id,),
        )
        conn.commit()
        return True
    except Exception as e:
        logger.exception("Could not delete module ID %s", module_id)
        return False
    finally:
        conn.close()


def get_all_modules():
    """Return a list of all registered modules.

    Returns:
        A list of dicts with keys: id, module_name, file_name, status, description.
        Returns an empty list on failure.
    """
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, module_name, file_name, status, description "
            "FROM modules_registry ORDER BY id ASC"
        )
        return cursor.fetchall()
    except Exception as e:
        logger.exception("Could not fetch modules")
        return []
    finally:
        conn.close()