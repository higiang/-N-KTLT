import sqlite3, os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.offline as opy
from flask import render_template, request, redirect, url_for, session, jsonify
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score

class AuthCeoExt:
    def get_db(self, path):
        conn = sqlite3.connect(path)
        conn.row_factory = sqlite3.Row
        return conn

    def save_to_downloads(self, filename, content):
        downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        os.makedirs(downloads, exist_ok=True)
        filepath = os.path.join(downloads, filename)
        with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
            f.write(content)
        return filepath

    def inject_global_variables(self):
        is_admin = False
        if 'user_email' in session:
            user = self.get_account_from_db(session['user_email'])
            if user and user.get('role') == 'admin':
                is_admin = True
        return dict(is_admin=is_admin)

    # --- AUTH & USERS ---
    def index(self):
        return redirect(url_for("login"))

    def get_account_from_db(self, email):
        conn = self.get_db(self.DB_USER)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM accounts WHERE email = ?", (email,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_full_user_info(self, email):
        conn = self.get_db(self.DB_USER)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT a.email, a.password, a.role, a.department_name AS department, d.manager_name AS manager, d.phone
            FROM accounts a LEFT JOIN departments d ON a.email = d.email WHERE a.email = ?
        """, (email,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def add_user_to_db(self, email, password, role='department', created_by=''):
        conn = self.get_db(self.DB_USER)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO accounts (department_name, email, password, role, created_by) VALUES ('', ?, ?, ?, ?)",
                (email, password, role, created_by)
            )
            conn.commit()
            success = True
        except sqlite3.IntegrityError:
            success = False
        finally:
            conn.close()
        return success

    def update_user_info_db(self, email, department, manager, phone):
        conn = self.get_db(self.DB_USER)
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE accounts SET department_name = ? WHERE email = ?", (department, email))
            cursor.execute("SELECT password FROM accounts WHERE email = ?", (email,))
            pwd_row = cursor.fetchone()
            password = pwd_row[0] if pwd_row else ''
            cursor.execute("SELECT email FROM departments WHERE email = ?", (email,))
            if cursor.fetchone():
                cursor.execute("UPDATE departments SET department_name = ?, manager_name = ?, phone = ? WHERE email = ?", (department, manager, phone, email))
            else:
                cursor.execute("INSERT INTO departments (department_name, manager_name, phone, email, password) VALUES (?, ?, ?, ?, ?)", (department, manager, phone, email, password))
            conn.commit()
        except Exception as e:
            print("Lỗi update database:", e)
        finally:
            conn.close()

    def login(self):
        error = None
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            form_role = request.form.get('role')
            user = self.get_account_from_db(email)
            if user:
                if user['password'] == password:
                    db_role = user.get('role')
                    if form_role == 'user' and db_role != 'department':
                        error = "This account does not have user privileges."
                    elif form_role == 'admin' and db_role != 'admin':
                        error = "This account does not have admin privileges."
                    else:
                        session['user_email'] = user['email']
                        return redirect(url_for('user_info'))
                else:
                    error = "Email or password is incorrect."
            else:
                error = "Email has not been registered."
        return render_template('log_in.html', error=error)

    def signup(self):
        error = None
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            if not email or not password:
                error = "Please enter all the required information."
            elif password != confirm_password:
                error = "Password doesn't match"
            else:
                if self.add_user_to_db(email, password, role='admin', created_by=email):
                    return redirect(url_for('login'))
                else:
                    error = "This email is already registered"
        return render_template('sign_up.html', error=error)

    def user_info(self):
        if 'user_email' not in session: return redirect(url_for('login'))
        current_email = session['user_email']
        if request.method == 'POST':
            self.update_user_info_db(current_email, request.form.get('department'), request.form.get('manager'), request.form.get('phone'))
            user = self.get_account_from_db(current_email)
            dept = user.get('department_name', '') if user else ''
            role = user.get('role', '') if user else ''
            if role == 'admin':
                    if user and user.get('created_by') == current_email:
                        return redirect('/settings')
                    return redirect('/dashboard')
            DEPT_ROUTES = {'marketing_department': '/mkt/dashboard', 'inventory_department': '/inv/dashboard', 'sales_department': '/sales', 'accounting_n_finance_department': '/acc/dashboard'}
            target = DEPT_ROUTES.get(dept)
            if target: return redirect(target)
        user_data = self.get_full_user_info(current_email)
        if not user_data: return redirect(url_for('logout'))
        return render_template('user_info.html', user=user_data)

    def logout(self):
        session.pop('user_email', None)
        return redirect(url_for('login'))

    def signout(self):
        session.pop('user_email', None)
        return redirect(url_for('login'))

    # --- CEO DASHBOARD ---
    def ceo_get_pie(self, table, keyword, value_col, h=170):
        conn = self.get_db(self.DB_ACC)
        df = pd.read_sql_query(f"SELECT Department, {value_col} FROM {table} WHERE Items != '{keyword}'", conn)
        conn.close()
        if df.empty: return ""
        df[value_col] = df[value_col].astype(str).str.replace(',', '').astype(float)
        df_g = df.groupby('Department', as_index=False)[value_col].sum()
        df_g['Value_M'] = df_g[value_col] / 1_000_000
        colors = ['#5D5FEF', '#FF947A', '#3CD856', '#FACC15', '#2DD4BF', '#A78BFA', '#38BDF8']
        fig = px.pie(df_g, names='Department', values='Value_M', hole=0, color_discrete_sequence=colors)
        fig.update_traces(textinfo='none', marker=dict(line=dict(color='#FFFFFF', width=2)), hovertemplate='<b>%{label}</b><br>%{value:,.1f}M<br>%{percent}<extra></extra>')
        fig.update_layout(margin=dict(l=5, r=5, t=5, b=5), height=h, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
        return opy.plot(fig, auto_open=False, output_type='div', config={'responsive': True, 'displayModeBar': False})

    def ceo_get_kpi(self):
        conn = self.get_db(self.DB_ACC)
        rows = conn.execute("SELECT * FROM TodaysSales").fetchall()
        conn.close()
        return {str(row['Metric']).strip(): {'val': row['Value'], 'status': row['Status']} for row in rows}

    def ceo_dashboard(self):
        if 'user_email' not in session: return redirect(url_for('login'))

        # 1. Lấy KPI gốc từ bảng TodaysSales
        kpi = self.ceo_get_kpi()

        # 2. TRUY VẤN TỔNG THỰC TẾ (Dùng SQL SUM )
        conn = self.get_db(self.DB_ACC)
        try:
            # dọn dẹp dấu phẩy và ép kiểu để tính tổng
            res = conn.execute("""
                SELECT SUM(CAST(REPLACE(REPLACE(Amount_VND, ',', ''), 'VND', '') AS FLOAT)) 
                FROM DetailedExpenses 
                WHERE Items NOT LIKE '%TOTAL%'
            """).fetchone()
            actual_total_cost = res[0] if res[0] else 0
        except Exception as e:
            print(f"--- [LỖI SQL] ---: {e}")
            actual_total_cost = 0
        finally:
            conn.close()

        display_number = f"{actual_total_cost / 1_000_000:,.0f}M"

        # In ra màn hình đen (Terminal) để kiểm tra
        print(f"--- [DEBUG] CEO DASHBOARD LOADED - ACTUAL COST: {display_number} ---")

        # 3. ÉP GHI ĐÈ VÀO DICTIONARY (Bất kể database có gì)
        kpi['Total Cost'] = {'val': display_number, 'status': 'Updated'}

        pie_rev = self.ceo_get_pie('RevenueDetails', 'TOTAL', 'Amount_VND')
        pie_cost = self.ceo_get_pie('DetailedExpenses', 'TOTAL', 'Amount_VND')

        return render_template("ceo_dashboard.html", kpi=kpi,
                               pie_rev=pie_rev, pie_cost=pie_cost,
                               is_admin=session.get('is_admin'))

    def ceo_reports(self):
        return render_template("ceo_reports.html")

    def get_accounts(self, owner_email):
        conn = self.get_db(self.DB_USER)
        rows = conn.execute(
            """SELECT a.id, d.manager_name AS manager, a.department_name AS department,
                      a.email, a.password, d.phone, a.role
               FROM accounts a LEFT JOIN departments d ON a.email = d.email
               WHERE a.created_by = ?""",   # thêm điều kiện lọc theo owner
            (owner_email,)
        ).fetchall()
        conn.close()
        return rows

    def ceo_settings(self):
        if 'user_email' not in session: return redirect(url_for('login'))
        current_email = session['user_email']
        user = self.get_account_from_db(current_email)

        # Xác định xem đây có phải là CEO mới tự đăng ký không
        is_new_ceo = bool(user and user.get('created_by') == current_email)

        # Lấy danh sách tài khoản thuộc về CEO này
        accounts = self.get_accounts(current_email)

        # Gom tất cả tên phòng ban thành 1 chuỗi chữ thường để tìm từ khóa
        all_depts_str = " ".join([str(acc['department']).lower().strip() for acc in accounts if acc['department']])

        return render_template("ceo_settings.html",
                               accounts=accounts,
                               is_new_ceo=is_new_ceo,
                               all_depts_str=all_depts_str)
    def api_create_account(self):
        data = request.get_json()
        owner = session.get('user_email', '')  # Lấy email của CEO đang đăng nhập

        # Lấy đầy đủ thông tin từ giao diện
        email = data.get("email")
        password = data.get("password")
        department = data.get("department", "")
        manager = data.get("manager", "")
        phone = data.get("phone", "")

        conn = self.get_db(self.DB_USER)
        try:
            # 1. Lưu email, mật khẩu và department_name vào bảng accounts
            conn.execute(
                "INSERT INTO accounts (department_name, email, password, role, created_by) VALUES (?, ?, ?, 'department', ?)",
                (department, email, password, owner)
            )
            conn.commit()

            # 2. Gọi hàm đồng bộ thông tin sang bảng departments để lưu manager và phone
            self.update_user_info_db(email, department, manager, phone)

            return jsonify({"message": "Create success"})
        except Exception as e:
            return jsonify({"message": "Error: " + str(e)})
        finally:
            conn.close()
    def api_update_account(self):
        data = request.get_json()
        try:
            self.update_user_info_db(data.get("email"), data.get("department"), data.get("manager"), data.get("phone"))
            return jsonify({"message": "Update success"})
        except Exception as e:
            return jsonify({"message": "Error: " + str(e)})

    def api_delete_account(self):
        data = request.get_json()
        email = data.get("email")
        conn = self.get_db(self.DB_USER)
        try:
            conn.execute("DELETE FROM accounts WHERE email = ?", (email,))
            conn.execute("DELETE FROM departments WHERE email = ?", (email,))
            conn.commit()
            return jsonify({"message": "Delete success"})
        except Exception as e:
            return jsonify({"message": "Error: " + str(e)})
        finally:
            conn.close()

    def api_get_account(self):
        email = request.args.get("email")
        conn = self.get_db(self.DB_USER)
        row = conn.execute("SELECT a.email, a.password, a.department_name AS department, d.manager_name AS manager, d.phone FROM accounts a LEFT JOIN departments d ON a.email = d.email WHERE a.email = ?", (email,)).fetchone()
        conn.close()
        return jsonify(dict(row)) if row else jsonify({})

    def forecast_revenue(self):
        conn = self.get_db(self.DB_ACC)
        df = pd.read_sql_query("SELECT Month, Revenue_VND FROM MonthlyRevenue", conn)
        conn.close()
        if df.empty or len(df) < 2: return jsonify({'forecast': '--', 'month': 'No data', 'r2': '--'})
        df['Month_Num'] = np.arange(1, len(df) + 1)
        X, y = df[['Month_Num']].values, df['Revenue_VND'].values
        model = LinearRegression()
        model.fit(X, y)
        pred_val = model.predict(np.array([[len(df) + 1]]))[0]
        r2 = r2_score(y, model.predict(X))
        last_month_str = df['Month'].iloc[-1]
        months_order = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        next_m_str = months_order[(months_order.index(last_month_str) + 1) % 12] if last_month_str in months_order else "Next Month"
        return jsonify({'forecast': f"{pred_val / 1000000:,.1f}M", 'month': next_m_str, 'r2': f"{r2:.2f}"})