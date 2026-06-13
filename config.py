# config.py
import hashlib
import decimal
import json
import os
import mysql.connector
from tkinter import messagebox

# Default database configuration values
_DEFAULT_DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "office_doc_db",
    "charset": "utf8mb4",
}

# Path to the local JSON config file (same directory as this script)
_DB_CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db_config.json")


def _load_db_config():
    """Load database configuration from db_config.json.

    If the file does not exist, create it with default values and return defaults.
    If the file exists but is malformed, fall back to defaults and overwrite.

    Returns:
        dict: Database configuration with keys: host, user, password, database, charset.
    """
    if not os.path.exists(_DB_CONFIG_FILE):
        _save_db_config(_DEFAULT_DB_CONFIG)
        return dict(_DEFAULT_DB_CONFIG)

    try:
        with open(_DB_CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        config = {}
        for key in _DEFAULT_DB_CONFIG:
            config[key] = data.get(key, _DEFAULT_DB_CONFIG[key])
        return config
    except (json.JSONDecodeError, IOError):
        _save_db_config(_DEFAULT_DB_CONFIG)
        return dict(_DEFAULT_DB_CONFIG)


def _save_db_config(config_dict):
    """Save database configuration to db_config.json.

    Args:
        config_dict (dict): Configuration dictionary to persist.
    """
    try:
        with open(_DB_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=4, ensure_ascii=False)
    except IOError as err:
        messagebox.showerror("Config Save Error", f"Could not save db_config.json:\n{err}")


def save_db_config(config_dict):
    """Public helper: save config to JSON and reload the in-memory DB_CONFIG.

    Args:
        config_dict (dict): Configuration dictionary to persist.
    """
    _save_db_config(config_dict)
    global DB_CONFIG
    DB_CONFIG = _load_db_config()


# Active in-memory configuration (loaded at import time)
DB_CONFIG = _load_db_config()

DEFAULT_DEPARTMENTS = [f"Department-{i}" for i in range(1, 11)]


def hash_password(password, username=""):
    raw = f"{username}:{password}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def get_db_connection():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        messagebox.showerror("Database Connection Error", f"Error: {err}")
        return None


def get_server_connection():
    try:
        server_config = {
            "host": DB_CONFIG["host"],
            "user": DB_CONFIG["user"],
            "password": DB_CONFIG["password"],
            "charset": DB_CONFIG.get("charset", "utf8mb4"),
            "use_unicode": True,
        }
        return mysql.connector.connect(**server_config)
    except mysql.connector.Error as err:
        messagebox.showerror("Database Connection Error", f"Error: {err}")
        return None


def _escape_sql_value(value):
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float, decimal.Decimal)):
        return str(value)
    text = str(value)
    text = text.replace("\\", "\\\\").replace("'", "\\'").replace("\n", "\\n").replace("\r", "\\r")
    return f"'{text}'"


def backup_database(backup_path):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        if not tables:
            return False

        with open(backup_path, "w", encoding="utf-8") as backup_file:
            backup_file.write(
                f"CREATE DATABASE IF NOT EXISTS `{DB_CONFIG['database']}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;\n"
                f"USE `{DB_CONFIG['database']}`;\n\n"
            )

            for table in tables:
                cursor.execute(f"SHOW CREATE TABLE `{table}`")
                create_row = cursor.fetchone()
                if not create_row or len(create_row) < 2:
                    continue
                backup_file.write(f"{create_row[1]};\n\n")
                cursor.execute(f"SELECT * FROM `{table}`")
                rows = cursor.fetchall()
                if not rows:
                    continue
                columns = [desc[0] for desc in cursor.description]
                cols_sql = ", ".join([f"`{col}`" for col in columns])
                for row in rows:
                    values = ", ".join([_escape_sql_value(value) for value in row])
                    backup_file.write(f"INSERT INTO `{table}` ({cols_sql}) VALUES ({values});\n")
                backup_file.write("\n")
        return True
    except Exception as err:
        messagebox.showerror("Backup Failed", f"Could not create backup: {err}")
        return False
    finally:
        conn.close()


def restore_database(backup_path):
    conn = get_server_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        with open(backup_path, "r", encoding="utf-8") as backup_file:
            sql = backup_file.read()
        for result in cursor.execute(sql, multi=True):
            pass
        conn.commit()
        return True
    except Exception as err:
        messagebox.showerror("Restore Failed", f"Could not restore database: {err}")
        return False
    finally:
        conn.close()


def delete_database():
    conn = get_server_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(f"DROP DATABASE IF EXISTS `{DB_CONFIG['database']}`")
        conn.commit()
        conn.close()
        init_db()
        return True
    except Exception as err:
        messagebox.showerror("Delete Failed", f"Could not delete database: {err}")
        return False
    finally:
        if conn.is_connected():
            conn.close()


def init_db():
    try:
        conn = mysql.connector.connect(host=DB_CONFIG["host"], user=DB_CONFIG["user"], password=DB_CONFIG["password"])
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.close()

        conn = get_db_connection()
        if not conn:
            return
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inletter (
                file_id INT AUTO_INCREMENT PRIMARY KEY, letter_date VARCHAR(50), send_date VARCHAR(50),
                letter_type VARCHAR(100), title TEXT, dept_from VARCHAR(255), recipient VARCHAR(255),
                security_lvl VARCHAR(50), urgency_lvl VARCHAR(50), casefile_no VARCHAR(100),
                attachment_path TEXT, remark TEXT,
                owner_department VARCHAR(255) DEFAULT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS outletter (
                file_id INT AUTO_INCREMENT PRIMARY KEY, letter_date VARCHAR(50), letter_type VARCHAR(100),
                title TEXT, dept_to TEXT, security_lvl VARCHAR(50), urgency_lvl VARCHAR(50),
                casefile_no VARCHAR(100), attachment_path TEXT, remark TEXT,
                owner_department VARCHAR(255) DEFAULT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS doc_type (
                file_id INT AUTO_INCREMENT PRIMARY KEY, doc_type VARCHAR(100), remark TEXT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS action_entry (
                file_id INT AUTO_INCREMENT PRIMARY KEY, action_type VARCHAR(100), action_process VARCHAR(100), sub_action VARCHAR(255), remark TEXT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS department (
                file_id INT AUTO_INCREMENT PRIMARY KEY, dept_name VARCHAR(255), dept_type VARCHAR(100), dept_level VARCHAR(100),
                address TEXT, email VARCHAR(100), phone VARCHAR(50), remark TEXT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        for dept_name in DEFAULT_DEPARTMENTS:
            cursor.execute("SELECT file_id FROM department WHERE dept_name = %s", (dept_name,))
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO department (dept_name, dept_type, dept_level, address, email, phone, remark) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (dept_name, "General", "Level 1", "", "", "", "Seeded default department."),
                )

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                role_id INT AUTO_INCREMENT PRIMARY KEY,
                role_name VARCHAR(50) NOT NULL UNIQUE,
                description VARCHAR(255),
                can_manage_users TINYINT(1) DEFAULT 0,
                can_manage_roles TINYINT(1) DEFAULT 0,
                can_delete_rows TINYINT(1) DEFAULT 0,
                can_edit_rows TINYINT(1) DEFAULT 0,
                can_entry_forms TINYINT(1) DEFAULT 1,
                can_view_reports TINYINT(1) DEFAULT 1,
                can_view_user_logs TINYINT(1) DEFAULT 0
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS department_role_permissions (
                perm_id INT AUTO_INCREMENT PRIMARY KEY,
                role_name VARCHAR(50) NOT NULL,
                department VARCHAR(255) NOT NULL,
                can_view_inletter TINYINT(1) DEFAULT 0,
                can_write_inletter TINYINT(1) DEFAULT 0,
                can_view_outletter TINYINT(1) DEFAULT 0,
                can_write_outletter TINYINT(1) DEFAULT 0,
                UNIQUE KEY uniq_role_dept (role_name, department)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(100) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(255),
                email VARCHAR(255),
                department VARCHAR(255),
                role VARCHAR(50) DEFAULT 'user',
                is_active TINYINT(1) DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_activity_log (
                log_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                username VARCHAR(100),
                action VARCHAR(255) NOT NULL,
                detail TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_user_id (user_id),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS modules_registry (
                id INTEGER PRIMARY KEY AUTO_INCREMENT,
                module_name TEXT,
                file_name TEXT,
                status INTEGER DEFAULT 1,
                description TEXT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        for col_sql in (
            "ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE users ADD COLUMN full_name VARCHAR(255)",
            "ALTER TABLE users ADD COLUMN email VARCHAR(255)",
            "ALTER TABLE users ADD COLUMN department VARCHAR(255)",
            "ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'user'",
            "ALTER TABLE users ADD COLUMN is_active TINYINT(1) DEFAULT 1",
            "ALTER TABLE inletter ADD COLUMN owner_department VARCHAR(255) DEFAULT NULL",
            "ALTER TABLE outletter ADD COLUMN owner_department VARCHAR(255) DEFAULT NULL",
            "ALTER TABLE roles ADD COLUMN can_view_user_logs TINYINT(1) DEFAULT 0",
        ):
            try:
                cursor.execute(col_sql)
            except mysql.connector.Error:
                pass

        from src.models.role_model import seed_default_roles
        seed_default_roles(cursor)

        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO users (username, password_hash, full_name, email, department, role, is_active) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (
                    "admin",
                    hash_password("admin123", "admin"),
                    "System Administrator",
                    "admin@office.gov",
                    "All Departments",
                    "admin",
                    1,
                ),
            )
        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"Init DB Error: {err}")