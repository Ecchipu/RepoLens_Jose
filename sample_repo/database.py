users = ["admin", "guest", "developer"]

def get_user(username):
    for user in users:
        if user == username:
            return user
    return None

