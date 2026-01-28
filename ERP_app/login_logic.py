def verify_user(username, password):
    users = {"ceo": "123", "acc": "456"}
    u = username.lower()
    if u in users and users[u] == password:
        return {"status": "success", "role": u}
    return {"status": "error", "message": "Sai pass rồi Limes ơi!"}