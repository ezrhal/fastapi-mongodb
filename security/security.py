from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext
from config.config import settings

SECRET_KEY = settings.SECRET_KEY.get_secret_value()  # use env var in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_token(subject: str, expires_delta: timedelta, token_type: str = "access") -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,             # who the token is for
        "type": token_type,         # "access" | "refresh"
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])