# models/user_model.py
import mysql.connector
from config import get_db_connection, hash_password
from models.role_model import get_permissions_for_role, get_role_names
from tkinter import messagebox


def is_admin(user):
    return bool(user and user.get("role") == "admin")


def get_user_department(user):
    return (user or {}).get("department") or ""


def apply_department_sql(user, query, params, column="owner_department"):
    """Append AND clause so non-admin users only see their department's rows."""
    if is_admin(user):
        return query, params
    dept = get_user_department(user)
    if not dept:
        query += " AND 1=0"
        return query, params
    query += f" AND {column} = %s"
    params.append(dept)
    return query, params


def authenticate(username, password):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT user_id, username, full_name, email, department, role, is_active, password_hash "
            "FROM users WHERE username = %s",
            (username.strip(),),
        )
        user = cursor.fetchone()
        if not user:
            return None
        if not user["is_active"]:
            return None
        if user["password_hash"] != hash_password(password, username.strip()):
            return None
        user.pop("password_hash", None)
        user["email"] = user.get("email") or ""
        user["department"] = user.get("department") or ""
        user["permissions"] = get_permissions_for_role(user.get("role", "user"))
        return user
    except Exception as e:
        messagebox.showerror("Model Error", str(e))
        return None
    finally:
        conn.close()


def fetch_all_users():
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT user_id, username, full_name, email, department, role, is_active, created_at "
                "FROM users ORDER BY user_id ASC"
            )
        except mysql.connector.Error:
            cursor.execute(
                "SELECT user_id, username, full_name, role, is_active "
                "FROM users ORDER BY user_id ASC"
            )
        rows = cursor.fetchall()
        for row in rows:
            row.setdefault("created_at", "")
            row.setdefault("email", "")
            row.setdefault("department", "")
            row["full_name"] = row.get("full_name") or ""
            row["role"] = row.get("role") or "user"
            row["is_active"] = 1 if row.get("is_active") else 0
        return rows
    except Exception as e:
        messagebox.showerror("Model Error", f"Could not load users: {e}")
        return []
    finally:
        conn.close()


def insert_user(username, password, full_name, email, department, role, is_active=1):
    valid_roles = get_role_names()
    if role not in valid_roles:
        messagebox.showerror("Model Error", f"Invalid role '{role}'.")
        return False
    if not department.strip() and role != "admin":
        messagebox.showwarning("Validation", "Department is required for non-admin users.")
        return False
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password_hash, full_name, email, department, role, is_active) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (
                username.strip(),
                hash_password(password, username.strip()),
                full_name.strip(),
                email.strip(),
                department.strip(),
                role,
                is_active,
            ),
        )
        conn.commit()
        return True
    except Exception as e:
        messagebox.showerror("Model Error", str(e))
        return False
    finally:
        conn.close()


def update_user(user_id, username, full_name, email, department, role, is_active, password=None):
    valid_roles = get_role_names()
    if role not in valid_roles:
        messagebox.showerror("Model Error", f"Invalid role '{role}'.")
        return False
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        if password:
            cursor.execute(
                "UPDATE users SET username=%s, password_hash=%s, full_name=%s, email=%s, "
                "department=%s, role=%s, is_active=%s WHERE user_id=%s",
                (
                    username.strip(),
                    hash_password(password, username.strip()),
                    full_name.strip(),
                    email.strip(),
                    department.strip(),
                    role,
                    is_active,
                    user_id,
                ),
            )
        else:
            cursor.execute(
                "UPDATE users SET username=%s, full_name=%s, email=%s, department=%s, "
                "role=%s, is_active=%s WHERE user_id=%s",
                (
                    username.strip(),
                    full_name.strip(),
                    email.strip(),
                    department.strip(),
                    role,
                    is_active,
                    user_id,
                ),
            )
        conn.commit()
        return True
    except Exception as e:
        messagebox.showerror("Model Error", str(e))
        return False
    finally:
        conn.close()


def update_user_role(user_id, role):
    valid_roles = get_role_names()
    if role not in valid_roles:
        messagebox.showerror("Model Error", f"Invalid role '{role}'.")
        return False
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE user_id = %s", (user_id,))
        if not cursor.fetchone():
            messagebox.showerror("Model Error", f"User ID {user_id} not found.")
            return False
        cursor.execute("UPDATE users SET role=%s WHERE user_id=%s", (role, user_id))
        conn.commit()
        return True
    except Exception as e:
        messagebox.showerror("Model Error", str(e))
        return False
    finally:
        conn.close()


def delete_user(user_id, current_user_id):
    if user_id == current_user_id:
        messagebox.showwarning("Delete Blocked", "သင့်အကောင့်ကို ဖျက်၍မရပါ။")
        return False
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin' AND is_active = 1")
        admin_count = cursor.fetchone()[0]
        cursor.execute("SELECT role FROM users WHERE user_id = %s", (user_id,))
        row = cursor.fetchone()
        if row and row[0] == "admin" and admin_count <= 1:
            messagebox.showwarning("Delete Blocked", "နောက်ဆုံး Admin အကောင့်ကို ဖျက်၍မရပါ။")
            return False
        cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        conn.commit()
        return True
    except Exception as e:
        messagebox.showerror("Model Error", str(e))
        return False
    finally:
        conn.close()
