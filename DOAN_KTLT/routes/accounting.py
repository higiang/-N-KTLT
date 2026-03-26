from flask import Blueprint, render_template, jsonify, redirect
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.offline as opy
import csv, io
from .utils import DB_ACC, get_db, save_to_downloads

acc_bp = Blueprint('acc_bp', __name__)

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

    if df.empty:
        return ""

    # ✅ giữ đúng thứ tự quý (KHÔNG fill 0)
    quarter_order = ['Q1', 'Q2', 'Q3', 'Q4']
    df['Quarter'] = pd.Categorical(df['Quarter'], categories=quarter_order, ordered=True)
    df = df.sort_values('Quarter')

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df['Quarter'],
        y=df['Sales_Forecast']/1000,
        mode='lines+markers',
        name='Sales',
        line=dict(color='#38BDF8', width=3),
        marker=dict(size=6),
        connectgaps=True   # 🔥 QUAN TRỌNG: nối line nếu thiếu data
    ))

    fig.add_trace(go.Scatter(
        x=df['Quarter'],
        y=df['Expense_Forecast']/1000,
        mode='lines+markers',
        name='Expenses',
        line=dict(color='#FA5A7D', width=3),
        marker=dict(size=6),
        connectgaps=True
    ))

    # ✅ FIX KHUNG LUÔN
    fig.update_xaxes(
        type='category',
        categoryorder='array',
        categoryarray=quarter_order,
        showgrid=False,
        tickfont=dict(size=11, color='#737791')
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor='#f1f5f9',
        tickfont=dict(size=11, color='#737791'),
        rangemode='tozero'   # luôn bắt đầu từ 0
    )

    fig.update_layout(
        margin=dict(l=20,r=20,t=40,b=20),
        height=260,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="right",
            x=1
        )
    )

    return opy.plot(
        fig,
        auto_open=False,
        output_type='div',
        config={'responsive': True, 'displayModeBar': False}
    )

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

@acc_bp.route("/acc")
def acc_index():
    return redirect("/acc/dashboard")

@acc_bp.route("/acc/dashboard")
def acc_dashboard():
    conn = get_db(DB_ACC)
    kpis = conn.execute("SELECT * FROM TodaysSales").fetchall()
    conn.close()
    kpi_dict = {row['Metric']: {'val': row['Value'], 'status': row['Status']} for row in kpis}
    return render_template("acc_dashboard.html", kpi=kpi_dict,
                           pie_rev=acc_get_pie('RevenueDetails','TOTAL',180),
                           pie_cost=acc_get_pie('DetailedExpenses','TOTAL',180))

@acc_bp.route("/acc/total-cost")
def acc_total_cost():
    conn = get_db(DB_ACC)
    summary   = conn.execute("SELECT * FROM TotalCostOverview").fetchone()
    items     = conn.execute("SELECT * FROM DetailedExpenses WHERE Items != 'TOTAL'").fetchall()
    total_row = conn.execute("SELECT * FROM DetailedExpenses WHERE Items = 'TOTAL'").fetchone()
    conn.close()
    return render_template("acc_total_cost.html", summary=summary, items=items, total_row=total_row,
                           pie_chart=acc_get_pie('DetailedExpenses','TOTAL',170), fmt_m=fmt_m)

@acc_bp.route("/acc/total-revenue")
def acc_total_revenue():
    conn = get_db(DB_ACC)
    summary   = conn.execute("SELECT * FROM TotalRevenueOverview").fetchone()
    items     = conn.execute("SELECT * FROM RevenueDetails WHERE Items != 'TOTAL'").fetchall()
    total_row = conn.execute("SELECT * FROM RevenueDetails WHERE Items = 'TOTAL'").fetchone()
    conn.close()
    return render_template("acc_total_revenue.html", summary=summary, items=items, total_row=total_row,
                           pie_chart=acc_get_pie('RevenueDetails','TOTAL',170),
                           line_chart=acc_get_line('MonthlyRevenue','Revenue_USD','#3CD856'), fmt_m=fmt_m)

@acc_bp.route("/acc/finance-report")
def acc_finance_report():
    return render_template("acc_fin_report.html", rev_cost_bar=acc_double_bar(),
                           cf_line=acc_cashflow_chart(), profit_bar=acc_profit_chart())

@acc_bp.route("/acc/documents")
def acc_documents():
    return render_template("acc_docs.html")

@acc_bp.route("/acc/export-dashboard")
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

@acc_bp.route("/acc/export-total-cost")
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

@acc_bp.route("/acc/export-total-revenue")
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

@acc_bp.route("/acc/export-finance-report")
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