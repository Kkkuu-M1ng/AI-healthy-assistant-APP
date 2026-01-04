# backend/app/routers/consult.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List

import json

# 导入你的数据库依赖
from app.db import get_session
# 导入你的模型 (确保 models.py 里已经加了 ConsultSession 和 ChatMessage)
from app.models import ConsultSession, ChatMessage, AdviceItem, TaskItem
# 导入刚才写的替身服务
from app.services.llm import chat_with_ai

router = APIRouter(prefix="/consult", tags=["Consult"])

def dump_json(obj):
    return json.dumps(obj, ensure_ascii=False)

# --------------------------
# 1. 创建会话 (Start)
# --------------------------
@router.post("/sessions")
def create_session(user_id: int, db: Session = Depends(get_session)):
    # 1. 创建会话
    session = ConsultSession(user_id=user_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    
    
    # 2. 自动插入欢迎语
    welcome_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content="你好，我是AI健康助手。请问哪里不舒服？"
    )
    db.add(welcome_msg)
    db.commit()
    # 4. 【新增】手动返回一个字典，绕过 SQLModel 的序列化问题
    return {
        "id": session.id,
        "user_id": session.user_id,
        "msg": "创建成功"
    }

# --------------------------
# 2. 获取历史消息 (History)
# --------------------------
@router.get("/{session_id}/messages", response_model=List[ChatMessage])
def get_messages(session_id: int, db: Session = Depends(get_session)):
    """
    加载某个会话的所有聊天记录
    """
    statement = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at)
    results = db.exec(statement).all()
    return results

# --------------------------
# 3. 发送消息并获取回复 (Chat)
# --------------------------

@router.post("/{session_id}/chat")
def chat(session_id: int, content: str, db: Session = Depends(get_session)):
    # --- 准备工作：硬编码用户ID (未来从Token取) ---
    current_user_id = 1
    # 假设当前是在给 1号成员 (宝宝) 问诊。未来这个应该从 session 里取或者前端传
    current_member_id = 1 

    # A. 存用户消息
    user_msg = ChatMessage(session_id=session_id, role="user", content=content)
    db.add(user_msg)
    db.commit()
    
    # B. 查历史
    history = db.exec(
        select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at)
    ).all()
    payload = [{"role": m.role, "content": m.content} for m in history]
    
    # C. 调用 AI (返回的是字典)
    ai_result = chat_with_ai(payload)
    
    # 解析数据
    reply_text = ai_result["reply"]
    new_advices = ai_result["new_advice"]
    new_tasks = ai_result["new_tasks"]
    
    # D. 【核心逻辑】自动入库：建议
    if new_advices:
        print(f"💡 AI 生成了 {len(new_advices)} 条建议")
        for item in new_advices:
            advice = AdviceItem(
                user_id=current_user_id,
                member_id=current_member_id,
                title=item["title"],
                reason=item["reason"],
                tags_json=dump_json(item["tags"]),
                detail_json="[]"
            )
            db.add(advice)
            
    # E. 【核心逻辑】自动入库：任务
    if new_tasks:
        print(f"📋 AI 生成了 {len(new_tasks)} 条任务")
        for item in new_tasks:
            task = TaskItem(
                user_id=current_user_id,
                member_id=current_member_id,
                title=item["title"],
                freq=item["freq"],
                due=item["due"],
                done=False,
                detail_json="[]",
                logs_json="[]"
            )
            db.add(task)

    # F. 存 AI 文本回复
    ai_msg = ChatMessage(session_id=session_id, role="assistant", content=reply_text)
    db.add(ai_msg)
    
    # 一次性提交所有更改 (建议、任务、消息)
    db.commit()
    db.refresh(ai_msg)
    
    return ai_msg
    