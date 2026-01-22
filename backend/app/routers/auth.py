# backend/app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from fastapi.responses import RedirectResponse
import requests # 👈 确保导入了 requests

from ..db import get_session
from ..models import User, FamilyMember
from ..core.security import create_access_token

router = APIRouter(tags=["auth"])

# auth.py 顶部

# 💡 开发开关：手动切换 True/False 即可
IS_DEV_MODE = False 

# 根据开关自动切换前端跳转地址
if IS_DEV_MODE:
    frontend_base_url = "https://localhost:5173"
else:
    frontend_base_url = "http://ff7c7e8.r15.cpolar.top" 

# 💡 填入你从“微信测试号管理页面”看到的那两串字符
WX_APPID = "wx34535c62052a74b3"
WX_SECRET = "96fc18e0ef5cadcb7b0c85124aa681e4"

# --- 1. 真实的微信授权登录接口 ---
@router.get("/auth/wechat")
def wechat_login(code: str = Query(...), session: Session = Depends(get_session)):
    """
    微信授权核心逻辑：
    - code: 微信传回来的临时密码
    """
    # 第一步：用 code 换取微信的 access_token 和 openid
    token_url = f"https://api.weixin.qq.com/sns/oauth2/access_token?appid={WX_APPID}&secret={WX_SECRET}&code={code}&grant_type=authorization_code"
    
    token_res = requests.get(token_url).json()
    openid = token_res.get("openid")
    wx_access_token = token_res.get("access_token")

    if not openid:
        raise HTTPException(status_code=400, detail=f"微信授权失败: {token_res.get('errmsg')}")

    # 第二步：获取用户真实的头像和昵称
    info_url = f"https://api.weixin.qq.com/sns/userinfo?access_token={wx_access_token}&openid={openid}&lang=zh_CN"
    wx_user_data = requests.get(info_url).json()
    
    # 第三步：数据库操作（查、增、改）
    user = session.exec(select(User).where(User.wx_openid == openid)).first()

    if not user:
        # 新用户：注册并同步微信信息
        user = User(
            wx_openid=openid, 
            nickname=wx_user_data.get("nickname", "新用户"), 
            avatar_url=wx_user_data.get("headimgurl") # 👈 拿到微信头像了！
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        # 同时创建“本人”档案
        self_member = FamilyMember(
            user_id=user.id,
            name=user.nickname,
            relation="本人",
            gender="男", # 微信返回数据里有 sex 字段，也可以映射，暂时默认
            age=22
        )
        session.add(self_member)
        session.commit()
        print(f"🎉 微信新用户注册：{user.nickname}")
    else:
        # 老用户：更新一下最新的微信头像和昵称（防止用户换了头像）
        user.nickname = wx_user_data.get("nickname", user.nickname)
        user.avatar_url = wx_user_data.get("headimgurl", user.avatar_url)
        session.add(user)
        session.commit()
        print(f"✅ 微信用户登录：{user.nickname}")

    # 第四步：颁发你自己的房卡 (Token)
    token = create_access_token(sub=str(user.id))
    
    # 拼凑跳转链接，把 Token 挂在 URL 后面
    base = frontend_base_url.rstrip('/')
    target_path = f"/?token={token}" # 👈 Vue Hash 模式下，参数应该在 # 号之前
    
    # 最终地址：https://.../#/home?token=xxx
    # 为了兼容，我们直接跳到根，让 App.vue 去捡
    redirect_url = f"{base}/#/{target_path}"
    
    print(f"🔗 正在引导用户跳回首页: {user.nickname}")
    
    return RedirectResponse(url=redirect_url)

# --- 2. 原有的开发模式登录（保留方便你测试） ---
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
