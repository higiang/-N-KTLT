import sqlite3, math
import pandas as pd
import plotly.express as px
import plotly.offline as opy
from flask import render_template, request

class SalesExt:
    def sales_get_data(self):
        conn = sqlite3.connect(self.DB_SALE)
        summary_df = pd.read_sql_query("SELECT SUM(units_sold) as total_units, SUM(revenue) as total_rev FROM sales_transactions", conn)
        units_sold = summary_df['total_units'][0]
        total_revenue = summary_df['total_rev'][0]
        top_prod_df = pd.read_sql_query("SELECT p.product_name FROM sales_transactions s JOIN products p ON s.product_id = p.id GROUP BY p.product_name ORDER BY SUM(s.units_sold) DESC LIMIT 1", conn)
        top_product = top_prod_df['product_name'][0]
        target_df = pd.read_sql_query("SELECT target_revenue FROM sales_targets WHERE year = '2026'", conn)
        target = target_df['target_revenue'][0]
        kpi_percent = round((total_revenue / target) * 100) if target > 0 else 0
        cust_df = pd.read_sql_query("SELECT customer_id, COUNT(id) as total_orders FROM sales_transactions GROUP BY customer_id", conn)
        total_cust = len(cust_df)
        vips = len(cust_df[cust_df['total_orders'] >= 5])
        returnings = len(cust_df[(cust_df['total_orders'] >= 2) & (cust_df['total_orders'] <= 4)])
        news = len(cust_df[cust_df['total_orders'] <= 1])
        vip_per = round((vips / total_cust) * 100) if total_cust > 0 else 0
        ret_per = round((returnings / total_cust) * 100) if total_cust > 0 else 0
        new_per = round((news / total_cust) * 100) if total_cust > 0 else 0
        trend_html = self.sales_trend_chart(conn)
        conn.close()
        return {"units": f"{units_sold:,}", "revenue": f"{total_revenue:,.0f} đ", "top_prod": top_product, "kpi": f"{kpi_percent}%", "customer_stats": {"vip": vip_per, "returning": ret_per, "new": new_per}, "trend_chart": trend_html}

    def sales_trend_chart(self, conn):
        df = pd.read_sql_query("SELECT strftime('%m', sale_date) as month_num, SUM(units_sold) as total FROM sales_transactions GROUP BY month_num ORDER BY month_num ASC", conn)
        if df.empty: return "No data available"
        fig = px.line(df, x='month_num', y='total', markers=True, labels={'month_num':'Tháng','total':'Sản phẩm'}, template="plotly_white")
        fig.update_traces(line_color='#3b82f6', fill='tozeroy', line_shape="spline")
        fig.update_layout(margin=dict(l=20,r=20,t=20,b=20), height=300)
        return opy.plot(fig, auto_open=False, output_type='div')

    def sales_top5(self, conn, search_query=""):
        df = pd.read_sql_query("SELECT p.product_name, SUM(s.units_sold) as total_units FROM sales_transactions s JOIN products p ON s.product_id = p.id GROUP BY p.product_name ORDER BY total_units DESC LIMIT 5", conn)
        if search_query: df = df[df['product_name'].str.contains(search_query, case=False, na=False)]
        if df.empty: return "<div style='padding:20px;text-align:center;'>Không có dữ liệu khớp</div>"
        fig = px.bar(df, x='product_name', y='total_units', text='total_units', labels={'product_name':'Product Name','total_units':'Units'}, color='total_units', color_continuous_scale='PuRd')
        fig.update_traces(textposition='outside', marker_line_color='rgb(8,48,107)', marker_line_width=1.5, opacity=0.8)
        fig.update_yaxes(range=[0, df['total_units'].max() * 1.15])
        fig.update_layout(margin=dict(t=40,b=0,l=0,r=0), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_title="", yaxis_title="Units Sold", showlegend=False, transition={'duration': 1000})
        return opy.plot(fig, auto_open=False, output_type='div')

    def sales_slow_moving(self, conn, search_query=""):
        df_all = pd.read_sql_query("SELECT p.product_name, SUM(s.units_sold) as total_units FROM sales_transactions s JOIN products p ON s.product_id = p.id GROUP BY p.product_name ORDER BY total_units ASC", conn)
        num_bottom = max(1, math.ceil(len(df_all) * 0.3))
        df_bottom = df_all.head(num_bottom).copy()
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
        if search_query: df_final = df_final[df_final['product_name'].str.contains(search_query, case=False, na=False)]
        return df_final.to_dict(orient='records')

    def sales_index(self):
        search_query = request.args.get('q', '').strip()
        conn = sqlite3.connect(self.DB_SALE)
        try:
            top5 = self.sales_top5(conn, search_query)
            data = self.sales_get_data()
            data['slow_prods'] = self.sales_slow_moving(conn, search_query)
            return render_template('sales.html', d=data, top5=top5, search_query=search_query)
        except Exception as e:
            return f"Lỗi hệ thống: {e}"
        finally:
            conn.close()
