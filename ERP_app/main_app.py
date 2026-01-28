import webview
import os
import db, login_logic, ceo_logic, acc_logic


class LemonadeBridge:
    def __init__(self):
        db.init_database()

    def login_request(self, u, p):
        return login_logic.verify_user(u, p)

    def get_ceo_data(self):
        return ceo_logic.get_stats()

    def get_acc_data(self):
        return acc_logic.get_report()


def start():
    api = LemonadeBridge()
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    html_path = os.path.join(curr_dir, "index.html")  # Fix lỗi 404

    window = webview.create_window(
        'Lemonade Beauty ERP',
        url=html_path,
        js_api=api,
        width=1280, height=850
    )
    webview.start()


if __name__ == '__main__':
    start()