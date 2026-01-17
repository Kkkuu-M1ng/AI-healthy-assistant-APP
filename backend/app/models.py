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

    full_name: Optional[str] = None 
    gender: Optional[str] = None
    age: Optional[int] = None

class FamilyMember(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)

    name: str
    relation: str  # 本人/爸爸/妈妈...
    gender: Optional[str] = None
    age: Optional[int] = None
    
    # 👇👇👇 健康档案全家桶（全部搬到这里） 👇👇👇
    height: Optional[float] = None
    weight: Optional[float] = None
    
    tags_json: str = Field(default="[]")      # 既往病史
    lifestyle_json: str = Field(default="[]") # 生活方式
    
    allergies: str = ""      # 过敏 (安全红线)
    meds: str = ""           # 用药 (安全红线)
    special_status: str = "" # 特殊状态
    
    notes: str = "" 
    
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AdviceItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    member_id: int = Field(index=True)

    title: str
    reason: str = ""
    tags_json: str = Field(default="[]")     # list[str]
    detail_json: str = Field(default="[]")   # list[str]

    # 状态位：True表示显示，False表示用户手动隐藏
    is_active: bool = Field(default=True)
    
    # 过期时间：默认生成时计算（如果是空，代表永久有效）
    expire_at: Optional[datetime] = Field(default=None) 

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

class ConsultSession(SQLModel, table=True):
    """
    问诊会话表：代表一次完整的问诊记录（比如“1月5日关于发烧的咨询”）
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)   # 对应 User.id
    member_id: int = Field(index=True) # 对应 FamilyMember.id 👈 指向具体的家属
    title: str = Field(default="新问诊会话")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ChatMessage(SQLModel, table=True):
    """
    聊天消息表：代表会话中的一句具体的话
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(index=True) # 关联到哪个 ConsultSession
    
    role: str   # 角色："user" (用户) 或 "assistant" (AI)
    content: str # 具体的聊天内容
    
    # 记录时间
    created_at: datetime = Field(default_factory=datetime.utcnow)       

class WikiArticle(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    source: str = ""
    
    # 标题与分类
    title: str = Field(index=True)
    category: str # 存入: child, pregnant, elder, common
    
    # 内容展示
    summary: str # 首页轮播图显示的简短摘要
    content: str # 详细长文正文 (支持分段文本)
    cover_url: str = "" # 存放封面图链接 (如: /static/wiki_1.jpg)
    
    # 搜索与关联
    tags_json: str = Field(default="[]") # 关键词标签
    
    created_at: datetime = Field(default_factory=datetime.utcnow)    