import hashlib


def md5(pwd):
    pm = hashlib.md5()
    pm.update(pwd.encode())
    return pm.hexdigest()
