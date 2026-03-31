import sqlite3, csv, io
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import plotly.offline as opy
from flask import render_template, request, redirect, url_for, jsonify

class AccountingExt:
    # --- HÀM TIỆN ÍCH ---
    def fmt_m(self, val):
        if isinstance(val, (int, float)):
            num = val / 1000000
            return "{:,.0f}M".format(num) if num == int(num) else "{:,.1f}M".format(num)
        return val

    def acc_make_chart(self, fig, h=110, ml=0, mr=0, mt=0, mb=0):
        fig.update_layout(margin=dict(l=ml, r=mr, t=mt, b=mb), height=h, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False, hoverlabel=dict(font_size=13, font_family="Poppins"))
        return opy.plot(fig, auto_open=False, output_type='div', config={'responsive': True, 'displayModeBar': False})

    def acc_get_pie(self, table, keyword, h=250, is_dashboard=False):
        conn = self.get_db(self.DB_ACC)
        # Lấy dữ liệu, loại bỏ dòng TOTAL để không làm sai lệch biểu đồ
        df = pd.read_sql_query(f"SELECT Department, Amount_VND FROM {table} WHERE Items != '{keyword}'", conn)
        conn.close()
        if df.empty: return ""
        # Làm sạch dữ liệu số (xóa dấu phẩy) và nhóm theo phòng ban
        df['Amount_VND'] = df['Amount_VND'].astype(str).str.replace(',', '').astype(float)
        df_g = df.groupby('Department', as_index=False)['Amount_VND'].sum()
        df_g['Value_M'] = df_g['Amount_VND'] / 1_000_000
        colors = ['#5D5FEF', '#FF947A', '#3CD856', '#FACC15', '#2DD4BF', '#A78BFA', '#38BDF8']
        fig = px.pie(df_g, names='Department', values='Value_M', hole=0.6, color_discrete_sequence=colors)

        # Tùy chỉnh hiển thị riêng cho Dashboard hoặc trang chi tiết
        if is_dashboard:
            fig.update_traces(textinfo='percent', textposition='inside', domain=dict(y=[0.3, 1]), marker=dict(line=dict(color='#FFFFFF', width=2)))
            fig.update_layout(margin=dict(l=5, r=5, t=5, b=5), height=h, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.5, xanchor="center", x=0.5, font=dict(size=8, color="#737791")))
        else:
            fig.update_traces(textinfo='percent', textposition='inside')
            fig.update_layout(margin=dict(l=5, r=5, t=20, b=50), height=h, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=True, legend=dict(orientation="h", yanchor="top", y=-0.1, xanchor="center", x=0.5))
        return opy.plot(fig, auto_open=False, output_type='div', config={'responsive': True, 'displayModeBar': False})

    def acc_get_line(self, table, y_col, color_hex):
        #Vẽ biểu đồ đường cho doanh thu hàng tháng
        conn = self.get_db(self.DB_ACC)
        df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
        conn.close()
        if df.empty: return ""
        df['Value_M'] = df[y_col] / 1000000
        fig = px.line(df, x='Month', y='Value_M', markers=True, color_discrete_sequence=[color_hex])
        fig.update_traces(fill='tozeroy', fillcolor="rgba(93, 95, 239, 0.1)", hovertemplate='<b>%{x}</b><br>%{y:,.0f}M<extra></extra>')
        fig.update_xaxes(title=None, showgrid=False, tickfont=dict(size=11, color='#737791'))
        fig.update_yaxes(title=None, showgrid=False, showticklabels=False)
        return self.acc_make_chart(fig, h=120, ml=40, mr=40, mt=15, mb=20)

    def acc_cashflow_chart(self):
        conn = self.get_db(self.DB_ACC)
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

    def acc_double_bar(self):
        conn = self.get_db(self.DB_ACC)
        df = pd.read_sql_query("SELECT * FROM ComparisonData", conn)
        conn.close()
        if df.empty: return ""
        df['Revenue_M'], df['Cost_M'] = df['Revenue']/1000, df['Cost']/1000
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df['Month'], y=df['Revenue_M'], name='Revenue', marker_color='#5D5FEF', text=df['Revenue_M'].apply(lambda x: f"{x:,.0f}M"), textposition='outside', cliponaxis=False))
        fig.add_trace(go.Bar(x=df['Month'], y=df['Cost_M'], name='Cost', marker_color='#3CD856', text=df['Cost_M'].apply(lambda x: f"{x:,.0f}M"), textposition='outside', cliponaxis=False))
        fig.update_layout(barmode='group', margin=dict(l=20, r=20, t=50, b=20), height=250, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5))
        return opy.plot(fig, auto_open=False, output_type='div', config={'responsive': True, 'displayModeBar': False})

    def acc_profit_chart(self):
        conn = self.get_db(self.DB_ACC)
        df = pd.read_sql_query("SELECT * FROM ComparisonData", conn)
        conn.close()
        if df.empty: return ""
        df['Profit_M'] = df['Profit'] /1000
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['Month'], y=df['Profit_M'], fill='tozeroy', mode='lines+markers+text', text=df['Profit_M'].apply(lambda x: f"{x:,.0f}M"), textposition='top center', textfont=dict(size=12, color='#151D48', weight='bold'), line=dict(color='#A78BFA', shape='spline', width=3), fillcolor='rgba(167,139,250,0.2)', cliponaxis=False))
        fig.update_layout(margin=dict(l=20, r=20, t=50, b=40), height=260, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
        return opy.plot(fig, auto_open=False, output_type='div', config={'responsive': True, 'displayModeBar': False})

    def acc_index(self): return redirect(url_for("acc_dashboard"))

    def acc_dashboard(self):
        conn = self.get_db(self.DB_ACC)
        # Tính tổng chi phí trực tiếp từ bảng chi tiết
        expenses = conn.execute("SELECT Amount_VND FROM DetailedExpenses WHERE Items NOT LIKE '%TOTAL%'").fetchall()
        actual_total_cost = sum(row["Amount_VND"] for row in expenses if row["Amount_VND"])
        kpis = conn.execute("SELECT * FROM TodaysSales").fetchall()
        conn.close()
        kpi_dict = {row['Metric']: {'val': row['Value'], 'status': row['Status']} for row in kpis}
        # Ghi đè giá trị thực tế vào KPI 'Total Cost'
        kpi_dict['Total Cost']['val'] = f"{actual_total_cost / 1_000_000:,.0f}M"
        return render_template("acc_dashboard.html", kpi=kpi_dict, pie_rev=self.acc_get_pie('RevenueDetails', 'TOTAL', 280, is_dashboard=True), pie_cost=self.acc_get_pie('DetailedExpenses', 'TOTAL', 280, is_dashboard=True))

    def acc_total_cost(self):
        conn = self.get_db(self.DB_ACC)
        items = conn.execute("SELECT * FROM DetailedExpenses WHERE Items NOT LIKE '%TOTAL%'").fetchall()
        actual_total = sum(row["Amount_VND"] for row in items if row["Amount_VND"])
        summary_data = {'Value': f"{actual_total / 1_000_000:,.0f}M"}
        conn.close()
        return render_template("acc_total_cost.html", summary=summary_data, items=items, total_row={"Items": "TOTAL", "Amount_VND": actual_total}, pie_chart=self.acc_get_pie('DetailedExpenses', 'TOTAL', 250, is_dashboard=False), fmt_m=self.fmt_m)

    def acc_total_revenue(self):
        conn = self.get_db(self.DB_ACC)
        summary = conn.execute("SELECT * FROM TotalRevenueOverview").fetchone()
        items = conn.execute("SELECT * FROM RevenueDetails WHERE Items != 'TOTAL'").fetchall()
        total_row = conn.execute("SELECT * FROM RevenueDetails WHERE Items = 'TOTAL'").fetchone()
        conn.close()
        return render_template("acc_total_revenue.html", summary=summary, items=items, total_row=total_row, pie_chart=self.acc_get_pie('RevenueDetails','TOTAL',170), line_chart=self.acc_get_line('MonthlyRevenue','Revenue_VND','#3CD856'), fmt_m=self.fmt_m)

    def acc_finance_report(self):
        return render_template("acc_fin_report.html", rev_cost_bar=self.acc_double_bar(), cf_line=self.acc_cashflow_chart(), profit_bar=self.acc_profit_chart())

    def acc_documents(self): return render_template("acc_docs.html")

    def acc_export_dashboard(self):
        conn = self.get_db(self.DB_ACC)
        items = conn.execute("SELECT * FROM TodaysSales").fetchall()
        conn.close()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Metric","Value","Growth Status"])
        for p in items: writer.writerow(list(p))
        return jsonify({"success": True, "message": f"File đã lưu tại: {self.save_to_downloads('finance_overview.csv', output.getvalue())}"})

    def acc_export_total_cost(self):
        conn = self.get_db(self.DB_ACC)
        items = conn.execute("SELECT * FROM DetailedExpenses").fetchall()
        conn.close()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Date","Items","Department","Amount_VN"])
        for r in items: writer.writerow(list(r))
        return jsonify({"success": True, "message": f"File đã lưu tại: {self.save_to_downloads('total_cost.csv', output.getvalue())}"})

    def acc_upload_total_cost(self):
        if "file" not in request.files:
            return jsonify({"success": False, "message": "Không tìm thấy file gửi lên."})

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"success": False, "message": "Bạn chưa chọn file Excel."})

        try:
            # 1. Đọc file Excel
            df_raw = pd.read_excel(file, header=None)
            header_idx = next((i for i, row in df_raw.iterrows() if
                               "date" in [str(val).strip().lower() for val in row.values if pd.notnull(val)]
                               and "items" in [str(val).strip().lower() for val in row.values if pd.notnull(val)]),
                              None)

            if header_idx is None:
                return jsonify({"success": False, "message": "Không tìm thấy dòng tiêu đề!"})

            file.seek(0)
            df = pd.read_excel(file, skiprows=header_idx).rename(columns=lambda x: str(x).strip().lower()).rename(
                columns={"date": "Date", "items": "Items", "department": "Department", "amount": "Amount_VND"})

            conn = self.get_db(self.DB_ACC)
            inserted = 0

            # 2. Vòng lặp Insert
            for _, row in df.iterrows():
                item_name = str(row.get("Items", "")).upper().strip()
                if not item_name or "TOTAL" in item_name or pd.isnull(row.get("Date")):
                    continue

                # Xử lý định dạng ngày và số tiền
                try:
                    raw_date = row["Date"]
                    formatted_date = pd.to_datetime(raw_date).strftime('%Y-%m-%d')

                    clean_num = str(row["Amount_VND"]).upper().replace(",", "").replace("VND", "").strip()
                    amount = float(clean_num.replace('M', '')) * 1e6 if 'M' in clean_num else float(clean_num)
                except:
                    continue

                conn.execute("INSERT INTO DetailedExpenses (Date, Items, Department, Amount_VND) VALUES (?, ?, ?, ?)",
                             (formatted_date, str(row["Items"]), str(row["Department"]), amount))
                inserted += 1

            # ============================================================
            # Tính tổng từ DB
            res = conn.execute("SELECT SUM(Amount_VND) FROM DetailedExpenses WHERE Items NOT LIKE '%TOTAL%'").fetchone()
            new_total = res[0] if res[0] else 0
            new_total_formatted = f"{new_total / 1_000_000:,.0f}M"

            print(f"--- DEBUG: New Total calculated: {new_total_formatted} ---")

            # Cập nhật bảng TodaysSales
            cursor = conn.execute("UPDATE TodaysSales SET Value = ? WHERE Metric LIKE '%Total%Cost%'", (new_total_formatted,))

            if cursor.rowcount == 0:
                print("--- WARNING: Không tìm thấy Metric 'Total Cost' trong bảng TodaysSales để update! ---")
            else:
                print(f"--- SUCCESS: Đã cập nhật TodaysSales thành công! ---")

            conn.commit()
            conn.close()

            return jsonify({"success": True, "message": f"Đã cập nhật xong! Tổng mới: {new_total_formatted}"})

        except Exception as e:
            print(f"--- ERROR: {str(e)} ---")
            return jsonify({"success": False, "message": f"Lỗi: {str(e)}"})

    def acc_export_total_revenue(self):
        conn = self.get_db(self.DB_ACC)
        items = conn.execute("SELECT * FROM RevenueDetails").fetchall()
        conn.close()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Date","Items","Department","Amount_D"])
        for r in items: writer.writerow(list(r))
        return jsonify({"success": True, "message": f"File đã lưu tại: {self.save_to_downloads('total_revenue.csv', output.getvalue())}"})

    def acc_export_finance_report(self):
        conn = self.get_db(self.DB_ACC)
        items = conn.execute("SELECT * FROM ComparisonData").fetchall()
        conn.close()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Month","Revenue","Cost","Profit"])
        for r in items: writer.writerow(list(r))
        return jsonify({"success": True, "message": f"File đã lưu tại: {self.save_to_downloads('finance_report.csv', output.getvalue())}"})