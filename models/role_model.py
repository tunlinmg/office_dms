# models/role_model.py
import mysql.connector
from config import get_db_connection
from tkinter import messagebox

PERMISSION_KEYS = (
    "can_manage_users",
    "can_manage_roles",
    "can_delete_rows",
    "can_edit_rows",
    "can_entry_forms",
    "can_view_reports",
)

PERMISSION_LABELS = {
    "can_manage_users": "Manage Users",
    "can_manage_roles": "Manage Roles",
    "can_delete_rows": "Delete Data Rows",
    "can_edit_rows": "Edit Data Rows",
    "can_entry_forms": "Entry Forms (In/Out letter, etc.)",
    "can_view_reports": "Query / Reports",
}

DEPT_PERMISSION_KEYS = (
    "can_view_inletter",
    "can_write_inletter",
    "can_view_outletter",
    "can_write_outletter",
)

DEPT_PERMISSION_LABELS = {
    "can_view_inletter": "View Inletter",
    "can_write_inletter": "Write Inletter",
    "can_view_outletter": "View Outletter",
    "can_write_outletter": "Write Outletter",
}

DEFAULT_ROLES = [
    {
        "role_name": "admin",
        "description": "Full system administrator",
        "can_manage_users": 1,
        "can_manage_roles": 1,
        "can_delete_rows": 1,
        "can_edit_rows": 1,
        "can_entry_forms": 1,
        "can_view_reports": 1,
    },
    {
        "role_name": "user",
        "description": "Standard office staff",
        "can_manage_users": 0,
        "can_manage_roles": 0,
        "can_delete_rows": 0,
        "can_edit_rows": 1,
        "can_entry_forms": 1,
        "can_view_reports": 1,
    },
    {
        "role_name": "viewer",
        "description": "Read-only access to reports",
        "can_manage_users": 0,
        "can_manage_roles": 0,
        "can_delete_rows": 0,
        "can_edit_rows": 0,
        "can_entry_forms": 0,
        "can_view_reports": 1,
    },
]


def _row_to_permissions(row):
    if not row:
        return {k: False for k in PERMISSION_KEYS}
    return {k: bool(row.get(k, 0)) for k in PERMISSION_KEYS}


def user_can(user, permission_key):
    if not user:
        return False
    perms = user.get("permissions")
    if perms:
        return bool(perms.get(permission_key, False))
    return user.get("role") == "admin"


def _dept_row_to_permissions(row):
    if not row:
        return {k: False for k in DEPT_PERMISSION_KEYS}
    return {k: bool(row.get(k, 0)) for k in DEPT_PERMISSION_KEYS}


def fetch_department_permissions(role_name, departments):
    if isinstance(departments, str):
        departments = [departments]
    if not departments:
        return {k: False for k in DEPT_PERMISSION_KEYS}
    conn = get_db_connection()
    if not conn:
        return {k: False for k in DEPT_PERMISSION_KEYS}
    try:
        cursor = conn.cursor(dictionary=True)
        if len(departments) == 1:
            cols = ", ".join(DEPT_PERMISSION_KEYS)
            cursor.execute(
                f"SELECT {cols} FROM department_role_permissions WHERE role_name = %s AND department = %s",
                (role_name, departments[0]),
            )
            return _dept_row_to_permissions(cursor.fetchone())
        placeholders = ", ".join(["%s"] * len(departments))
        cols = ", ".join(DEPT_PERMISSION_KEYS)
        cursor.execute(
            f"SELECT {cols} FROM department_role_permissions WHERE role_name = %s AND department IN ({placeholders})",
            [role_name] + departments,
        )
        rows = cursor.fetchall()
        if not rows or len(rows) < len(departments):
            return {k: False for k in DEPT_PERMISSION_KEYS}
        common = {k: True for k in DEPT_PERMISSION_KEYS}
        for row in rows:
            for key in DEPT_PERMISSION_KEYS:
                common[key] = common[key] and bool(row.get(key, 0))
        return common
    except Exception as e:
        messagebox.showerror("Model Error", str(e))
        return {k: False for k in DEPT_PERMISSION_KEYS}
    finally:
        conn.close()


def fetch_all_department_role_permissions():
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cols = ", ".join(["role_name", "department"] + list(DEPT_PERMISSION_KEYS))
        cursor.execute(f"SELECT {cols} FROM department_role_permissions ORDER BY role_name, department")
        return cursor.fetchall()
    except Exception as e:
        messagebox.showerror("Model Error", f"Could not load department role permissions: {e}")
        return []
    finally:
        conn.close()


def _dept_permission_type(row):
    if not row:
        return "None"
    write = bool(row.get("can_write_inletter") or row.get("can_write_outletter"))
    view = bool(row.get("can_view_inletter") or row.get("can_view_outletter"))
    if write:
        return "Write"
    if view:
        return "View Only"
    return "None"


def fetch_role_department_summaries():
    rows = fetch_all_department_role_permissions()
    summaries = {}
    for row in rows:
        role = row.get("role_name")
        if role not in summaries:
            summaries[role] = {
                "departments": [],
                "permission_types": set(),
            }
        summaries[role]["departments"].append(row.get("department") or "")
        summaries[role]["permission_types"].add(_dept_permission_type(row))
    result = {}
    for role, info in summaries.items():
        perms = info["permission_types"]
        if not perms:
            perm_label = "None"
        elif len(perms) == 1:
            perm_label = next(iter(perms))
        else:
            perm_label = "Mixed"
        result[role] = {
            "departments": ", ".join(sorted([d for d in info["departments"] if d])),
            "dept_permissions": perm_label,
        }
    return result


def save_department_permissions(role_name, departments, permissions):
    if isinstance(departments, str):
        departments = [departments]
    if not departments:
        return False
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cols = ", ".join(DEPT_PERMISSION_KEYS)
        placeholders = ", ".join(["%s"] * len(DEPT_PERMISSION_KEYS))
        set_clause = ", ".join([f"{k}=VALUES({k})" for k in DEPT_PERMISSION_KEYS])
        query = (
            f"INSERT INTO department_role_permissions (role_name, department, {cols}) VALUES (%s, %s, {placeholders}) "
            f"ON DUPLICATE KEY UPDATE {set_clause}"
        )
        vals = [1 if permissions.get(k) else 0 for k in DEPT_PERMISSION_KEYS]
        params = [[role_name, department] + vals for department in departments]
        cursor.executemany(query, params)
        conn.commit()
        return True
    except Exception as e:
        messagebox.showerror("Model Error", str(e))
        return False
    finally:
        conn.close()


def fetch_all_roles():
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor(dictionary=True)
        cols = ", ".join(["role_id", "role_name", "description"] + list(PERMISSION_KEYS))
        cursor.execute(f"SELECT {cols} FROM roles ORDER BY role_id")
        return cursor.fetchall()
    except Exception as e:
        messagebox.showerror("Model Error", f"Could not load roles: {e}")
        return []
    finally:
        conn.close()


def get_role_by_name(role_name):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor(dictionary=True)
        cols = ", ".join(["role_id", "role_name", "description"] + list(PERMISSION_KEYS))
        cursor.execute(f"SELECT {cols} FROM roles WHERE role_name = %s", (role_name,))
        return cursor.fetchone()
    except Exception as e:
        messagebox.showerror("Model Error", str(e))
        return None
    finally:
        conn.close()


def get_permissions_for_role(role_name):
    row = get_role_by_name(role_name)
    if not row:
        fallback = next((r for r in DEFAULT_ROLES if r["role_name"] == role_name), None)
        if fallback:
            return _row_to_permissions(fallback)
        return _row_to_permissions(DEFAULT_ROLES[1])
    return _row_to_permissions(row)


def get_role_names():
    roles = fetch_all_roles()
    if roles:
        return [r["role_name"] for r in roles]
    return [r["role_name"] for r in DEFAULT_ROLES]


def insert_role(role_name, description, permissions):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        vals = [role_name.strip().lower(), description.strip()]
        vals += [1 if permissions.get(k) else 0 for k in PERMISSION_KEYS]
        placeholders = ", ".join(["%s"] * (2 + len(PERMISSION_KEYS)))
        col_names = "role_name, description, " + ", ".join(PERMISSION_KEYS)
        cursor.execute(f"INSERT INTO roles ({col_names}) VALUES ({placeholders})", vals)
        conn.commit()
        return True
    except Exception as e:
        messagebox.showerror("Model Error", str(e))
        return False
    finally:
        conn.close()


def update_role(role_id, role_name, description, permissions):
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        sets = ["role_name=%s", "description=%s"] + [f"{k}=%s" for k in PERMISSION_KEYS]
        vals = [role_name.strip().lower(), description.strip()]
        vals += [1 if permissions.get(k) else 0 for k in PERMISSION_KEYS]
        vals.append(role_id)
        cursor.execute(f"UPDATE roles SET {', '.join(sets)} WHERE role_id=%s", vals)
        conn.commit()
        return True
    except Exception as e:
        messagebox.showerror("Model Error", str(e))
        return False
    finally:
        conn.close()


def delete_role(role_id, role_name):
    if role_name in ("admin", "user"):
        messagebox.showwarning("Delete Blocked", f"Built-in role '{role_name}' cannot be deleted.")
        return False
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = %s", (role_name,))
        if cursor.fetchone()[0] > 0:
            messagebox.showwarning("Delete Blocked", "Users are still assigned to this role.")
            return False
        cursor.execute("DELETE FROM roles WHERE role_id = %s", (role_id,))
        conn.commit()
        return True
    except Exception as e:
        messagebox.showerror("Model Error", str(e))
        return False
    finally:
        conn.close()


def seed_default_roles(cursor):
    for role in DEFAULT_ROLES:
        cursor.execute("SELECT role_id FROM roles WHERE role_name = %s", (role["role_name"],))
        if cursor.fetchone():
            continue
        cols = "role_name, description, " + ", ".join(PERMISSION_KEYS)
        placeholders = ", ".join(["%s"] * (2 + len(PERMISSION_KEYS)))
        vals = [role["role_name"], role["description"]] + [role[k] for k in PERMISSION_KEYS]
        cursor.execute(f"INSERT INTO roles ({cols}) VALUES ({placeholders})", vals)
