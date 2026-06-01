import importlib.util
import sys
import traceback
import os

# Ensure office_dms is on sys.path so package-local imports resolve
base = r"c:\Users\user\Downloads\Python\Group Project\dms_20260601\office_dms"
if base not in sys.path:
    sys.path.insert(0, base)

paths = [
    r"c:\Users\user\Downloads\Python\Group Project\dms_20260601\office_dms\models\role_model.py",
    r"c:\Users\user\Downloads\Python\Group Project\dms_20260601\office_dms\views\role_mgmt_view.py",
    r"c:\Users\user\Downloads\Python\Group Project\dms_20260601\office_dms\views\role_management.py",
]

success = True
for p in paths:
    try:
        spec = importlib.util.spec_from_file_location("mod", p)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        print("Loaded:", p)
    except Exception:
        traceback.print_exc()
        success = False

if not success:
    sys.exit(2)
print("IMPORTS_OK")
