from flask import Flask, render_template
import sqlite3
import os
import webview
import threading

app = Flask(__name__)


# Kết nối database nằm trong thư mục database/
def get_db_connection():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(base_dir, 'database', 'lemonade_counting_finance.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    try:
        conn = get_db_connection()
        # Lấy data từ đúng các bảng trong ketoan_taichinh.py
        kpi = conn.execute('SELECT * FROM TotalCostOverview').fetchone()
        expenses = conn.execute('SELECT * FROM DetailedExpenses').fetchall()
        conn.close()


        return render_template('acc/db_total_cost.html', kpi=kpi, expenses=expenses)
    except Exception as e:
        return f"Lỗi rồi Limes ơi: {e}"


def start_flask():
    app.run(port=5000)


if __name__ == '__main__':
    t = threading.Thread(target=start_flask)
    t.daemon = True
    t.start()

    webview.create_window(
        'Lemonade Accounting System',
        'http://127.0.0.1:5000',
        width=1440,
        height=900
    )
    webview.start()