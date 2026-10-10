import secrets

security_key = secrets.token_urlsafe(32)
print(security_key)