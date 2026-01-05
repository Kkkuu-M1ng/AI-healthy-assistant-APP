# backend/app/routers/auth.py
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from ..db import get_session
from ..models import User, FamilyMember
from ..core.security import create_access_token

router = APIRouter(tags=["auth"])

@router.post("/auth/dev")
def dev_login(session: Session = Depends(get_session)):
    openid = "dev_openid_001"

    user = session.exec(select(User).where(User.wx_openid == openid)).first()
    # A. 创建 User 账号 (基础登录信息)
    user = User(
        wx_openid=openid, 
        nickname="Kkkuu", # 默认昵称
        # 如果你以后删库重建，这里会给个默认头像。
        # 如果你不删库，这里不会覆盖你自己上传的头像。
        avatar_url="http://127.0.0.1:8000/static/Kkkuu.jpg" 
    )
    session.add(user)
    session.commit()
    session.refresh(user) # 拿到 user.id
        
    # B. 【新增】自动创建"本人"的健康档案
    # 这样你的 Me.vue 就能读写身高体重了
    self_member = FamilyMember(
        user_id=user.id,
        name=user.nickname or "我",
        relation="本人",  # 关键标记
        gender="男",     # 默认值，可在前端改
        age=22          # 默认值
    )
    session.add(self_member)
    session.commit()
        

    # 2. 颁发 Token (房卡)
    token = create_access_token(sub=str(user.id))
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "wx_openid": user.wx_openid,
            "nickname": user.nickname,
            "avatar_url": user.avatar_url,
        },
    }
