# 数据库里有哪些表、每张表有哪些字段

import json
from datetime import datetime
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

class FamilyMember(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # 归属哪个用户
    user_id: int = Field(index=True)

    # 成员基础信息
    name: str
    relation: str  # 本人/爸爸/妈妈/孩子...
    gender: Optional[str] = None
    age: Optional[int] = None

    # 标签用 JSON 字符串存（API 给/收 list[str] 更舒服）
    tags_json: str = Field(default="[]")

    created_at: datetime = Field(default_factory=datetime.utcnow)

class AdviceItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    member_id: int = Field(index=True)

    title: str
    reason: str = ""
    tags_json: str = Field(default="[]")     # list[str]
    detail_json: str = Field(default="[]")   # list[str]

    created_at: datetime = Field(default_factory=datetime.utcnow)


class TaskItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    member_id: int = Field(index=True)

    title: str
    freq: str = ""
    due: str = ""            # 简化：先用字符串，如 "2025-01-01"，没有就空
    done: bool = False

    detail_json: str = Field(default="[]")   # list[str]
    logs_json: str = Field(default="[]")     # list[str] 完成记录时间戳列表（可选）

    created_at: datetime = Field(default_factory=datetime.utcnow)    