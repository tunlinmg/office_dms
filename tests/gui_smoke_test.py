import sys
import os

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from src.views.dashboard import MainDashboard

user = {
    'username': 'tester',
    'full_name': 'Test User',
    'role': 'admin',
    'permissions': {
        'can_manage_users': 1,
        'can_manage_roles': 1,
        'can_delete_rows': 1,
        'can_edit_rows': 1,
        'can_entry_forms': 1,
        'can_view_reports': 1,
    }
}

root = MainDashboard(user)
root.update_idletasks()
root.show_view('users')
root.update_idletasks()
root.show_view('roles')
root.update_idletasks()
print('SMOKE_TEST_PASS')
root.destroy()
