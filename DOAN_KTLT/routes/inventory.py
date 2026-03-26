from flask import Blueprint, render_template, jsonify, redirect
import pandas as pd
import plotly.express as px
import plotly.offline as opy
import csv, io
from routes.utils import DB_INV, get_db, save_to_downloads

inv_bp = Blueprint('inv_bp', __name__)

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

@inv_bp.route("/inv")
def inv_index():
    return redirect("/inv/dashboard")

@inv_bp.route("/inv/dashboard")
def inv_dashboard():
    conn = get_db(DB_INV)
    rows   = conn.execute("SELECT * FROM InventoryOverview").fetchall()
    ov     = {row['TieuDe']: fmt_inv(row['SoLieu']) for row in rows}
    alerts = conn.execute("SELECT * FROM LowStockAlert").fetchall()
    conn.close()
    return render_template("inv_dashboard.html", ov=ov, alerts=alerts)

@inv_bp.route("/inv/products")
def inv_products():
    conn = get_db(DB_INV)
    items = conn.execute("SELECT * FROM AllProducts").fetchall()
    conn.close()
    return render_template("inv_productlist.html", items=items, fmt=fmt_inv, chart=inv_stock_chart())

@inv_bp.route("/inv/suppliers")
def inv_suppliers():
    conn = get_db(DB_INV)
    sups = conn.execute("SELECT * FROM Suppliers").fetchall()
    conn.close()
    return render_template("inv_supplier.html", sups=sups)

@inv_bp.route("/inv/export")
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