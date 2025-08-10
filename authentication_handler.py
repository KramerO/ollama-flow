#!/usr/bin/env python3
import jwt
import base64
import time

def generate_token(username, password):
    token = {
        "username": username,
        "password": password,
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600
    }
    return jwt.encode(token, "secret_key", algorithm="HS256").decode("utf-8")

def verify_token(token):
    try:
        payload = jwt.decode(token, "secret_key", algorithms=["HS256"])
        if time.time() > int(payload["exp"]):
            raise jwt.ExpiredSignatureError
        return payload["username"]
    except jwt.ExpiredSignatureError:
        return None

