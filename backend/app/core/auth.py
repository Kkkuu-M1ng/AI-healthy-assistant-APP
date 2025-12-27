# backend/app/core/auth.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

from .security import SECRET_KEY, ALGORITHM

bearer = HTTPBearer()

def get_current_user_id(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
) -> int:
    token = creds.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub = payload.get("sub")
        if sub is None:
            raise HTTPException(status_code=401, detail="无效token")
        return int(sub)
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="无效token")
