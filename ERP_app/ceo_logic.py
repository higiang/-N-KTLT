import db
def get_stats():
    d = db.get_data_by_type('revenue')
    d["stats"] = ["$125,400", "3,450", "78%"]
    return d