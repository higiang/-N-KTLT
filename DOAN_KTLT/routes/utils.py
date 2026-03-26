import os, sqlite3

# vì các account đều dùng database nên gộp chung vào 1 file tiện ích riêng để dễ quản lý
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

DB_ACC  = os.path.join(BASE_DIR, 'database', 'lemonade_counting_finance.db')
DB_INV  = os.path.join(BASE_DIR, 'database', 'lemonade_inventory.db')
DB_MKT  = os.path.join(BASE_DIR, 'database', 'mkt_department.db')
DB_SALE = os.path.join(BASE_DIR, 'database', 'sales.db')
DB_USER = os.path.join(BASE_DIR, 'database', 'info.db')

def get_db(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

def save_to_downloads(filename, content):

    downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    os.makedirs(downloads, exist_ok=True)
    filepath = os.path.join(downloads, filename)
    with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
        f.write(content)
    return filepath


def update_user_info(email, department, manager, phone):
    conn = get_db(DB_USER)
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE accounts SET department_name = ? WHERE email = ?", (department, email))
        cursor.execute("SELECT password FROM accounts WHERE email = ?", (email,))
        pwd_row = cursor.fetchone()
        password = pwd_row[0] if pwd_row else ''
        cursor.execute("SELECT email FROM departments WHERE email = ?", (email,))
        if cursor.fetchone():
            cursor.execute("""
                UPDATE departments SET department_name = ?, manager_name = ?, phone = ?
                WHERE email = ?
            """, (department, manager, phone, email))
        else:
            cursor.execute("""
                INSERT INTO departments (department_name, manager_name, phone, email, password)
                VALUES (?, ?, ?, ?, ?)
            """, (department, manager, phone, email, password))
        conn.commit()
    except Exception as e:
        print("Lỗi update database:", e)
    finally:
        conn.close()