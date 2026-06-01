# Office DMS - Document Management System

## 1. Prerequisites
Before running the application, ensure you have the required Python package installed:
```bash
pip install mysql-connector-python
pip install matplotlib
pip install tkcalendar
```

## 2. Project Structure
Create the following directory and file structure:
```
office_dms/
│
├── config.py             # Database Connection settings
├── main.py               # Application Entry Point (Run this file)
│
├── models/               # --- MODELS (Database Logic) ---
│   ├── __init__.py
│   ├── inletter_model.py
│   ├── outletter_model.py
│   ├── doctype_model.py
│   ├── action_model.py
│   ├── dept_model.py
│   ├── user_model.py
│   ├── role_model.py
│   └── row_model.py
│
└── views/                # --- VIEWS & CONTROLLERS (UI & Event Handling) ---
    ├── __init__.py
    ├── dashboard.py      # Main Dashboard View
    ├── inletter_view.py
    ├── inletter_query.py
    ├── outletter_view.py
    ├── outletter_query.py
    ├── doctype_view.py
    ├── action_view.py
    ├── dept_view.py
    ├── main_query.py     # Search and Report View
    ├── login_view.py     # Login Interface
    ├── access_mgmt_view.py  # User management
    ├── role_mgmt_view.py    # Role & permission management
    ├── user_mgmt_view.py  # alias for access_mgmt_view
    ├── user_view.py       # alias for access_mgmt_view
    ├── role_management.py  # Database Row Edit/Delete
    └── row_manage_view.py  # alias for role_management
```

## 3. Default Login Credentials
- **Username:** `admin`
- **Password:** `admin123`

## 4. User Roles & Permissions
| Role | Permissions |
|------|-------------|
| `admin` | Full access to all features |
| `user` | Entry and Edit permissions |
| `viewer` | Reports only |

**Note:** The "Users & Roles" section in the sidebar is only visible to users with the `can_manage_users` permission.

## 5. Running the Application
Navigate to the `office_dms/` directory in your terminal and execute:
```bash
python main.py