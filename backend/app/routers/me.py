# backend/app/routers/me.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from ..db import get_session
from ..models import User
from ..core.auth import get_current_user_id

router = APIRouter(tags=["me"])

class MeUpdate(BaseModel):
    full_name: str | None = None
    gender: str | None = None
    age: int | None = None

@router.get("/me")
def get_me(
    session: Session = Depends(get_session),
    uid: int = Depends(get_current_user_id),
):
    user = session.get(User, uid)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return {
        "id": user.id,
        "wx_openid": user.wx_openid,
        "nickname": user.nickname,
        "avatar_url": user.avatar_url,
        "full_name": user.full_name,
        "gender": user.gender,
        "age": user.age,
    }

@router.put("/me")
def update_me(
    data: MeUpdate,
    session: Session = Depends(get_session),
    uid: int = Depends(get_current_user_id),
):
    user = session.get(User, uid)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(user, k, v)

    session.add(user)
    session.commit()
    session.refresh(user)
    return {"ok": True}
