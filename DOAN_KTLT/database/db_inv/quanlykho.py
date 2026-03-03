import sqlite3

def setup_complete_inventory_system():
    conn = sqlite3.connect('lemonade_inventory.db')
    cursor = conn.cursor()

    #SCREEN 1: TABLE 1 - INVENTORY OVERVIEW
    cursor.execute('DROP TABLE IF EXISTS InventoryOverview')
    cursor.execute('CREATE TABLE InventoryOverview (TieuDe TEXT, SoLieu INTEGER)')
    overview_data = [
        ('TOTAL ITEMS', 385420), ('LOW STOCK', 18),
        ('EXPIRING', 2450), ('SUPPLIERS', 15)
    ]
    cursor.executemany('INSERT INTO InventoryOverview VALUES (?,?)', overview_data)

    #SCREEN 1: TABLE 2 - LOW STOCK ALERT
    cursor.execute('DROP TABLE IF EXISTS LowStockAlert')
    cursor.execute('CREATE TABLE LowStockAlert (ProductName TEXT, Stock INTEGER, Status TEXT)')
    low_stock_data = [
        ('Son Kem Lì Blurry Stain - Bloom', 850, 'Low Stock'),
        ('Phấn Nước SuperMatte Cushion - A01.Light', 45, 'Critical'),
        ('Chì Kẻ Mày Micro Eyebrow - 02.Dark Brown', 980, 'Low Stock'),
        ('Mặt Nạ Giấy Premium (Cấp Ẩm)', 0, 'Out of Stock'),
        ('Má Hồng Mirror Mirror Blush - 03.Spacy', 120, 'Critical'),
        ('Túi Thời Trang Đa Năng (Màu Bạc)', 15, 'Critical'),
        ('Son Perfect Couple Lip - 05.Engaging', 1200, 'Low Stock'),
        ('Phấn Phủ SuperMatte Loose Powder (Tím)', 0, 'Out of Stock'),
        ('Gương Cầm Tay Lemonade (Limited)', 0, 'Out of Stock'),
        ('Che Khuyết Điểm Matte Addict - A01', 350, 'Critical'),
        ('Son Tint Bóng - T03 (Đỏ Cherry)', 1450, 'Low Stock'),
        ('Kẻ Mắt Nước Supernatural (Nâu Đen)', 680, 'Low Stock')
    ]
    cursor.executemany('INSERT INTO LowStockAlert VALUES (?,?,?)', low_stock_data)


    #SCREEN 2: TABLE 3 - ALL PRODUCTS
    cursor.execute('DROP TABLE IF EXISTS AllProducts')
    cursor.execute('CREATE TABLE AllProducts (ProductName TEXT, SKU TEXT, Stock INTEGER, Price REAL)')
    products = [
        ('Son Kem Lì Blurry Stain', '#LM001', 4500, 250000),
        ('Phấn Nước SuperMatte Cushion', '#LM002', 2100, 320000),
        ('Chì Kẻ Mày Micro Eyebrow', '#LM003', 1280, 160000),
        ('Mặt Nạ Giấy Premium', '#LM004', 5000, 35000),
        ('Má Hồng Mirror Mirror', '#LM005', 3200, 210000),
        ('Túi Thời Trang Limited', '#LM006', 150, 450000),
        ('Son Perfect Couple Lip', '#LM007', 1200, 290000),
        ('Phấn Phủ Loose Powder', '#LM008', 800, 300000),
        ('Gương Cầm Tay Lemonade', '#LM009', 500, 99000),
        ('Che Khuyết Điểm Matte Addict', '#LM010', 3500, 230000),
        ('Son Tint Bóng T03', '#LM011', 7770, 220000)
    ]
    cursor.executemany('INSERT INTO AllProducts VALUES (?,?,?,?)', products)

    #SCREEN 2: TABLE 4 - STOCK QUANTITY
    cursor.execute('DROP TABLE IF EXISTS StockQuantity')
    cursor.execute('CREATE TABLE StockQuantity (Week TEXT, Imported INTEGER, Sold INTEGER, InStock INTEGER)')
    weekly_stats = [
        ('Week 1', 50000, 25000, 25000),
        ('Week 2', 40000, 35000, 30000),
        ('Week 3', 35000, 40000, 25000),
        ('Week 4', 25000, 20000, 30000)
    ]
    cursor.executemany('INSERT INTO StockQuantity VALUES (?,?,?,?)', weekly_stats)


    #SCREEN 3: TABLE 5 - SUPPLIER LIST
    cursor.execute('DROP TABLE IF EXISTS Suppliers')
    cursor.execute('CREATE TABLE Suppliers (CompanyName TEXT, Phone TEXT, Category TEXT, Location TEXT)')
    suppliers = [
        ('In Ấn Việt Nhật', '02438385555', 'Bao bì giấy / Vỏ Son', 'Long An'),
        ('Chai Lọ Duy Tân', '02833339999', 'Chai lọ nhựa (Cushion)', 'Vũng Tàu'),
        ('Hóa Chất Á Châu (ACC)', '02854161234', 'Nguyên liệu / Màu khoáng', 'TP.HCM'),
        ('Hương Liệu Pháp Việt', '0903999888', 'Hương liệu (Fragrance)', 'TP.HCM'),
        ('Cosmax Korea', '(+82) 23456789', 'Gia công (OEM/ODM)', 'Seoul, Korea'),
        ('Bao Bì Tân Tiến', '0933777888', 'Màng co / Bao bì nhựa', 'Đồng Nai'),
        ('Tem Nhãn Hoàng Hà', '0915444333', 'Decal / Tem chống giả', 'Đồng Nai'),
        ('Thủy Tinh MISO', '0909555222', 'Chai lọ thủy tinh (Serum)', 'TP.HCM'),
        ('Nhựa Đức Đạt', '0901888666', 'Hũ nhựa Acrylic cao cấp', 'Bình Dương'),
        ('Giấy Sài Gòn', '038762222', 'Thùng Carton đóng hàng', 'Bình Dương'),
        ('Hương Liệu Việt Hương', '02839991111', 'Tinh dầu / Chất lưu hương', 'TP.HCM'),
        ('Bao Bì Khang Thịnh', '0902333444', 'Hộp cứng cao cấp (Giftset)', 'TP.HCM'),
        ('Vận Tải Phương Trang', '19.006.067', 'Logistics (Vận chuyển)', 'Toàn quốc'),
        ('Viettel Post Logistics', '19.008.095', 'Giao hàng nhanh (Express)', 'Hà Nội'),
        ('Nguyên Liệu Brenntag', '02837775555', 'Dung môi / Chất bảo quản', 'Đồng Nai')
    ]
    cursor.executemany('INSERT INTO Suppliers VALUES (?,?,?,?)', suppliers)

    conn.commit()
    conn.close()

setup_complete_inventory_system()