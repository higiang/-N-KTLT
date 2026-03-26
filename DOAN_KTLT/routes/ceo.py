from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.offline as opy
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from .utils import DB_ACC, DB_USER, get_db, update_user_info

ceo_bp = Blueprint('ceo_bp', __name__)



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

@ceo_bp.route("/dashboard")
def ceo_dashboard():
    kpi      = ceo_get_kpi()
    pie_rev  = ceo_get_pie('RevenueDetails', 'TOTAL')
    pie_cost = ceo_get_pie('DetailedExpenses', 'TOTAL')
    return render_template("ceo_dashboard.html", kpi=kpi, pie_rev=pie_rev, pie_cost=pie_cost)

@ceo_bp.route("/reports")
def ceo_reports():
    return render_template("ceo_reports.html")



def get_accounts():
    conn = get_db(DB_USER)
    cursor = conn.cursor()
    query = """
    SELECT a.id, d.manager_name AS manager, a.department_name AS department,
           a.email, a.password, d.phone, a.role
    FROM accounts a
    LEFT JOIN departments d ON a.email = d.email
    """
    rows = cursor.execute(query).fetchall()
    conn.close()
    return rows

@ceo_bp.route("/settings")
def ceo_settings():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    accounts = get_accounts()
    return render_template("ceo_settings.html", accounts=accounts)

@ceo_bp.route("/api/create_account", methods=["POST"])
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

@ceo_bp.route("/api/update_account", methods=["POST"])
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

@ceo_bp.route("/api/delete_account", methods=["POST"])
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

@ceo_bp.route("/api/get_account")
def api_get_account():
    email = request.args.get("email")
    conn = get_db(DB_USER)
    cursor = conn.cursor()
    query = """
    SELECT a.email, a.password, a.department_name AS department, d.manager_name AS manager, d.phone
    FROM accounts a
    LEFT JOIN departments d ON a.email = d.email
    WHERE a.email = ?
    """
    row = cursor.execute(query, (email,)).fetchone()
    conn.close()
    if row:
        return jsonify(dict(row))
    return jsonify({})

@ceo_bp.route("/api/forecast")
def forecast_revenue():
    conn = get_db(DB_ACC)
    df = pd.read_sql_query("SELECT * FROM MonthlyRevenue", conn)
    conn.close()
    if len(df) < 2:
        return jsonify({"forecast": "N/A", "month": "", "r2": "N/A"})
    X = np.array(range(len(df))).reshape(-1, 1)
    y = df['Revenue_USD'].values
    model = LinearRegression().fit(X, y)
    next_val = model.predict([[len(df)]])[0]
    r2 = r2_score(y, model.predict(X))
    return jsonify({
        "forecast": f"${next_val:,.0f} USD",
        "month": f"Tháng {len(df) + 1}",
        "r2": f"{r2:.2f}"
    })