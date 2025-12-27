# backend/app/routers/auth.py
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from ..db import get_session
from ..models import User
from ..core.security import create_access_token

router = APIRouter(tags=["auth"])

@router.post("/auth/dev")
def dev_login(session: Session = Depends(get_session)):
    openid = "dev_openid_001"

    user = session.exec(select(User).where(User.wx_openid == openid)).first()
    if not user:
        user = User(wx_openid=openid, nickname="Dev User")
        session.add(user)
        session.commit()
        session.refresh(user)

    token = create_access_token(sub=str(user.id))
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "wx_openid": user.wx_openid,
            "nickname": user.nickname,
        },
    }
