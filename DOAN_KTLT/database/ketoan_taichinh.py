import sqlite3

def setup_lemonade_counting_finance():
    conn = sqlite3.connect('lemonade_counting_finance.db')
    cursor = conn.cursor()

    #SCREEN 1: OVERVIEW DASHBOARD
    # Bảng 1: Các chỉ số tổng
    cursor.execute('DROP TABLE IF EXISTS TodaysSales')
    cursor.execute('CREATE TABLE TodaysSales (Metric TEXT, Value TEXT, Status TEXT)')
    sales_data = [
        ('Profit', '$14,050', '+15%'),
        ('Total Cost', '$27,950', '+8%'),
        ('Product Sold', '1,850', '+12%'),
        ('Total Revenue', '$42,000', '+25%')
    ]
    cursor.executemany('INSERT INTO TodaysSales VALUES (?,?,?)', sales_data)

    # Bảng 2: Biểu đồ tròn Cost
    cursor.execute('DROP TABLE IF EXISTS Screen1_CostCircle')
    cursor.execute('CREATE TABLE Screen1_CostCircle (Category TEXT, Percentage TEXT)')
    cost_circle = [('Marketing', '45%'), ('Nhập hàng', '45%'), ('Vận hành', '10%')]
    cursor.executemany('INSERT INTO Screen1_CostCircle VALUES (?,?)', cost_circle)

    # Bảng 3: Biểu đồ tròn Revenue
    cursor.execute('DROP TABLE IF EXISTS Screen1_RevenueCircle')
    cursor.execute('CREATE TABLE Screen1_RevenueCircle (Category TEXT, Percentage TEXT)')
    rev_circle = [
        ('Son Kem Lì ($18,900)', '45%'),
        ('Cushion A01 ($18,900)', '45%'),
        ('Mắt & Mày ($4,200)', '10%')
    ]
    cursor.executemany('INSERT INTO Screen1_RevenueCircle VALUES (?,?)', rev_circle)


    #SCREEN 2: TOTAL COST DETAILS
    cursor.execute('DROP TABLE IF EXISTS TotalCostOverview')
    cursor.execute('CREATE TABLE TotalCostOverview (Metric TEXT, Value TEXT, Status TEXT)')
    cursor.execute("INSERT INTO TotalCostOverview VALUES ('Total Cost', '$27,950', '+5% from yesterday')")

    cursor.execute('DROP TABLE IF EXISTS CostDistribution')
    cursor.execute('CREATE TABLE CostDistribution (Category TEXT, Percentage TEXT)')
    dist_data = [('Marketing', '45%'), ('Nhập hàng', '45%'), ('Vận hành', '10%')]
    cursor.executemany('INSERT INTO CostDistribution VALUES (?,?)', dist_data)

    cursor.execute('DROP TABLE IF EXISTS MonthlyCost')
    cursor.execute('CREATE TABLE MonthlyCost (Month TEXT, Cost_USD INTEGER)')
    monthly_cost_data = [('Jan', 25000), ('Feb', 18000), ('Mar', 28000), ('Apr', 20000), ('May', 22000), ('Jun', 30000)]
    cursor.executemany('INSERT INTO MonthlyCost VALUES (?,?)', monthly_cost_data)

    cursor.execute('DROP TABLE IF EXISTS DetailedExpenses')
    cursor.execute('CREATE TABLE DetailedExpenses (Date TEXT, Items TEXT, Department TEXT, Amount_USD INTEGER)')
    expense_items = [
        ('29/01/2026', 'Thanh toán Ads Facebook (Summer Sale)', 'Marketing', 5000),
        ('29/01/2026', 'Nhập 1.000 vỏ hộp Cushion A01', 'Houseware', 8500),
        ('29/01/2026', 'Phí vận chuyển COD Tháng 1', 'Logistics', 4200),
        ('29/01/2026', 'Booking KOL review TikTok (Hà Linh)', 'Marketing', 3200),
        ('29/01/2026', 'Nhập 2.000 vỏ giấy bao bì son', 'Houseware', 1500),
        ('29/01/2026', 'Mua nguyên liệu Màu khoáng (Đỏ Cherry)', 'Production', 2800),
        ('29/01/2026', 'Phí Server & Cloud Hosting', 'Operation', 850),
        ('29/01/2026', 'Đặt cọc lô chai lọ Serum thủy tinh', 'Houseware', 1200),
        ('29/01/2026', 'Thanh toán Ads TikTok Shop', 'Marketing', 2500),
        ('29/01/2026', 'Chi phí văn phòng phẩm & in ấn', 'Admin', 150),
        ('29/01/2026', 'Lương làm thêm giờ (OT) kho vận', 'HR', 350),
        ('29/01/2026', 'Tem chống giả Hologram (5.000 tem)', 'Houseware', 450),
        ('29/01/2026', 'Tiền điện văn phòng & Kho tháng 1', 'Operation', 1100),
        ('29/01/2026', 'Nhập hương liệu Tinh dầu Cam chanh', 'Production', 600),
        ('29/01/2026', 'Thuê xe tải chở hàng đi tỉnh', 'Logistics', 950),
        ('29/01/2026', 'Bảo trì máy lạnh kho chứa hàng', 'Operation', 200),
        ('29/01/2026', 'Mua suất ăn trưa cho nhân viên', 'HR', 120),
        ('29/01/2026', 'Phần mềm Email Marketing (Gia hạn)', 'Marketing', 180)
    ]
    total_sum_expense = sum(item[3] for item in expense_items)
    cursor.executemany('INSERT INTO DetailedExpenses VALUES (?,?,?,?)', expense_items)
    cursor.execute("INSERT INTO DetailedExpenses VALUES ('-', 'TOTAL', '-', ?)", (total_sum_expense,))


    #SCREEN 3: TOTAL REVENUE DETAILS
    cursor.execute('DROP TABLE IF EXISTS TotalRevenueOverview')
    cursor.execute('CREATE TABLE TotalRevenueOverview (Metric TEXT, Value TEXT, Status TEXT)')
    cursor.execute("INSERT INTO TotalRevenueOverview VALUES ('Total Revenue', '$42,000', '+25% from yesterday')")

    cursor.execute('DROP TABLE IF EXISTS RevenueDistribution')
    cursor.execute('CREATE TABLE RevenueDistribution (Category TEXT, Percentage TEXT)')
    rev_dist_data = [('Son Kem Lì ($18,900)', '45%'), ('Cushion A01 ($18,900)', '45%'), ('Mắt & Mày ($4,200)', '10%')]
    cursor.executemany('INSERT INTO RevenueDistribution VALUES (?,?)', rev_dist_data)

    cursor.execute('DROP TABLE IF EXISTS MonthlyRevenue')
    cursor.execute('CREATE TABLE MonthlyRevenue (Month TEXT, Revenue_USD INTEGER)')
    monthly_rev_data = [('Jan', 35000), ('Feb', 28000), ('Mar', 45000), ('Apr', 32000), ('May', 38000), ('Jun', 42000)]
    cursor.executemany('INSERT INTO MonthlyRevenue VALUES (?,?)', monthly_rev_data)

    cursor.execute('DROP TABLE IF EXISTS RevenueDetails')
    cursor.execute('CREATE TABLE RevenueDetails (Date TEXT, Items TEXT, Department TEXT, Amount_USD INTEGER)')
    revenue_items = [
        ('29/01/2026', 'Doanh thu Livestream TikTok (Ca Sáng)', 'TikTok Shop', 4500),
        ('29/01/2026', 'Doanh thu Livestream TikTok (Ca Tối - Hà Linh)', 'TikTok Shop', 10000),
        ('29/01/2026', 'Đơn hàng sỉ Đại lý Hà Nội (Batch #WH01)', 'Wholesale (Sỉ)', 5000),
        ('29/01/2026', 'Đơn hàng sỉ Đại lý Đà Nẵng (Batch #WH02)', 'Wholesale (Sỉ)', 5000),
        ('29/01/2026', 'Doanh thu sàn Shopee Mall (Super Brand Day)', 'E-commerce', 6000),
        ('29/01/2026', 'Doanh thu sàn Lazada Mall (Flash Sale)', 'E-commerce', 1800),
        ('29/01/2026', 'Doanh thu Cửa hàng Flagship (Q1, TP.HCM)', 'Offline Store', 1200),
        ('29/01/2026', 'Doanh thu Cửa hàng Aeon Mall (Tân Phú)', 'Offline Store', 1300),
        ('29/01/2026', 'Đơn hàng Doanh nghiệp (Quà tặng 8/3 sớm)', 'B2B Contract', 3000),
        ('29/01/2026', 'Doanh thu Website (Direct Sales)', 'Website', 2500),
        ('29/01/2026', 'Phí nhượng quyền thương hiệu (Tháng 1)', 'Franchise', 1200),
        ('29/01/2026', 'Thanh lý vỏ chai lỗi/hư hỏng', 'Warehouse', 500)
    ]
    total_rev_sum = sum(item[3] for item in revenue_items)
    cursor.executemany('INSERT INTO RevenueDetails VALUES (?,?,?,?)', revenue_items)
    cursor.execute("INSERT INTO RevenueDetails VALUES ('-', 'TỔNG CỘNG (Total Revenue)', '-', ?)", (total_rev_sum,))


    #SCREEN 4: CASH FLOW & COMPARISON
    cursor.execute('DROP TABLE IF EXISTS CashFlowForecast')
    cursor.execute('CREATE TABLE CashFlowForecast (Quarter TEXT, Sales_Forecast INTEGER, Expense_Forecast INTEGER)')
    quarterly_data = [('Q1 (T1-T3)', 108000, 71000), ('Q2 (T4-T6)', 112000, 72000), ('Q3 (T7-T9)', 150000, 90000), ('Q4 (T10-T12)', 200000, 120000)]
    cursor.executemany('INSERT INTO CashFlowForecast VALUES (?,?,?)', quarterly_data)

    cursor.execute('DROP TABLE IF EXISTS ComparisonData')
    cursor.execute('CREATE TABLE ComparisonData (Month TEXT, Revenue INTEGER, Cost INTEGER, Profit INTEGER)')
    comparison_data = [
        ('Jan', 35000, 25000, 10000), ('Feb', 28000, 18000, 10000),
        ('Mar', 45000, 28000, 17000), ('Apr', 32000, 20000, 12000),
        ('May', 38000, 22000, 16000), ('Jun', 42000, 30000, 12000)
    ]
    cursor.executemany('INSERT INTO ComparisonData VALUES (?,?,?,?)', comparison_data)

    cursor.execute('DROP TABLE IF EXISTS MonthlyProfit')
    cursor.execute('CREATE TABLE MonthlyProfit (Month TEXT, Profit_USD INTEGER)')
    profit_only_data = [('Jan', 10000), ('Feb', 10000), ('Mar', 17000), ('Apr', 12000), ('May', 16000), ('Jun', 12000)]
    cursor.executemany('INSERT INTO MonthlyProfit VALUES (?,?)', profit_only_data)

    conn.commit()
    conn.close()

setup_lemonade_counting_finance()