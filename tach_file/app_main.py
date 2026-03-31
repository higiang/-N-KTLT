import os
import threading
import webview
import time
from flask import Flask

# Import các Class phòng ban
from auth_ceo_ext import AuthCeoExt
from inventory_ext import InventoryExt
from sales_ext import SalesExt
from marketing_ext import MarketingExt
from accounting_ext import AccountingExt

# Đa kế thừa: AppMain nhận tất cả phương thức từ các module
class AppMain(AuthCeoExt, InventoryExt, SalesExt, MarketingExt, AccountingExt):
    def __init__(self):
        self.app = Flask(__name__)
        self.app.secret_key = 'lemonade_super_secret_key'

        # Chuyển đổi đường dẫn DB thành thuộc tính (Attributes) để các class con dùng chung
        self.BASE_DIR = os.path.abspath(os.path.dirname(__file__))
        self.DB_ACC  = os.path.join(self.BASE_DIR, 'database', 'lemonade_counting_finance.db')
        self.DB_INV  = os.path.join(self.BASE_DIR, 'database', 'lemonade_inventory.db')
        self.DB_MKT  = os.path.join(self.BASE_DIR, 'database', 'mkt_department.db')
        self.DB_SALE = os.path.join(self.BASE_DIR, 'database', 'sales.db')
        self.DB_USER = os.path.join(self.BASE_DIR, 'database', 'info.db')

        self.setup_routes()

    def setup_routes(self):
        # Biến toàn cục HTML
        self.app.context_processor(self.inject_global_variables)

        # =============== ROUTES AUTH & CEO ===============
        self.app.add_url_rule("/", view_func=self.index)
        self.app.add_url_rule("/login", view_func=self.login, methods=['GET', 'POST'])
        self.app.add_url_rule("/signup", view_func=self.signup, methods=['GET', 'POST'])
        self.app.add_url_rule("/user_info", view_func=self.user_info, methods=['GET', 'POST'])
        self.app.add_url_rule("/logout", view_func=self.logout)
        self.app.add_url_rule("/signout", view_func=self.signout)
        self.app.add_url_rule("/dashboard", view_func=self.ceo_dashboard)
        self.app.add_url_rule("/reports", view_func=self.ceo_reports)
        self.app.add_url_rule("/settings", view_func=self.ceo_settings)
        self.app.add_url_rule("/api/create_account", view_func=self.api_create_account, methods=["POST"])
        self.app.add_url_rule("/api/update_account", view_func=self.api_update_account, methods=["POST"])
        self.app.add_url_rule("/api/delete_account", view_func=self.api_delete_account, methods=["POST"])
        self.app.add_url_rule("/api/get_account", view_func=self.api_get_account)
        self.app.add_url_rule("/api/forecast", view_func=self.forecast_revenue)

        # =============== ROUTES INVENTORY ===============
        self.app.add_url_rule("/inv", view_func=self.inv_index)
        self.app.add_url_rule("/inv/dashboard", view_func=self.inv_dashboard)
        self.app.add_url_rule("/inv/products", view_func=self.inv_products)
        self.app.add_url_rule("/inv/suppliers", view_func=self.inv_suppliers)
        self.app.add_url_rule("/inv/export", view_func=self.inv_export)

        # =============== ROUTES SALES ===============
        self.app.add_url_rule("/sales", view_func=self.sales_index)

        # =============== ROUTES MARKETING ===============
        self.app.add_url_rule("/mkt", view_func=self.mkt_index)
        self.app.add_url_rule("/mkt/dashboard", view_func=self.mkt_dashboard)
        self.app.add_url_rule("/mkt/segment", view_func=self.mkt_segment)
        self.app.add_url_rule("/mkt/campaign", view_func=self.mkt_campaign)
        self.app.add_url_rule("/mkt/market-share", view_func=self.mkt_market_share)
        self.app.add_url_rule("/mkt/upload", view_func=self.mkt_upload)
        self.app.add_url_rule("/api/dashboard/summary", view_func=self.api_dashboard_summary)
        self.app.add_url_rule("/api/dashboard/campaigns", view_func=self.api_dashboard_campaigns)
        self.app.add_url_rule("/api/dashboard/export", view_func=self.api_dashboard_export)
        self.app.add_url_rule("/api/segment/kpis", view_func=self.api_segment_kpis)
        self.app.add_url_rule("/api/segment/chart", view_func=self.api_segment_chart)
        self.app.add_url_rule("/api/segment/export", view_func=self.api_segment_export)
        self.app.add_url_rule("/api/campaign/kpis", view_func=self.api_campaign_kpis)
        self.app.add_url_rule("/api/campaign/revenue-over-time", view_func=self.api_campaign_revenue)
        self.app.add_url_rule("/api/campaign/export", view_func=self.api_campaign_export)
        self.app.add_url_rule("/api/market-share/kpis", view_func=self.api_market_share_kpis)
        self.app.add_url_rule("/api/market-share/pie", view_func=self.api_market_share_pie)
        self.app.add_url_rule("/api/market-share/export", view_func=self.api_market_share_export)
        self.app.add_url_rule("/api/upload", view_func=self.api_upload, methods=["POST"])

        # =============== ROUTES ACCOUNTING ===============
        self.app.add_url_rule("/acc", view_func=self.acc_index)
        self.app.add_url_rule("/acc/dashboard", view_func=self.acc_dashboard)
        self.app.add_url_rule("/acc/total-cost", view_func=self.acc_total_cost)
        self.app.add_url_rule("/acc/total-revenue", view_func=self.acc_total_revenue)
        self.app.add_url_rule("/acc/finance-report", view_func=self.acc_finance_report)
        self.app.add_url_rule("/acc/documents", view_func=self.acc_documents)
        self.app.add_url_rule("/acc/export-dashboard", view_func=self.acc_export_dashboard)
        self.app.add_url_rule("/acc/export-total-cost", view_func=self.acc_export_total_cost)
        self.app.add_url_rule("/acc/upload-total-cost", view_func=self.acc_upload_total_cost, methods=["POST"])
        self.app.add_url_rule("/acc/export-total-revenue", view_func=self.acc_export_total_revenue)
        self.app.add_url_rule("/acc/export-finance-report", view_func=self.acc_export_finance_report)

    def run(self):
        def run_flask():
            self.app.run(debug=False, port=5000, use_reloader=False)

        t = threading.Thread(target=run_flask)
        t.daemon = True
        t.start()
        time.sleep(1)

        webview.create_window("Lemonade – Business Performance Management and Analytics System", "http://127.0.0.1:5000/login", width=1366, height=768, resizable=True)
        webview.start()


if __name__ == "__main__":
    app_instance = AppMain()
    app_instance.run()
