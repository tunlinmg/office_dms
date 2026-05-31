# config.py
import hashlib
import mysql.connector
from tkinter import messagebox

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",  # မိမိ MySQL Password ထည့်ပါ
    "database": "office_doc_db",
    "charset": "utf8mb4"
}

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

def init_db():
    try:
        # Database မရှိလျှင် ဆောက်ရန်
        conn = mysql.connector.connect(host=DB_CONFIG["host"], user=DB_CONFIG["user"], password=DB_CONFIG["password"])
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.close()
        
        # Table များ ဆောက်ရန်
        conn = get_db_connection()
        if not conn: return
        cursor = conn.cursor()
        
        # Inletter Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS inletter (
                file_id INT AUTO_INCREMENT PRIMARY KEY, letter_date VARCHAR(50), send_date VARCHAR(50),
                letter_type VARCHAR(100), title TEXT, dept_from VARCHAR(255), recipient VARCHAR(255),
                security_lvl VARCHAR(50), urgency_lvl VARCHAR(50), casefile_no VARCHAR(100),
                attachment_path TEXT, remark TEXT,
                owner_department VARCHAR(255) DEFAULT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        # Outletter Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS outletter (
                file_id INT AUTO_INCREMENT PRIMARY KEY, letter_date VARCHAR(50), letter_type VARCHAR(100),
                title TEXT, dept_to TEXT, security_lvl VARCHAR(50), urgency_lvl VARCHAR(50),
                casefile_no VARCHAR(100), attachment_path TEXT, remark TEXT,
                owner_department VARCHAR(255) DEFAULT NULL
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        # Doc Type Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS doc_type (
                file_id INT AUTO_INCREMENT PRIMARY KEY, doc_type VARCHAR(100), remark TEXT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        # Action Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS action_entry (
                file_id INT AUTO_INCREMENT PRIMARY KEY, action_type VARCHAR(100), action_process VARCHAR(100), sub_action VARCHAR(255), remark TEXT
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        # Department Table
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

        # Roles Table (permissions)
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
                can_view_reports TINYINT(1) DEFAULT 1
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

        from models.role_model import seed_default_roles
        seed_default_roles(cursor)

        # Users Table
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
        # Migrate older tables
        for col_sql in (
            "ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "ALTER TABLE users ADD COLUMN full_name VARCHAR(255)",
            "ALTER TABLE users ADD COLUMN email VARCHAR(255)",
            "ALTER TABLE users ADD COLUMN department VARCHAR(255)",
            "ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'user'",
            "ALTER TABLE users ADD COLUMN is_active TINYINT(1) DEFAULT 1",
            "ALTER TABLE inletter ADD COLUMN owner_department VARCHAR(255) DEFAULT NULL",
            "ALTER TABLE outletter ADD COLUMN owner_department VARCHAR(255) DEFAULT NULL",
        ):
            try:
                cursor.execute(col_sql)
            except mysql.connector.Error:
                pass

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