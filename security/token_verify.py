# auth_dep.py
from fastapi import Header, HTTPException
from jose import jwt, JWTError
from config.config import settings

SECRET_KEY = settings.SECRET_KEY.get_secret_value()
ALGO = "HS256"

def verify_access_token(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGO])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Wrong token type")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
