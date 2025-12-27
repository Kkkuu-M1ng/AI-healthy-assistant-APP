# 数据库里有哪些表、每张表有哪些字段

from typing import Optional
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # 微信授权识别用户的关键字段
    wx_openid: str = Field(index=True, unique=True)

    # 可选信息（后面接微信授权再填）
    nickname: Optional[str] = None
    avatar_url: Optional[str] = None

    # “我的信息”先简单放这里
    full_name: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
