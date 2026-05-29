1) အရေးကြီးကြိုတင်ပြင်ဆင်ရန်: Terminal တွင် pip install mysql-connector-python ကို အရင်ဆုံး Install ပြုလုပ်ထားပေးပါ။

2) create direcroty and file as follow
 office_dms/
│
├── config.py             # Database Connection settings
├── main.py               # Application Entry Point (Run လုပ်မည့်ဖိုင်)
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
    ├── outletter_view.py
    ├── doctype_view.py
    ├── action_view.py
    ├── dept_view.py
    ├── main_query.py    # စာရှာဖွေရန်နှင့် Report ထုတ်ရန် View
    ├── login_view.py    # Login ဝင်ရောက်ရန်
    ├── access_mgmt_view.py  # User management
    ├── role_mgmt_view.py    # Role & permission management
    ├── user_mgmt_view.py  # alias for access_mgmt_view
    ├── user_view.py       # alias for access_mgmt_view
    ├── role_management.py  # Database Row ပြင်ဆင်/ဖျက်ရန်
    └── row_manage_view.py  # alias for role_management

4) Default Login: admin / admin123
   Roles: admin (full), user (entry+edit), viewer (reports only)
   Sidebar "Users & Roles" visible only if role has can_manage_users permission

3) Terminal / Command Prompt တွင် အဓိက Root လမ်းကြောင်း office_dms/ ထဲသို့ ဝင်ရောက်ပြီး အောက်ပါအတိုင်း ရိုက်နှိပ် Run ပါ - "python main.py"
