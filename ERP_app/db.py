import sqlite3

def init_database():
    conn = sqlite3.connect('lemonade.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS finance 
                      (type TEXT, label TEXT, value REAL)''')
    cursor.execute("SELECT count(*) FROM finance")
    if cursor.fetchone()[0] == 0:
        data = [
            ('revenue', 'T1', 30), ('revenue', 'T2', 45), ('revenue', 'T3', 60),
            ('expense', 'Nhập hàng', 40), ('expense', 'Lương', 30), ('expense', 'Mặt bằng', 30)
        ]
        cursor.executemany("INSERT INTO finance VALUES (?,?,?)", data)
    conn.commit()
    conn.close()

def get_data_by_type(t):
    conn = sqlite3.connect('lemonade.db')
    cursor = conn.cursor()
    cursor.execute("SELECT label, value FROM finance WHERE type=?", (t,))
    rows = cursor.fetchall()
    conn.close()
    return {"labels": [r[0] for r in rows], "values": [r[1] for r in rows]}