import sqlite3

def tao_data_tai_chinh():
    #Kết nối và tạo file database
    conn = sqlite3.connect('quan_ly_my_pham.db')
    cursor = conn.cursor()

    #Tạo bảng Chi Tiêu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ChiTieu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ngay TEXT,
            hang_muc TEXT,
            phong_ban TEXT,
            so_tien REAL
        )
    ''')

    #Tạo bảng Doanh Thu
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS DoanhThu (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ngay TEXT,
            san_pham TEXT,
            phong_ban TEXT,
            so_tien REAL
        )
    ''')

    #Nạp dữ liệu mẫu cho 6 tháng (Mỗi tháng 1 ít cho dễ vẽ biểu đồ)
    du_lieu_chi_tieu = [
        ('2025-01-15', 'Lương nhân viên', 'Nhân sự', 50000000),
        ('2025-02-10', 'Chi phí sản xuất son', 'Sản xuất', 20000000),
        ('2025-03-05', 'Quảng cáo Facebook', 'Marketing', 15000000),
        ('2025-04-20', 'Tiền thuê mặt bằng', 'Tài chính', 30000000),
        ('2025-05-12', 'Nguyên liệu mỹ phẩm', 'Sản xuất', 25000000),
        ('2025-06-18', 'Lương nhân viên', 'Nhân sự', 50000000)
    ]

    du_lieu_doanh_thu = [
        ('1/2025', 'Son bóng Lemonade', 'Bán lẻ', 200000000),
        ('2/2025', 'Phấn nền', 'Bán lẻ', 180000000),
        ('3/2025', 'Chì kẻ mày', 'Bán lẻ', 210000000),
        ('4/2025', 'Combo trang điểm', 'Đại lý', 250000000),
        ('5/2025', 'Son lì', 'Bán lẻ', 190000000),
        ('6/2025', 'Nước tẩy trang', 'Bán lẻ', 220000000)
    ]

    cursor.executemany('INSERT INTO ChiTieu (ngay, hang_muc, phong_ban, so_tien) VALUES (?,?,?,?)', du_lieu_chi_tieu)
    cursor.executemany('INSERT INTO DoanhThu (ngay, san_pham, phong_ban, so_tien) VALUES (?,?,?,?)', du_lieu_doanh_thu)

    conn.commit()
    conn.close()

# Gọi hàm để tạo data
tao_data_tai_chinh()