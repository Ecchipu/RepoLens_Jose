def login_user(username, password):
    if username == "admin" and password == "secret":
        return True
    return False


def logout_user(username):
    return f"{username} logged out"