from auth import  login_user, logout_user

def login_route(username, password):
    return login_user(username, password)

def logout_route(username):
    return logout_user(username)