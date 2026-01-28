import db
def get_report():
    d = db.get_data_by_type('expense')
    d["stats"] = ["$45,000", "890", "62%"]
    return d