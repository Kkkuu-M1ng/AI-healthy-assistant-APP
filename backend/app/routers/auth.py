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

    if not user:
        # A. 创建 User 账号
        user = User(
            wx_openid=openid, 
            nickname="Kkkuu", 
            avatar_url="http://127.0.0.1:8000/static/Kkkuu.jpg" 
        )
        session.add(user)
        session.commit()
        session.refresh(user) 
            
        # B. 同时创建“本人”健康档案
        self_member = FamilyMember(
            user_id=user.id,
            name=user.nickname or "我",
            relation="本人",
            gender="男",
            age=22
        )
        session.add(self_member)
        session.commit()
        print("✨ 欢迎新用户注册！")
    else:
        # 如果人已经在数据库里了，代码会直接运行到这里
        print("✅ 欢迎老用户回来！数据已就绪。")
        

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
