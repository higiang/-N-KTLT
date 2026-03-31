import sqlite3


def setup_lemonade_counting_finance():
    conn = sqlite3.connect('lemonade_counting_finance.db')
    cursor = conn.cursor()

    #DỮ LIỆU 6 THÁNG GẦN NHẤT (VND)
    months = ['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
    rev_vnd = [850000000, 900000000, 1100000000, 800000000, 840000000, 1050000000]
    cost_vnd = [600000000, 650000000, 750000000, 500000000, 647000000, 699000000]
    sold_units = [1400, 1500, 2000, 1300, 1652, 1850]

    #CÔNG THỨC TỰ ĐỘNG TÍNH PERCENTAGE (%) ---
    curr_idx, prev_idx = 5, 4  # Tháng 3 (Index 5) và Tháng 2 (Index 4)

    curr_rev = rev_vnd[curr_idx]
    rev_growth = ((curr_rev - rev_vnd[prev_idx]) / rev_vnd[prev_idx]) * 100

    curr_cost = cost_vnd[curr_idx]
    cost_growth = ((curr_cost - cost_vnd[prev_idx]) / cost_vnd[prev_idx]) * 100

    curr_profit = curr_rev - curr_cost
    prev_profit = rev_vnd[prev_idx] - cost_vnd[prev_idx]
    profit_growth = ((curr_profit - prev_profit) / prev_profit) * 100

    curr_sold = sold_units[curr_idx]
    sold_growth = ((curr_sold - sold_units[prev_idx]) / sold_units[prev_idx]) * 100

    #BẢNG TỔNG QUAN KPI ---
    cursor.execute('DROP TABLE IF EXISTS TodaysSales')
    cursor.execute('CREATE TABLE TodaysSales (Metric TEXT, Value TEXT, Status TEXT)')
    #Format dạng X,XXXM cho giao diện
    sales_data = [
        ('Profit', f'{curr_profit / 1000000:,.0f}M', f'{profit_growth:+.0f}%'),
        ('Total Cost', f'{curr_cost / 1000000:,.0f}M', f'{cost_growth:+.0f}%'),
        ('Product Sold', f'{curr_sold:,.0f}', f'{sold_growth:+.0f}%'),
        ('Total Revenue', f'{curr_rev / 1000000:,.0f}M', f'{rev_growth:+.0f}%')
    ]
    cursor.executemany('INSERT INTO TodaysSales VALUES (?,?,?)', sales_data)

    cursor.execute('DROP TABLE IF EXISTS TotalCostOverview')
    cursor.execute('CREATE TABLE TotalCostOverview (Metric TEXT, Value TEXT, Status TEXT)')
    cursor.execute("INSERT INTO TotalCostOverview VALUES (?,?,?)",
                   ('Total Cost', f'{curr_cost / 1000000:,.0f}M', f'{cost_growth:+.0f}% from last month'))

    cursor.execute('DROP TABLE IF EXISTS TotalRevenueOverview')
    cursor.execute('CREATE TABLE TotalRevenueOverview (Metric TEXT, Value TEXT, Status TEXT)')
    cursor.execute("INSERT INTO TotalRevenueOverview VALUES (?,?,?)",
                   ('Total Revenue', f'{curr_rev / 1000000:,.0f}M', f'{rev_growth:+.0f}% from last month'))

    #BẢNG DỮ LIỆU BIỂU ĐỒ 6 THÁNG
    cursor.execute('DROP TABLE IF EXISTS MonthlyCost')
    cursor.execute('CREATE TABLE MonthlyCost (Month TEXT, Cost_VND INTEGER)')
    cursor.executemany('INSERT INTO MonthlyCost VALUES (?,?)', zip(months, cost_vnd))

    cursor.execute('DROP TABLE IF EXISTS MonthlyRevenue')
    cursor.execute('CREATE TABLE MonthlyRevenue (Month TEXT, Revenue_VND INTEGER)')
    cursor.executemany('INSERT INTO MonthlyRevenue VALUES (?,?)', zip(months, rev_vnd))

    #BẢNG CHI TIẾT CHI PHÍ ĐẦY ĐỦ (Tổng khớp 699,000,000 VND)
    cursor.execute('DROP TABLE IF EXISTS DetailedExpenses')
    cursor.execute('CREATE TABLE DetailedExpenses (Date TEXT, Items TEXT, Department TEXT, Amount_VND INTEGER)')
    expense_items = [
        ('14/03/2026', 'Thanh toán Ads Facebook & IG', 'Marketing', 125000000),
        ('14/03/2026', 'Booking KOL TikTok Campaign', 'Marketing', 80000000),
        ('14/03/2026', 'Nhập 5.000 vỏ hộp Cushion', 'Houseware', 150000000),
        ('14/03/2026', 'Nhập bao bì son thỏi', 'Houseware', 50000000),
        ('14/03/2026', 'Phí vận chuyển GHTK & ViettelPost', 'Logistics', 105000000),
        ('14/03/2026', 'Nhập nguyên liệu: Màu khoáng Đỏ', 'Production', 70000000),
        ('14/03/2026', 'Tiền thuê văn phòng Quận 1', 'Operation', 40000000),
        ('14/03/2026', 'Tiền thuê kho bãi Quận 9', 'Operation', 21500000),
        ('14/03/2026', 'Phí Server AWS & Domain', 'Operation', 21250000),
        ('14/03/2026', 'Tiền điện nước văn phòng', 'Operation', 27500000),
        ('14/03/2026', 'Lương làm thêm giờ (OT) kho', 'HR', 8750000)
    ]
    total_sum_expense = sum(item[3] for item in expense_items)
    cursor.executemany('INSERT INTO DetailedExpenses VALUES (?,?,?,?)', expense_items)
    cursor.execute("INSERT INTO DetailedExpenses VALUES ('-', 'TOTAL', '-', ?)", (total_sum_expense,))

    #BẢNG CHI TIẾT DOANH THU ĐẦY ĐỦ (Tổng khớp 1,050,000,000 VND)
    cursor.execute('DROP TABLE IF EXISTS RevenueDetails')
    cursor.execute('CREATE TABLE RevenueDetails (Date TEXT, Items TEXT, Department TEXT, Amount_VND INTEGER)')
    revenue_items = [
        ('14/03/2026', 'Doanh thu Mega Livestream TikTok', 'TikTok Shop', 250000000),
        ('14/03/2026', 'Đơn hàng tự nhiên TikTok Shop', 'TikTok Shop', 100000000),
        ('14/03/2026', 'Đơn sỉ Đại lý khu vực Miền Bắc', 'Wholesale', 150000000),
        ('14/03/2026', 'Đơn sỉ Đại lý khu vực Miền Nam', 'Wholesale', 100000000),
        ('14/03/2026', 'Doanh thu Shopee Mall (Sale 3.3)', 'E-commerce', 200000000),
        ('14/03/2026', 'Doanh thu Lazada LazMall', 'E-commerce', 75000000),
        ('14/03/2026', 'Doanh thu Cửa hàng Flagship', 'Offline Store', 80000000),
        ('14/03/2026', 'Đơn hàng Website Trực tiếp', 'Website', 45000000),
        ('14/03/2026', 'Hợp đồng B2B (Quà tặng 8/3)', 'B2B Contract', 50000000)
    ]
    total_rev_sum = sum(item[3] for item in revenue_items)
    cursor.executemany('INSERT INTO RevenueDetails VALUES (?,?,?,?)', revenue_items)
    cursor.execute("INSERT INTO RevenueDetails VALUES ('-', 'TOTAL', '-', ?)", (total_rev_sum,))

    #BẢNG FORECAST & COMPARISON
    cursor.execute('DROP TABLE IF EXISTS CashFlowForecast')
    cursor.execute('CREATE TABLE CashFlowForecast (Quarter TEXT, Sales_Forecast INTEGER, Expense_Forecast INTEGER)')
    quarterly_data = [('Q1', 3400000, 2100000), ('Q2', 3600000, 2200000), ('Q3', 4200000, 2800000),
                      ('Q4', 5500000, 3500000)]
    cursor.executemany('INSERT INTO CashFlowForecast VALUES (?,?,?)', quarterly_data)

    cursor.execute('DROP TABLE IF EXISTS ComparisonData')
    cursor.execute('CREATE TABLE ComparisonData (Month TEXT, Revenue INTEGER, Cost INTEGER, Profit INTEGER)')

    #Scale số liệu xuống để không bị vỡ biểu đồ trong app.py
    comparison_data = []
    for i in range(6):
        # Vì file app.py chia 1000,lưu dạng thousands (ví dụ: 1,050M = 1,050,000 ngàn)
        comparison_data.append((months[i], rev_vnd[i] / 1000, cost_vnd[i] / 1000, (rev_vnd[i] - cost_vnd[i]) / 1000))

    cursor.executemany('INSERT INTO ComparisonData VALUES (?,?,?,?)', comparison_data)

    conn.commit()
    conn.close()


if __name__ == '__main__':
    setup_lemonade_counting_finance()