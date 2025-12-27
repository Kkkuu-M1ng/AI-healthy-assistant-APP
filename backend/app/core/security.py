from datetime import datetime, timedelta
from jose import jwt

SECRET_KEY = "dev-secret-change-me"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 72

def create_access_token(sub: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {"sub": sub, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
