import sqlite3, csv, io
import pandas as pd
import plotly.express as px
import plotly.offline as opy
from flask import render_template, jsonify, redirect, url_for

class InventoryExt:
    def fmt_inv(self, val):
        return "{:,.0f}".format(val).replace(',', '.') if val else "0"

    def inv_stock_chart(self):
        conn = self.get_db(self.DB_INV)
        df = pd.read_sql_query("SELECT * FROM StockQuantity", conn)
        conn.close()
        if df.empty: return ""
        df['Imported'] = df['Sold'] + df['InStock']
        fig = px.bar(df, x='Week', y=['Imported','Sold','InStock'], barmode='group', color_discrete_sequence=['#4aa8ff','#22c55e','#f472b6'])
        fig.update_layout(margin=dict(l=10,r=10,t=10,b=10), height=210, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        return opy.plot(fig, auto_open=False, output_type='div')

    def inv_index(self):
        return redirect(url_for("inv_dashboard"))

    def inv_dashboard(self):
        conn = self.get_db(self.DB_INV)
        rows   = conn.execute("SELECT * FROM InventoryOverview").fetchall()
        ov     = {row['TieuDe']: self.fmt_inv(row['SoLieu']) for row in rows}
        alerts = conn.execute("SELECT * FROM LowStockAlert").fetchall()
        conn.close()
        return render_template("inv_dashboard.html", ov=ov, alerts=alerts)

    def inv_products(self):
        conn = self.get_db(self.DB_INV)
        items = conn.execute("SELECT * FROM AllProducts").fetchall()
        conn.close()
        return render_template("inv_productlist.html", items=items, fmt=self.fmt_inv, chart=self.inv_stock_chart())

    def inv_suppliers(self):
        conn = self.get_db(self.DB_INV)
        sups = conn.execute("SELECT * FROM Suppliers").fetchall()
        conn.close()
        return render_template("inv_supplier.html", sups=sups)

    def inv_export(self):
        conn = self.get_db(self.DB_INV)
        items = conn.execute("SELECT * FROM AllProducts").fetchall()
        conn.close()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Product Name","SKU","Stock","Price"])
        for p in items: writer.writerow(list(p))
        filepath = self.save_to_downloads("lemonade_inventory.csv", output.getvalue())
        return jsonify({"success": True, "message": f"File đã lưu tại: {filepath}"})