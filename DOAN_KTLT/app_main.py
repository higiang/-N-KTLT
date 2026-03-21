import sqlite3, csv, io, os, math
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.offline as opy

# ══════════════════════════════════════════════════════════════════
# KHỞI TẠO APP DUY NHẤT
# Tất cả phòng ban chạy chung 1 Flask app, port 5000
# ══════════════════════════════════════════════════════════════════
app = Flask(__name__)
app.secret_key = 'lemonade_super_secret_key'

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Đường dẫn các database
DB_ACC  = os.path.join(BASE_DIR, 'database', 'lemonade_counting_finance.db')
DB_INV  = os.path.join(BASE_DIR, 'database', 'lemonade_inventory.db')
DB_MKT  = os.path.join(BASE_DIR, 'database', 'mkt_department.db')
DB_SALE = os.path.join(BASE_DIR, 'database', 'sales.db')
DB_USER = os.path.join(BASE_DIR, 'database', 'info.db')


# ══════════════════════════════════════════════════════════════════
# CEO SETTINGS (ACCOUNT MANAGEMENT)
# ══════════════════════════════════════════════════════════════════

def get_accounts():
    conn = get_db(DB_USER)
    cursor = conn.cursor()

    query = """
    SELECT 
        a.id,
        d.manager_name AS manager,
        a.department_name AS department,
        a.email,
        a.password,
        d.phone,
        a.role
    FROM accounts a
    LEFT JOIN departments d
    ON a.email = d.email
    """

    rows = cursor.execute(query).fetchall()
    conn.close()

    return rows

# ══════════════════════════════════════════════════════════════════
# HÀM TIỆN ÍCH CHUNG
# ══════════════════════════════════════════════════════════════════

def get_db(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn

def save_to_downloads(filename, content):
    """Lưu file CSV vào thư mục Downloads."""
    downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    os.makedirs(downloads, exist_ok=True)
    filepath = os.path.join(downloads, filename)
    with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
        f.write(content)
    return filepath
# GLOBAL CONTEXT PROCESSOR (Biến dùng chung cho toàn bộ HTML)
# ══════════════════════════════════════════════════════════════════
@app.context_processor
def inject_global_variables():
    is_admin = False
    # Kiểm tra xem có user nào đang đăng nhập không
    if 'user_email' in session:
        user = get_account_from_db(session['user_email'])
        # Kiểm tra xem role có phải admin không
        if user and user.get('role') == 'admin':
            is_admin = True

    # Trả về một dictionary, tất cả các key trong này sẽ thành biến trong HTML
    return dict(is_admin=is_admin)


# ══════════════════════════════════════════════════════════════════
# TRANG CHỦ → chuyển về Login
# ══════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return redirect(url_for("login"))


# ══════════════════════════════════════════════════════════════════
# LOGIN / SIGNUP / USER INFO
# ══════════════════════════════════════════════════════════════════

def get_account_from_db(email):
    conn = get_db(DB_USER)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM accounts WHERE email = ?", (email,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_full_user_info(email):
    conn = get_db(DB_USER)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.email, a.password, a.role,
               a.department_name AS department,
               d.manager_name AS manager,
               d.phone
        FROM accounts a
        LEFT JOIN departments d ON a.email = d.email
        WHERE a.email = ?
    """, (email,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def add_user_to_db(email, password):
    conn = get_db(DB_USER)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO accounts (department_name, email, password, role) VALUES ('', ?, ?, 'department')",
            (email, password)
        )
        conn.commit()
        success = True
    except sqlite3.IntegrityError:
        success = False
    finally:
        conn.close()
    return success

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

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email     = request.form.get('email')
        password  = request.form.get('password')
        form_role = request.form.get('role')
        user = get_account_from_db(email)
        # kiểm tra thông tin user có khớp không
        if user:
            if user['password'] == password:
                db_role = user.get('role')  # trả về admin hoặc user từ db
                # kiểm tra role sao cho trùng khớp giữa html và database
                if form_role == 'user' and db_role != 'department':
                    error = "This account does not have user privileges."
                elif form_role == 'admin' and db_role != 'admin':
                    error = "This account does not have admin privileges."
                else:
                    session['user_email'] = user['email']  # giữ phiên đăng nhập
                    return redirect(url_for('user_info'))

            else:
                error = "Email or password is incorrect."
        else:
            error = "Email has not been registered."
    return render_template('log_in.html', error=error)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    error = None
    if request.method == 'POST':
        email            = request.form.get('email')
        password         = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if not email or not password:
            error = "Please enter all the required information."
        elif password != confirm_password:
            error = "Password doesn't match"
        else:
            if add_user_to_db(email, password):
                return redirect(url_for('login'))
            else:
                error = "This email is already registered"
    return render_template('sign_up.html', error=error)


@app.route('/user_info', methods=['GET', 'POST'])
def user_info():
    # 1. Kiểm tra đăng nhập
    if 'user_email' not in session:
        return redirect(url_for('login'))

    current_email = session['user_email']

    # 2. Xử lý khi người dùng ấn nút Confirm (POST)
    if request.method == 'POST':
        # Lấy dữ liệu an toàn từ form
        department = request.form.get('department', '').strip()
        manager = request.form.get('manager', '').strip()
        phone = request.form.get('phone', '').strip()

        # Cập nhật DB
        update_user_info(current_email, department, manager, phone)

        # Kiểm tra Role Admin từ DB
        user = get_account_from_db(current_email)
        role = user.get('role', '').strip().lower() if user else ''

        if role == 'admin':
            return redirect('/dashboard')

        # Điều hướng theo phòng ban (Chuyển hết về chữ thường để tránh lỗi gõ sai hoa/thường)
        dept_lower = department.lower()

        DEPT_ROUTES = {
            'marketing_department': '/mkt/dashboard',
            'inventory_department': '/inv/dashboard',
            'sales_department': '/sales',
            'accounting_n_finance_department': '/acc/dashboard',
        }

        target = DEPT_ROUTES.get(dept_lower)

        if target:
            return redirect(target)
        else:
            # Fallback: Nếu không khớp phòng ban nào, tải lại trang User Info để họ chọn lại
            return redirect(url_for('user_info'))

    # 3. Xử lý khi người dùng mới văng vào trang (GET)
    user_data = get_full_user_info(current_email)

    if not user_data:
        return redirect(url_for('logout'))

    return render_template('user_info.html', user=user_data)
@app.route('/logout')
def logout():
    session.pop('user_email', None)
    return redirect(url_for('login'))

@app.route('/signout')
def signout():
    session.pop('user_email', None)
    return redirect(url_for('login'))


# ══════════════════════════════════════════════════════════════════
# CEO DASHBOARD
# ══════════════════════════════════════════════════════════════════

def ceo_get_pie(table, keyword, h=170):
    conn = get_db(DB_ACC)
    df = pd.read_sql_query(f"SELECT Department, Amount_USD FROM {table} WHERE Items != '{keyword}'", conn)
    conn.close()
    if df.empty: return ""
    df_g = df.groupby('Department', as_index=False)['Amount_USD'].sum()
    df_g['Value_M'] = df_g['Amount_USD'] / 1_000_000
    colors = ['#5D5FEF','#FF947A','#3CD856','#FACC15','#2DD4BF','#A78BFA','#38BDF8']
    fig = px.pie(df_g, names='Department', values='Value_M', hole=0, color_discrete_sequence=colors)
    fig.update_traces(textinfo='none', marker=dict(line=dict(color='#FFFFFF', width=2)),
                      hovertemplate='<b>%{label}</b><br>%{value:,.1f}M<br>%{percent}<extra></extra>')
    fig.update_layout(margin=dict(l=5,r=5,t=5,b=5), height=h,
                      paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                      showlegend=False)
    return opy.plot(fig, auto_open=False, output_type='div',
                    config={'responsive': True, 'displayModeBar': False})

def ceo_get_kpi():
    conn = get_db(DB_ACC)
    rows = conn.execute("SELECT * FROM TodaysSales").fetchall()
    conn.close()
    return {row['Metric']: {'val': row['Value'], 'status': row['Status']} for row in rows}

@app.route("/dashboard")
def ceo_dashboard():
    kpi      = ceo_get_kpi()
    pie_rev  = ceo_get_pie('RevenueDetails', 'TOTAL')
    pie_cost = ceo_get_pie('DetailedExpenses', 'TOTAL')
    return render_template("ceo_dashboard.html", kpi=kpi, pie_rev=pie_rev, pie_cost=pie_cost)

@app.route("/reports")
def ceo_reports():
    return render_template("ceo_reports.html")

@app.route("/settings")
def ceo_settings():
    if 'user_email' not in session:
        return redirect(url_for('login'))

    accounts = get_accounts()
    return render_template("ceo_settings.html", accounts=accounts)

# ================= CRUD ACCOUNT =================

@app.route("/api/create_account", methods=["POST"])
def api_create_account():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    conn = get_db(DB_USER)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO accounts (department_name, email, password, role) VALUES ('', ?, ?, 'department')",
            (email, password)
        )
        conn.commit()
        return jsonify({"message": "Create success"})
    except Exception as e:
        return jsonify({"message": "Error: " + str(e)})
    finally:
        conn.close()


@app.route("/api/update_account", methods=["POST"])
def api_update_account():
    data = request.get_json()

    email = data.get("email")
    department = data.get("department")
    manager = data.get("manager")
    phone = data.get("phone")

    try:
        update_user_info(email, department, manager, phone)
        return jsonify({"message": "Update success"})
    except Exception as e:
        return jsonify({"message": "Error: " + str(e)})


@app.route("/api/delete_account", methods=["POST"])
def api_delete_account():
    data = request.get_json()
    email = data.get("email")

    conn = get_db(DB_USER)
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM accounts WHERE email = ?", (email,))
        cursor.execute("DELETE FROM departments WHERE email = ?", (email,))
        conn.commit()
        return jsonify({"message": "Delete success"})
    except Exception as e:
        return jsonify({"message": "Error: " + str(e)})
    finally:
        conn.close()

# ================= GET ACCOUNT (CHO MODAL UPDATE / DELETE) =================

@app.route("/api/get_account")
def api_get_account():
    email = request.args.get("email")

    conn = get_db(DB_USER)
    cursor = conn.cursor()

    query = """
    SELECT 
        a.email,
        a.password,
        a.department_name AS department,
        d.manager_name AS manager,
        d.phone
    FROM accounts a
    LEFT JOIN departments d ON a.email = d.email
    WHERE a.email = ?
    """

    row = cursor.execute(query, (email,)).fetchone()
    conn.close()

    if row:
        return jsonify(dict(row))
    else:
        return jsonify({})
# ══════════════════════════════════════════════════════════════════
# MARKETING
# ══════════════════════════════════════════════════════════════════

def fmt_money(val):
    val = val or 0
    if val >= 1_000_000_000: return f"{val/1_000_000_000:.1f}B"
    if val >= 1_000_000:     return f"{val/1_000_000:.0f}M"
    if val >= 1_000:         return f"${val/1_000:.0f}k"
    return f"${val:.0f}"

def fmt_pct(val):
    if val is None: return "+0.0%"
    sign = "+" if val >= 0 else ""
    return f"{sign}{val:.1f}%"

@app.route("/mkt")
def mkt_index():
    return redirect(url_for("mkt_dashboard"))

@app.route("/mkt/dashboard")
def mkt_dashboard():
    return render_template("mar_dashboard.html")

@app.route("/mkt/segment")
def mkt_segment():
    return render_template("mar_seg_perform.html")

@app.route("/mkt/campaign")
def mkt_campaign():
    return render_template("mar_cam_perform.html")

@app.route("/mkt/market-share")
def mkt_market_share():
    return render_template("mar_market_share_analysis.html")

@app.route("/mkt/upload")
def mkt_upload():
    return render_template("mar_upload_data.html")

@app.route("/api/dashboard/summary")
def api_dashboard_summary():
    conn = get_db(DB_MKT)
    cur  = conn.cursor()
    cur.execute("SELECT * FROM marketing_daily_summary ORDER BY report_date DESC LIMIT 1")
    today = cur.fetchone()
    cur.execute("SELECT COUNT(*) as cnt FROM recent_campaigns WHERE status='Active'")
    active = cur.fetchone()["cnt"]
    conn.close()
    return jsonify({
        "today_revenue": {"value": fmt_money(today["total_revenue"]) if today else "$0", "change": fmt_pct(today["revenue_change_pct"]) if today else "+0%"},
        "total_clicks":  {"value": f"{today['total_clicks']:,}" if today else "0", "change": fmt_pct(today["clicks_change_pct"]) if today else "+0%"},
        "conversion_rate": {"value": f"{today['conversion_rate']:.1f}%" if today else "0%", "change": fmt_pct(today["conversion_change_pct"]) if today else "+0%"}
    })

@app.route("/api/dashboard/campaigns")
def api_dashboard_campaigns():
    search = request.args.get("search", "")
    conn = get_db(DB_MKT)
    cur  = conn.cursor()
    cur.execute("""
        SELECT campaign_name, status, budget, progress FROM recent_campaigns
        WHERE campaign_name LIKE ?
        ORDER BY CASE status WHEN 'Active' THEN 0 WHEN 'Pending' THEN 1 ELSE 2 END, id DESC
        LIMIT 10
    """, (f"%{search}%",))
    rows = cur.fetchall()
    conn.close()
    return jsonify([{"name": r["campaign_name"], "status": r["status"],
                     "budget": f"${r['budget']:,.0f}", "progress": int(r["progress"] or 0)} for r in rows])

@app.route("/api/dashboard/export")
def api_dashboard_export():
    conn = get_db(DB_MKT)
    cur  = conn.cursor()
    cur.execute("SELECT campaign_name, status, budget, start_date, end_date, clicks_generated, conversions, revenue_generated, progress FROM recent_campaigns ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Campaign Name","Status","Budget","Start","End","Clicks","Conversions","Revenue","Progress%"])
    for r in rows: writer.writerow(list(r))
    filepath = save_to_downloads("campaigns.csv", output.getvalue())
    return jsonify({"success": True, "message": f"File đã lưu tại: {filepath}"})

@app.route("/api/segment/kpis")
def api_segment_kpis():
    conn = get_db(DB_MKT)
    cur  = conn.cursor()
    cur.execute("SELECT report_date FROM segment_daily_performance ORDER BY report_date DESC LIMIT 1")
    row = cur.fetchone()
    today_date = row["report_date"] if row else None
    cur.execute("SELECT SUM(s.revenue) as r, AVG(s.revenue_change_pct) as p FROM segment_daily_performance s JOIN products p ON p.id = s.product_id WHERE s.report_date = ? AND p.segment_id = 1", (today_date,))
    bs = cur.fetchone()
    cur.execute("SELECT SUM(s.units_sold) as u, AVG(s.units_change_pct) as p FROM segment_daily_performance s JOIN products p ON p.id = s.product_id WHERE s.report_date = ? AND p.segment_id = 2", (today_date,))
    sm = cur.fetchone()
    cur.execute("SELECT COUNT(*) as cnt FROM recent_campaigns WHERE status='Active'")
    active = cur.fetchone()["cnt"]
    cur.execute("SELECT conversion_rate, conversion_change_pct FROM marketing_daily_summary ORDER BY report_date DESC LIMIT 1")
    summary = cur.fetchone()
    conn.close()
    return jsonify({
        "best_sellers":    {"value": fmt_money(bs["r"] if bs and bs["r"] else 0), "change": fmt_pct(bs["p"] if bs else None)},
        "slow_movers":     {"value": f"{int(sm['u']) if sm and sm['u'] else 0} units", "change": fmt_pct(sm["p"] if sm else None)},
        "active_campaigns":{"value": f"{active} campaigns", "change": "+0%"},
        "conversion_rate": {"value": f"{summary['conversion_rate']:.1f}%" if summary else "0%", "change": fmt_pct(summary["conversion_change_pct"] if summary else None)}
    })

@app.route("/api/segment/chart")
def api_segment_chart():
    conn = get_db(DB_MKT)
    cur  = conn.cursor()
    cur.execute("SELECT p.product_name, p.segment_id, SUM(s.units_sold) as u, SUM(s.revenue) as r FROM segment_daily_performance s JOIN products p ON p.id = s.product_id GROUP BY p.id ORDER BY p.segment_id, p.id")
    rows = cur.fetchall()
    conn.close()
    return jsonify({"labels": [r["product_name"] for r in rows], "units": [int(r["u"]) for r in rows],
                    "revenue": [float(r["r"]) for r in rows], "segments": [r["segment_id"] for r in rows]})

@app.route("/api/segment/export")
def api_segment_export():
    conn = get_db(DB_MKT)
    cur  = conn.cursor()
    cur.execute("SELECT s.report_date, p.product_name, p.category, seg.segment_name, s.units_sold, s.revenue, s.units_change_pct, s.revenue_change_pct FROM segment_daily_performance s JOIN products p ON p.id = s.product_id JOIN segments seg ON seg.id = p.segment_id ORDER BY s.report_date DESC, p.product_name")
    rows = cur.fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date","Product","Category","Segment","Units Sold","Revenue","Units Change %","Revenue Change %"])
    for r in rows: writer.writerow(list(r))
    filepath = save_to_downloads("segment_performance.csv", output.getvalue())
    return jsonify({"success": True, "message": f"File đã lưu tại: {filepath}"})

@app.route("/api/campaign/kpis")
def api_campaign_kpis():
    conn = get_db(DB_MKT)
    cur  = conn.cursor()
    cur.execute("SELECT SUM(revenue_generated) as total_rev, SUM(budget) as total_bud, COUNT(CASE WHEN status='Active' THEN 1 END) as active FROM recent_campaigns")
    row = cur.fetchone()
    total_rev = row["total_rev"] or 0
    total_bud = row["total_bud"] or 1
    active    = row["active"] or 0
    cur.execute("SELECT SUM(revenue_generated) as r, SUM(budget) as b FROM recent_campaigns WHERE status='Completed'")
    comp = cur.fetchone()
    growth = 0.0
    if comp and comp["b"] and comp["b"] > 0:
        growth = (comp["r"] - comp["b"]) / comp["b"] * 100
    conn.close()
    return jsonify({
        "revenue_growth":   {"value": fmt_pct(growth)},
        "active_campaigns": {"value": f"{active} Campaigns"},
        "roi":              {"value": f"{total_rev/total_bud:.1f}x"}
    })

@app.route("/api/campaign/revenue-over-time")
def api_campaign_revenue():
    conn = get_db(DB_MKT)
    cur  = conn.cursor()
    cur.execute("SELECT revenue_date, SUM(revenue_amount) as total FROM campaign_revenue_daily GROUP BY revenue_date ORDER BY revenue_date ASC")
    rows    = cur.fetchall()
    labels  = [r["revenue_date"] for r in rows]
    revenue = [float(r["total"]) for r in rows]
    cur.execute("SELECT AVG(budget) as avg FROM recent_campaigns")
    avg_bud  = cur.fetchone()["avg"] or 0
    baseline = [round(avg_bud / 30, 2)] * len(labels)
    conn.close()
    return jsonify({"labels": labels, "revenue": revenue, "baseline": baseline,
                    "peak": {"date": labels[revenue.index(max(revenue))] if revenue else None, "value": max(revenue) if revenue else 0}})

@app.route("/api/campaign/export")
def api_campaign_export():
    conn = get_db(DB_MKT)
    cur  = conn.cursor()
    cur.execute("SELECT c.campaign_name, c.status, c.budget, c.start_date, c.end_date, c.clicks_generated, c.conversions, c.revenue_generated, c.progress, COALESCE(SUM(d.revenue_amount), 0) as total_daily_revenue FROM recent_campaigns c LEFT JOIN campaign_revenue_daily d ON d.campaign_id = c.id GROUP BY c.id ORDER BY c.id DESC")
    rows = cur.fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Campaign Name","Status","Budget","Start Date","End Date","Clicks","Conversions","Revenue Generated","Progress %","Total Daily Revenue"])
    for r in rows: writer.writerow(list(r))
    filepath = save_to_downloads("campaign_performance.csv", output.getvalue())
    return jsonify({"success": True, "message": f"File đã lưu tại: {filepath}"})

@app.route("/api/market-share/kpis")
def api_market_share_kpis():
    conn = get_db(DB_MKT)
    cur  = conn.cursor()
    cur.execute("SELECT DISTINCT period FROM market_share_period ORDER BY period DESC LIMIT 2")
    periods = [r["period"] for r in cur.fetchall()]
    cur_p  = periods[0] if periods else None
    prev_p = periods[1] if len(periods) > 1 else None
    cur.execute("SELECT SUM(revenue) as t FROM market_share_period WHERE period=?", (cur_p,))
    cur_t  = cur.fetchone()["t"] or 1
    cur.execute("SELECT SUM(revenue) as t FROM market_share_period WHERE period=?", (prev_p,))
    prev_t = cur.fetchone()["t"] or 1
    trend  = (cur_t - prev_t) / prev_t * 100
    cur.execute("SELECT p.product_name, m.revenue as r FROM market_share_period m JOIN products p ON p.id = m.product_id WHERE m.period = ? ORDER BY m.revenue DESC LIMIT 1", (cur_p,))
    top = cur.fetchone()
    top_growth = 0.0
    if top and prev_p:
        cur.execute("SELECT m.revenue FROM market_share_period m JOIN products p ON p.id = m.product_id WHERE p.product_name = ? AND m.period = ?", (top["product_name"], prev_p))
        pt = cur.fetchone()
        if pt and pt["revenue"]:
            top_growth = (top["r"] - pt["revenue"]) / pt["revenue"] * 100
    conn.close()
    return jsonify({
        "top_product":  {"value": fmt_pct(top_growth), "product": top["product_name"] if top else ""},
        "share_trend":  {"value": fmt_pct(trend)}
    })

@app.route("/api/market-share/pie")
def api_market_share_pie():
    conn = get_db(DB_MKT)
    cur  = conn.cursor()
    cur.execute("SELECT DISTINCT period FROM market_share_period ORDER BY period DESC LIMIT 1")
    row   = cur.fetchone()
    cur_p = row["period"] if row else None
    cur.execute("SELECT p.product_name, m.revenue FROM market_share_period m JOIN products p ON p.id = m.product_id WHERE m.period = ? ORDER BY m.revenue DESC", (cur_p,))
    rows  = cur.fetchall()
    total = sum(r["revenue"] for r in rows) or 1
    conn.close()
    COLORS = ["#7B61FF","#F4A9C0","#4ECDC4","#FFD166","#06D6A0","#FF6B6B"]
    return jsonify({"labels": [r["product_name"] for r in rows],
                    "values": [round(r["revenue"] / total * 100, 1) for r in rows],
                    "colors": [COLORS[i % len(COLORS)] for i in range(len(rows))], "period": cur_p})

@app.route("/api/market-share/export")
def api_market_share_export():
    conn = get_db(DB_MKT)
    cur  = conn.cursor()
    cur.execute("SELECT m.period, p.product_name, p.category, m.revenue, ROUND(m.revenue * 100.0 / SUM(m.revenue) OVER (PARTITION BY m.period), 2) as share_pct FROM market_share_period m JOIN products p ON p.id = m.product_id ORDER BY m.period DESC, m.revenue DESC")
    rows = cur.fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Period","Product","Category","Revenue","Market Share %"])
    for r in rows: writer.writerow(list(r))
    filepath = save_to_downloads("market_share_analysis.csv", output.getvalue())
    return jsonify({"success": True, "message": f"File đã lưu tại: {filepath}"})

@app.route("/api/upload", methods=["POST"])
def api_upload():
    if "file" not in request.files:
        return jsonify({"success": False, "error": "Không tìm thấy file."}), 400
    f = request.files["file"]
    if not (f.filename or "").lower().endswith(".csv"):
        return jsonify({"success": False, "error": "Chỉ chấp nhận file .csv"}), 400
    fb = f.read()
    if not fb:
        return jsonify({"success": False, "error": "File rỗng."}), 400
    rows = list(csv.DictReader(io.StringIO(fb.decode("utf-8-sig"))))
    if not rows:
        return jsonify({"success": False, "error": "CSV không có dữ liệu."}), 400
    conn = get_db(DB_MKT)
    cur  = conn.cursor()
    inserted = skipped = 0
    for row in rows:
        name = (row.get("campaign_name") or row.get("name") or "").strip()
        if not name: skipped += 1; continue
        status = (row.get("status") or "Pending").strip().capitalize()
        if status not in ("Active", "Completed", "Pending"): status = "Pending"
        try:
            cur.execute("INSERT OR IGNORE INTO recent_campaigns (campaign_name, status, budget, start_date, end_date, clicks_generated, conversions, revenue_generated, progress) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (name, status, float(row.get("budget") or 0), row.get("start_date",""), row.get("end_date",""),
                 int(float(row.get("clicks_generated") or 0)), int(float(row.get("conversions") or 0)),
                 float(row.get("revenue_generated") or 0), float(row.get("progress") or 0)))
            inserted += 1
        except Exception: skipped += 1
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": f"Import {inserted} campaigns thành công.", "inserted": inserted, "skipped": skipped, "total": len(rows)})


# ══════════════════════════════════════════════════════════════════
# FINANCE & ACCOUNTING
# ══════════════════════════════════════════════════════════════════

def fmt_m(val):
    if isinstance(val, (int, float)):
        num = val / 1000000
        return "{:,.0f}M".format(num) if num == int(num) else "{:,.1f}M".format(num)
    return val

def acc_make_chart(fig, h=110, ml=0, mr=0, mt=0, mb=0):
    fig.update_layout(margin=dict(l=ml, r=mr, t=mt, b=mb), height=h,
                      paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                      showlegend=False, hoverlabel=dict(font_size=13, font_family="Poppins"))
    return opy.plot(fig, auto_open=False, output_type='div', config={'responsive': True, 'displayModeBar': False})

def acc_get_pie(table, keyword, h=170):
    conn = get_db(DB_ACC)
    df = pd.read_sql_query(f"SELECT Department, Amount_USD FROM {table} WHERE Items != '{keyword}'", conn)
    conn.close()
    if df.empty: return ""
    df_g = df.groupby('Department', as_index=False)['Amount_USD'].sum()
    df_g['Value_M'] = df_g['Amount_USD'] / 1000000
    colors = ['#5D5FEF','#FF947A','#3CD856','#FACC15','#2DD4BF','#A78BFA','#38BDF8']
    fig = px.pie(df_g, names='Department', values='Value_M', hole=0, color_discrete_sequence=colors)
    fig.update_traces(textinfo='none', hoverinfo='label+percent+value',
                      marker=dict(line=dict(color='#FFFFFF', width=2)),
                      hovertemplate='<b>%{label}</b><br>%{value:,.1f}M<br>%{percent}<extra></extra>')
    return acc_make_chart(fig, h=h, ml=5, mr=5, mt=5, mb=5)

def acc_get_line(table, y_col, color_hex):
    conn = get_db(DB_ACC)
    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
    conn.close()
    if df.empty: return ""
    df['Value_M'] = df[y_col] / 1000000
    fig = px.line(df, x='Month', y='Value_M', markers=True, color_discrete_sequence=[color_hex])
    fig.update_traces(fill='tozeroy', fillcolor="rgba(93, 95, 239, 0.1)",
                      hovertemplate='<b>%{x}</b><br>%{y:,.0f}M<extra></extra>')
    fig.update_xaxes(title=None, showgrid=False, tickfont=dict(size=11, color='#737791'))
    fig.update_yaxes(title=None, showgrid=False, showticklabels=False)
    return acc_make_chart(fig, h=120, ml=40, mr=40, mt=15, mb=20)

def acc_cashflow_chart():
    conn = get_db(DB_ACC)
    df = pd.read_sql_query("SELECT * FROM CashFlowForecast", conn)
    conn.close()
    if df.empty: return ""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Quarter'], y=df['Sales_Forecast']/1000, fill='tozeroy', mode='lines+markers', name='Sales', line=dict(color='#38BDF8', width=3), fillcolor='rgba(56,189,248,0.2)', cliponaxis=False))
    fig.add_trace(go.Scatter(x=df['Quarter'], y=df['Expense_Forecast']/1000, fill='tozeroy', mode='lines+markers', name='Expenses', line=dict(color='#FA5A7D', width=3), fillcolor='rgba(250,90,125,0.2)', cliponaxis=False))
    fig.update_layout(margin=dict(l=20,r=20,t=40,b=20), height=250, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="right", x=1))
    fig.update_xaxes(showgrid=False, tickfont=dict(size=11, color='#737791'))
    fig.update_yaxes(showgrid=True, gridcolor='#f1f5f9', tickfont=dict(size=11, color='#737791'))
    return opy.plot(fig, auto_open=False, output_type='div', config={'responsive': True, 'displayModeBar': False})

def acc_double_bar():
    conn = get_db(DB_ACC)
    df = pd.read_sql_query("SELECT * FROM ComparisonData", conn)
    conn.close()
    if df.empty: return ""
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['Month'], y=df['Revenue']/1000, name='Revenue', marker_color='#5D5FEF', text=df['Revenue']/1000, textposition='outside', cliponaxis=False))
    fig.add_trace(go.Bar(x=df['Month'], y=df['Cost']/1000, name='Cost', marker_color='#3CD856', text=df['Cost']/1000, textposition='outside', cliponaxis=False))
    fig.update_layout(barmode='group', margin=dict(l=20,r=20,t=50,b=20), height=250, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5))
    fig.update_xaxes(showgrid=False, tickfont=dict(size=11, color='#737791'))
    fig.update_yaxes(showgrid=True, gridcolor='#f1f5f9', tickfont=dict(size=11, color='#737791'))
    return opy.plot(fig, auto_open=False, output_type='div', config={'responsive': True, 'displayModeBar': False})

def acc_profit_chart():
    conn = get_db(DB_ACC)
    df = pd.read_sql_query("SELECT * FROM ComparisonData", conn)
    conn.close()
    if df.empty: return ""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Month'], y=df['Profit']/1000, fill='tozeroy', mode='lines+markers+text',
                             text=df['Profit']/1000, textposition='top center',
                             textfont=dict(size=12, color='#151D48', weight='bold'),
                             line=dict(color='#A78BFA', shape='spline', width=3), fillcolor='rgba(167,139,250,0.2)', cliponaxis=False))
    fig.update_layout(margin=dict(l=20,r=20,t=50,b=40), height=260, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
    fig.update_xaxes(showgrid=False, tickfont=dict(size=12, color='#737791', weight='bold'))
    fig.update_yaxes(showgrid=True, gridcolor='#f1f5f9', tickfont=dict(size=11, color='#737791'), range=[0, 22], tick0=0, dtick=5)
    return opy.plot(fig, auto_open=False, output_type='div', config={'responsive': True, 'displayModeBar': False})

@app.route("/acc")
def acc_index():
    return redirect(url_for("acc_dashboard"))

@app.route("/acc/dashboard")
def acc_dashboard():
    conn = get_db(DB_ACC)
    kpis = conn.execute("SELECT * FROM TodaysSales").fetchall()
    conn.close()
    kpi_dict = {row['Metric']: {'val': row['Value'], 'status': row['Status']} for row in kpis}
    return render_template("acc_dashboard.html", kpi=kpi_dict,
                           pie_rev=acc_get_pie('RevenueDetails','TOTAL',180),
                           pie_cost=acc_get_pie('DetailedExpenses','TOTAL',180))

@app.route("/acc/total-cost")
def acc_total_cost():
    conn = get_db(DB_ACC)
    summary   = conn.execute("SELECT * FROM TotalCostOverview").fetchone()
    items     = conn.execute("SELECT * FROM DetailedExpenses WHERE Items != 'TOTAL'").fetchall()
    total_row = conn.execute("SELECT * FROM DetailedExpenses WHERE Items = 'TOTAL'").fetchone()
    conn.close()
    return render_template("acc_total_cost.html", summary=summary, items=items, total_row=total_row,
                           pie_chart=acc_get_pie('DetailedExpenses','TOTAL',170), fmt_m=fmt_m)

@app.route("/acc/total-revenue")
def acc_total_revenue():
    conn = get_db(DB_ACC)
    summary   = conn.execute("SELECT * FROM TotalRevenueOverview").fetchone()
    items     = conn.execute("SELECT * FROM RevenueDetails WHERE Items != 'TOTAL'").fetchall()
    total_row = conn.execute("SELECT * FROM RevenueDetails WHERE Items = 'TOTAL'").fetchone()
    conn.close()
    return render_template("acc_total_revenue.html", summary=summary, items=items, total_row=total_row,
                           pie_chart=acc_get_pie('RevenueDetails','TOTAL',170),
                           line_chart=acc_get_line('MonthlyRevenue','Revenue_USD','#3CD856'), fmt_m=fmt_m)

@app.route("/acc/finance-report")
def acc_finance_report():
    return render_template("acc_fin_report.html", rev_cost_bar=acc_double_bar(),
                           cf_line=acc_cashflow_chart(), profit_bar=acc_profit_chart())

@app.route("/acc/documents")
def acc_documents():
    return render_template("acc_docs.html")

@app.route("/acc/export-dashboard")
def acc_export_dashboard():
    conn = get_db(DB_ACC)
    items = conn.execute("SELECT * FROM TodaysSales").fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Metric","Value","Growth Status"])
    for p in items: writer.writerow(list(p))
    filepath = save_to_downloads("finance_overview.csv", output.getvalue())
    return jsonify({"success": True, "message": f"File đã lưu tại: {filepath}"})

@app.route("/acc/export-total-cost")
def acc_export_total_cost():
    conn = get_db(DB_ACC)
    items = conn.execute("SELECT * FROM DetailedExpenses").fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date","Items","Department","Amount_USD"])
    for r in items: writer.writerow(list(r))
    filepath = save_to_downloads("total_cost.csv", output.getvalue())
    return jsonify({"success": True, "message": f"File đã lưu tại: {filepath}"})

@app.route("/acc/export-total-revenue")
def acc_export_total_revenue():
    conn = get_db(DB_ACC)
    items = conn.execute("SELECT * FROM RevenueDetails").fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date","Items","Department","Amount_USD"])
    for r in items: writer.writerow(list(r))
    filepath = save_to_downloads("total_revenue.csv", output.getvalue())
    return jsonify({"success": True, "message": f"File đã lưu tại: {filepath}"})

@app.route("/acc/export-finance-report")
def acc_export_finance_report():
    conn = get_db(DB_ACC)
    items = conn.execute("SELECT * FROM ComparisonData").fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Month","Revenue","Cost","Profit"])
    for r in items: writer.writerow(list(r))
    filepath = save_to_downloads("finance_report.csv", output.getvalue())
    return jsonify({"success": True, "message": f"File đã lưu tại: {filepath}"})


# ══════════════════════════════════════════════════════════════════
# INVENTORY
# ══════════════════════════════════════════════════════════════════

def fmt_inv(val):
    return "{:,.0f}".format(val).replace(',', '.') if val else "0"

def inv_stock_chart():
    conn = get_db(DB_INV)
    df = pd.read_sql_query("SELECT * FROM StockQuantity", conn)
    conn.close()
    if df.empty: return ""
    df['Imported'] = df['Sold'] + df['InStock']
    fig = px.bar(df, x='Week', y=['Imported','Sold','InStock'], barmode='group',
                 color_discrete_sequence=['#4aa8ff','#22c55e','#f472b6'])
    fig.update_layout(margin=dict(l=10,r=10,t=10,b=10), height=210,
                      paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    return opy.plot(fig, auto_open=False, output_type='div')

@app.route("/inv")
def inv_index():
    return redirect(url_for("inv_dashboard"))

@app.route("/inv/dashboard")
def inv_dashboard():
    conn = get_db(DB_INV)
    rows   = conn.execute("SELECT * FROM InventoryOverview").fetchall()
    ov     = {row['TieuDe']: fmt_inv(row['SoLieu']) for row in rows}
    alerts = conn.execute("SELECT * FROM LowStockAlert").fetchall()
    conn.close()
    return render_template("inv_dashboard.html", ov=ov, alerts=alerts)

@app.route("/inv/products")
def inv_products():
    conn = get_db(DB_INV)
    items = conn.execute("SELECT * FROM AllProducts").fetchall()
    conn.close()
    return render_template("inv_productlist.html", items=items, fmt=fmt_inv, chart=inv_stock_chart())

@app.route("/inv/suppliers")
def inv_suppliers():
    conn = get_db(DB_INV)
    sups = conn.execute("SELECT * FROM Suppliers").fetchall()
    conn.close()
    return render_template("inv_supplier.html", sups=sups)

@app.route("/inv/export")
def inv_export():
    conn = get_db(DB_INV)
    items = conn.execute("SELECT * FROM AllProducts").fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Product Name","SKU","Stock","Price"])
    for p in items: writer.writerow(list(p))
    filepath = save_to_downloads("lemonade_inventory.csv", output.getvalue())
    return jsonify({"success": True, "message": f"File đã lưu tại: {filepath}"})


# ══════════════════════════════════════════════════════════════════
# SALES
# ══════════════════════════════════════════════════════════════════

def sales_get_data():
    conn = sqlite3.connect(DB_SALE)
    summary_df  = pd.read_sql_query("SELECT SUM(units_sold) as total_units, SUM(revenue) as total_rev FROM sales_transactions", conn)
    units_sold  = summary_df['total_units'][0]
    total_revenue = summary_df['total_rev'][0]
    top_prod_df = pd.read_sql_query("SELECT p.product_name FROM sales_transactions s JOIN products p ON s.product_id = p.id GROUP BY p.product_name ORDER BY SUM(s.units_sold) DESC LIMIT 1", conn)
    top_product = top_prod_df['product_name'][0]
    target_df   = pd.read_sql_query("SELECT target_revenue FROM sales_targets WHERE year = '2026'", conn)
    target      = target_df['target_revenue'][0]
    kpi_percent = round((total_revenue / target) * 100) if target > 0 else 0
    cust_df     = pd.read_sql_query("SELECT customer_id, COUNT(id) as total_orders FROM sales_transactions GROUP BY customer_id", conn)
    total_cust  = len(cust_df)
    vips        = len(cust_df[cust_df['total_orders'] >= 5])
    returnings  = len(cust_df[(cust_df['total_orders'] >= 2) & (cust_df['total_orders'] <= 4)])
    news        = len(cust_df[cust_df['total_orders'] <= 1])
    vip_per  = round((vips / total_cust) * 100) if total_cust > 0 else 0
    ret_per  = round((returnings / total_cust) * 100) if total_cust > 0 else 0
    new_per  = round((news / total_cust) * 100) if total_cust > 0 else 0
    trend_html = sales_trend_chart(conn)
    conn.close()
    return {"units": f"{units_sold:,}", "revenue": f"{total_revenue:,.0f} đ",
            "top_prod": top_product, "kpi": f"{kpi_percent}%",
            "customer_stats": {"vip": vip_per, "returning": ret_per, "new": new_per},
            "trend_chart": trend_html}

def sales_trend_chart(conn):
    df = pd.read_sql_query("SELECT strftime('%m', sale_date) as month_num, SUM(units_sold) as total FROM sales_transactions GROUP BY month_num ORDER BY month_num ASC", conn)
    if df.empty: return "No data available"
    fig = px.line(df, x='month_num', y='total', markers=True, labels={'month_num':'Tháng','total':'Sản phẩm'}, template="plotly_white")
    fig.update_traces(line_color='#3b82f6', fill='tozeroy', line_shape="spline")
    fig.update_layout(margin=dict(l=20,r=20,t=20,b=20), height=300)
    return opy.plot(fig, auto_open=False, output_type='div')

def sales_top5(conn, search_query=""):
    df = pd.read_sql_query("SELECT p.product_name, SUM(s.units_sold) as total_units FROM sales_transactions s JOIN products p ON s.product_id = p.id GROUP BY p.product_name ORDER BY total_units DESC LIMIT 5", conn)
    if search_query:
        df = df[df['product_name'].str.contains(search_query, case=False, na=False)]
    if df.empty: return "<div style='padding:20px;text-align:center;'>Không có dữ liệu khớp</div>"
    fig = px.bar(df, x='product_name', y='total_units', text='total_units',
                 labels={'product_name':'Product Name','total_units':'Units'},
                 color='total_units', color_continuous_scale='PuRd')
    fig.update_traces(textposition='outside', marker_line_color='rgb(8,48,107)', marker_line_width=1.5, opacity=0.8)
    fig.update_yaxes(range=[0, df['total_units'].max() * 1.15])
    fig.update_layout(margin=dict(t=40,b=0,l=0,r=0), plot_bgcolor='rgba(0,0,0,0)',
                      paper_bgcolor='rgba(0,0,0,0)', xaxis_title="", yaxis_title="Units Sold",
                      showlegend=False, transition={'duration': 1000})
    return opy.plot(fig, auto_open=False, output_type='div')

def sales_slow_moving(conn, search_query=""):
    df_all = pd.read_sql_query("SELECT p.product_name, SUM(s.units_sold) as total_units FROM sales_transactions s JOIN products p ON s.product_id = p.id GROUP BY p.product_name ORDER BY total_units ASC", conn)
    num_bottom = max(1, math.ceil(len(df_all) * 0.3))
    df_bottom  = df_all.head(num_bottom).copy()
    df_monthly = pd.read_sql_query("SELECT p.product_name, strftime('%m', s.sale_date) as month, SUM(s.units_sold) as units FROM sales_transactions s JOIN products p ON s.product_id = p.id WHERE month IN ('11','12') GROUP BY p.product_name, month", conn)
    if not df_monthly.empty:
        df_pivot = df_monthly.pivot(index='product_name', columns='month', values='units').fillna(0)
        if '11' not in df_pivot: df_pivot['11'] = 0
        if '12' not in df_pivot: df_pivot['12'] = 0
        df_pivot['growth'] = (df_pivot['12'] - df_pivot['11']) / df_pivot['11'].replace(0, 1)
        df_final = df_bottom.merge(df_pivot[['growth']], on='product_name', how='left').fillna(0)
    else:
        df_final = df_bottom
        df_final['growth'] = 0
    def classify(g):
        p = g * 100
        if p < -10: return 'low'
        elif p <= 10: return 'stable'
        return 'improving'
    df_final['status'] = df_final['growth'].apply(classify)
    if search_query:
        df_final = df_final[df_final['product_name'].str.contains(search_query, case=False, na=False)]
    return df_final.to_dict(orient='records')

@app.route("/sales")
def sales_index():
    search_query = request.args.get('q', '').strip()
    conn = sqlite3.connect(DB_SALE)
    try:
        top5 = sales_top5(conn)
        data = sales_get_data()
        data['slow_prods'] = sales_slow_moving(conn, search_query)
        return render_template('sales.html', d=data, top5=top5, search_query=search_query)
    except Exception as e:
        return f"Lỗi hệ thống: {e}"
    finally:
        conn.close()


# ══════════════════════════════════════════════════════════════════
# KHỞI CHẠY ỨNG DỤNG
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import threading
    import webview
    import time

    def run_flask():
        app.run(debug=False, port=5000, use_reloader=False)

    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()
    time.sleep(1)

    webview.create_window(
        "Lemonade – Business Management",
        "http://127.0.0.1:5000/login",
        width=1366,
        height=768,
        resizable=True
    )
    webview.start()

