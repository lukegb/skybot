

def query(db, config, user, channel, permission):
    if user in config["admins"]:
        return True
    return False
