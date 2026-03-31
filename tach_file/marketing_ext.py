import sqlite3, csv, io
from flask import render_template, request, redirect, url_for, jsonify

class MarketingExt:
    def fmt_money(self, val):
        val = val or 0
        if val >= 1_000_000_000: return f"{val/1_000_000_000:.1f}B"
        if val >= 1_000_000:     return f"{val/1_000_000:.0f}M"
        if val >= 1_000:         return f"${val/1_000:.0f}k"
        return f"${val:.0f}"

    def fmt_pct(self, val):
        if val is None: return "+0.0%"
        sign = "+" if val >= 0 else ""
        return f"{sign}{val:.1f}%"

    def mkt_index(self): return redirect(url_for("mkt_dashboard"))
    def mkt_dashboard(self): return render_template("mar_dashboard.html")
    def mkt_segment(self): return render_template("mar_seg_perform.html")
    def mkt_campaign(self): return render_template("mar_cam_perform.html")
    def mkt_market_share(self): return render_template("mar_market_share_analysis.html")
    def mkt_upload(self): return render_template("mar_upload_data.html")

    def api_dashboard_summary(self):
        conn = self.get_db(self.DB_MKT)
        today = conn.execute("SELECT * FROM marketing_daily_summary ORDER BY report_date DESC LIMIT 1").fetchone()
        active = conn.execute("SELECT COUNT(*) as cnt FROM recent_campaigns WHERE status='Active'").fetchone()["cnt"]
        conn.close()
        return jsonify({
            "today_revenue": {"value": self.fmt_money(today["total_revenue"]) if today else "$0", "change": self.fmt_pct(today["revenue_change_pct"]) if today else "+0%"},
            "total_clicks":  {"value": f"{today['total_clicks']:,}" if today else "0", "change": self.fmt_pct(today["clicks_change_pct"]) if today else "+0%"},
            "conversion_rate": {"value": f"{today['conversion_rate']:.1f}%" if today else "0%", "change": self.fmt_pct(today["conversion_change_pct"]) if today else "+0%"}
        })

    def api_dashboard_campaigns(self):
        search = request.args.get("search", "")
        conn = self.get_db(self.DB_MKT)
        rows = conn.execute("SELECT campaign_name, status, budget, progress FROM recent_campaigns WHERE campaign_name LIKE ? ORDER BY CASE status WHEN 'Active' THEN 0 WHEN 'Pending' THEN 1 ELSE 2 END, id DESC LIMIT 10", (f"%{search}%",)).fetchall()
        conn.close()
        return jsonify([{"name": r["campaign_name"], "status": r["status"], "budget": f"${r['budget']:,.0f}", "progress": int(r["progress"] or 0)} for r in rows])

    def api_dashboard_export(self):
        conn = self.get_db(self.DB_MKT)
        rows = conn.execute("SELECT campaign_name, status, budget, start_date, end_date, clicks_generated, conversions, revenue_generated, progress FROM recent_campaigns ORDER BY id DESC").fetchall()
        conn.close()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Campaign Name","Status","Budget","Start","End","Clicks","Conversions","Revenue","Progress%"])
        for r in rows: writer.writerow(list(r))
        filepath = self.save_to_downloads("campaigns.csv", output.getvalue())
        return jsonify({"success": True, "message": f"File đã lưu tại: {filepath}"})

    def api_segment_kpis(self):
        conn = self.get_db(self.DB_MKT)
        row = conn.execute("SELECT report_date FROM segment_daily_performance ORDER BY report_date DESC LIMIT 1").fetchone()
        today_date = row["report_date"] if row else None
        bs = conn.execute("SELECT SUM(s.revenue) as r, AVG(s.revenue_change_pct) as p FROM segment_daily_performance s JOIN products p ON p.id = s.product_id WHERE s.report_date = ? AND p.segment_id = 1", (today_date,)).fetchone()
        sm = conn.execute("SELECT SUM(s.units_sold) as u, AVG(s.units_change_pct) as p FROM segment_daily_performance s JOIN products p ON p.id = s.product_id WHERE s.report_date = ? AND p.segment_id = 2", (today_date,)).fetchone()
        active = conn.execute("SELECT COUNT(*) as cnt FROM recent_campaigns WHERE status='Active'").fetchone()["cnt"]
        summary = conn.execute("SELECT conversion_rate, conversion_change_pct FROM marketing_daily_summary ORDER BY report_date DESC LIMIT 1").fetchone()
        conn.close()
        return jsonify({
            "best_sellers": {"value": self.fmt_money(bs["r"] if bs and bs["r"] else 0), "change": self.fmt_pct(bs["p"] if bs else None)},
            "slow_movers": {"value": f"{int(sm['u']) if sm and sm['u'] else 0} units", "change": self.fmt_pct(sm["p"] if sm else None)},
            "active_campaigns": {"value": f"{active} campaigns", "change": "+0%"},
            "conversion_rate": {"value": f"{summary['conversion_rate']:.1f}%" if summary else "0%", "change": self.fmt_pct(summary["conversion_change_pct"] if summary else None)}
        })

    def api_segment_chart(self):
        conn = self.get_db(self.DB_MKT)
        rows = conn.execute("SELECT p.product_name, p.segment_id, SUM(s.units_sold) as u, SUM(s.revenue) as r FROM segment_daily_performance s JOIN products p ON p.id = s.product_id GROUP BY p.id ORDER BY p.segment_id, p.id").fetchall()
        conn.close()
        return jsonify({"labels": [r["product_name"] for r in rows], "units": [int(r["u"]) for r in rows], "revenue": [float(r["r"]) for r in rows], "segments": [r["segment_id"] for r in rows]})

    def api_segment_export(self):
        conn = self.get_db(self.DB_MKT)
        rows = conn.execute("SELECT s.report_date, p.product_name, p.category, seg.segment_name, s.units_sold, s.revenue, s.units_change_pct, s.revenue_change_pct FROM segment_daily_performance s JOIN products p ON p.id = s.product_id JOIN segments seg ON seg.id = p.segment_id ORDER BY s.report_date DESC, p.product_name").fetchall()
        conn.close()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Date","Product","Category","Segment","Units Sold","Revenue","Units Change %","Revenue Change %"])
        for r in rows: writer.writerow(list(r))
        filepath = self.save_to_downloads("segment_performance.csv", output.getvalue())
        return jsonify({"success": True, "message": f"File đã lưu tại: {filepath}"})

    def api_campaign_kpis(self):
        conn = self.get_db(self.DB_MKT)
        row = conn.execute("SELECT SUM(revenue_generated) as total_rev, SUM(budget) as total_bud, COUNT(CASE WHEN status='Active' THEN 1 END) as active FROM recent_campaigns").fetchone()
        comp = conn.execute("SELECT SUM(revenue_generated) as r, SUM(budget) as b FROM recent_campaigns WHERE status='Completed'").fetchone()
        growth = ((comp["r"] - comp["b"]) / comp["b"] * 100) if comp and comp["b"] and comp["b"] > 0 else 0.0
        conn.close()
        return jsonify({"revenue_growth": {"value": self.fmt_pct(growth)}, "active_campaigns": {"value": f"{row['active'] or 0} Campaigns"}, "roi": {"value": f"{(row['total_rev'] or 0)/(row['total_bud'] or 1):.1f}x"}})

    def api_campaign_revenue(self):
        conn = self.get_db(self.DB_MKT)
        rows = conn.execute("SELECT revenue_date, SUM(revenue_amount) as total FROM campaign_revenue_daily GROUP BY revenue_date ORDER BY revenue_date ASC").fetchall()
        labels, revenue = [r["revenue_date"] for r in rows], [float(r["total"]) for r in rows]
        avg_bud = conn.execute("SELECT AVG(budget) as avg FROM recent_campaigns").fetchone()["avg"] or 0
        conn.close()
        return jsonify({"labels": labels, "revenue": revenue, "baseline": [round(avg_bud / 30, 2)] * len(labels), "peak": {"date": labels[revenue.index(max(revenue))] if revenue else None, "value": max(revenue) if revenue else 0}})

    def api_campaign_export(self):
        conn = self.get_db(self.DB_MKT)
        rows = conn.execute("SELECT c.campaign_name, c.status, c.budget, c.start_date, c.end_date, c.clicks_generated, c.conversions, c.revenue_generated, c.progress, COALESCE(SUM(d.revenue_amount), 0) as total_daily_revenue FROM recent_campaigns c LEFT JOIN campaign_revenue_daily d ON d.campaign_id = c.id GROUP BY c.id ORDER BY c.id DESC").fetchall()
        conn.close()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Campaign Name","Status","Budget","Start Date","End Date","Clicks","Conversions","Revenue Generated","Progress %","Total Daily Revenue"])
        for r in rows: writer.writerow(list(r))
        filepath = self.save_to_downloads("campaign_performance.csv", output.getvalue())
        return jsonify({"success": True, "message": f"File đã lưu tại: {filepath}"})

    def api_market_share_kpis(self):
        conn = self.get_db(self.DB_MKT)
        periods = [r["period"] for r in conn.execute("SELECT DISTINCT period FROM market_share_period ORDER BY period DESC LIMIT 2").fetchall()]
        cur_p = periods[0] if periods else None
        prev_p = periods[1] if len(periods) > 1 else None
        cur_t = conn.execute("SELECT SUM(revenue) as t FROM market_share_period WHERE period=?", (cur_p,)).fetchone()["t"] or 1
        prev_t = conn.execute("SELECT SUM(revenue) as t FROM market_share_period WHERE period=?", (prev_p,)).fetchone()["t"] or 1
        top = conn.execute("SELECT p.product_name, m.revenue as r FROM market_share_period m JOIN products p ON p.id = m.product_id WHERE m.period = ? ORDER BY m.revenue DESC LIMIT 1", (cur_p,)).fetchone()
        top_growth = 0.0
        if top and prev_p:
            pt = conn.execute("SELECT m.revenue FROM market_share_period m JOIN products p ON p.id = m.product_id WHERE p.product_name = ? AND m.period = ?", (top["product_name"], prev_p)).fetchone()
            if pt and pt["revenue"]: top_growth = (top["r"] - pt["revenue"]) / pt["revenue"] * 100
        conn.close()
        return jsonify({"top_product": {"value": self.fmt_pct(top_growth), "product": top["product_name"] if top else ""}, "share_trend": {"value": self.fmt_pct((cur_t - prev_t) / prev_t * 100)}})

    def api_market_share_pie(self):
        conn = self.get_db(self.DB_MKT)
        row = conn.execute("SELECT DISTINCT period FROM market_share_period ORDER BY period DESC LIMIT 1").fetchone()
        cur_p = row["period"] if row else None
        rows = conn.execute("SELECT p.product_name, m.revenue FROM market_share_period m JOIN products p ON p.id = m.product_id WHERE m.period = ? ORDER BY m.revenue DESC", (cur_p,)).fetchall()
        total = sum(r["revenue"] for r in rows) or 1
        conn.close()
        COLORS = ["#7B61FF","#F4A9C0","#4ECDC4","#FFD166","#06D6A0","#FF6B6B"]
        return jsonify({"labels": [r["product_name"] for r in rows], "values": [round(r["revenue"] / total * 100, 1) for r in rows], "colors": [COLORS[i % len(COLORS)] for i in range(len(rows))], "period": cur_p})

    def api_market_share_export(self):
        conn = self.get_db(self.DB_MKT)
        rows = conn.execute("SELECT m.period, p.product_name, p.category, m.revenue, ROUND(m.revenue * 100.0 / SUM(m.revenue) OVER (PARTITION BY m.period), 2) as share_pct FROM market_share_period m JOIN products p ON p.id = m.product_id ORDER BY m.period DESC, m.revenue DESC").fetchall()
        conn.close()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Period","Product","Category","Revenue","Market Share %"])
        for r in rows: writer.writerow(list(r))
        filepath = self.save_to_downloads("market_share_analysis.csv", output.getvalue())
        return jsonify({"success": True, "message": f"File đã lưu tại: {filepath}"})

    def api_upload(self):
        if "file" not in request.files: return jsonify({"success": False, "error": "Không tìm thấy file."}), 400
        f = request.files["file"]
        if not (f.filename or "").lower().endswith(".csv"): return jsonify({"success": False, "error": "Chỉ chấp nhận file .csv"}), 400
        fb = f.read()
        rows = list(csv.DictReader(io.StringIO(fb.decode("utf-8-sig"))))
        if not rows: return jsonify({"success": False, "error": "CSV rỗng."}), 400
        conn = self.get_db(self.DB_MKT)
        inserted, skipped = 0, 0
        for row in rows:
            name = (row.get("campaign_name") or row.get("name") or "").strip()
            if not name: skipped += 1; continue
            status = (row.get("status") or "Pending").strip().capitalize()
            if status not in ("Active", "Completed", "Pending"): status = "Pending"
            try:
                conn.execute("INSERT OR IGNORE INTO recent_campaigns (campaign_name, status, budget, start_date, end_date, clicks_generated, conversions, revenue_generated, progress) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (name, status, float(row.get("budget") or 0), row.get("start_date",""), row.get("end_date",""), int(float(row.get("clicks_generated") or 0)), int(float(row.get("conversions") or 0)), float(row.get("revenue_generated") or 0), float(row.get("progress") or 0)))
                inserted += 1
            except: skipped += 1
        conn.commit(); conn.close()
        return jsonify({"success": True, "message": f"Import {inserted} campaigns thành công.", "skipped": skipped})