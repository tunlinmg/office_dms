# main.py
import config
from views.login_view import LoginWindow
from views.dashboard import MainDashboard


def main():
    # ၁။ config ဖိုင်မှတစ်ဆင့် Database & Tables များကို Auto-Init ပြုလုပ်ခြင်း
    config.init_db()

    # ၂။ Login ဝင်ရောက်ပြီးမှ Main Dashboard ဖွင့်ခြင်း
    login = LoginWindow()
    login.mainloop()
    if login.user:
        app = MainDashboard(login.user)
        app.mainloop()


if __name__ == "__main__":
    main()
