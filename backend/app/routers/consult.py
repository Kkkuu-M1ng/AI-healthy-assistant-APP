# backend/app/routers/consult.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List

import json

# 导入你的数据库依赖
from app.db import get_session
# 导入你的模型 (确保 models.py 里已经加了 ConsultSession 和 ChatMessage)
from app.models import ConsultSession, ChatMessage, AdviceItem, TaskItem, FamilyMember
from app.core.auth import get_current_user_id
# 导入刚才写的替身服务
from app.services.llm import chat_with_ai

router = APIRouter(prefix="/consult", tags=["Consult"])

def dump_json(obj):
    return json.dumps(obj, ensure_ascii=False)

# --------------------------
# 1. 创建会话 (Start)
# --------------------------
@router.post("/sessions")
def create_session(
    member_id: int,  # 👈 1. 确保这里接收了成员ID
    db: Session = Depends(get_session),
    uid: int = Depends(get_current_user_id) # 👈 2. 确保是从 Token 拿用户ID
):
    # 3. 创建会话时，必须把 member_id 存进去！
    session = ConsultSession(user_id=uid, member_id=member_id)
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    # 自动插入欢迎语
    welcome_msg = ChatMessage(
        session_id=session.id,
        role="assistant",
        content="你好，我是AI健康助手。请问哪里不舒服？"
    )
    db.add(welcome_msg)
    db.commit()

    # 返回给前端
    return {
        "id": session.id,
        "user_id": session.user_id,
        "member_id": session.member_id,
        "msg": "问诊室已开启"
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
def chat(
    session_id: int, 
    content: str, 
    db: Session = Depends(get_session), 
    uid: int = Depends(get_current_user_id) # 🆕 自动识别当前登录用户
):
    # 1. 找到当前的问诊会话，确认它属于谁
    session_obj = db.get(ConsultSession, session_id)
    if not session_obj or session_obj.user_id != uid:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 👇👇👇 加上这两行打印，看看到底在找谁 👇👇👇
    print(f"🔍 DEBUG: 当前登录 UserID={uid}")
    print(f"🔍 DEBUG: 当前会话绑定的 MemberID={session_obj.member_id}")

    # 2. 核心：获取这个人的“健康画像” (Persona)
    # 假设会话中记录了 member_id，如果没有，默认取该用户的“本人”档案
    # 我们这里做一个兼容逻辑：
    target_member_id = getattr(session_obj, "member_id", None)
    if not target_member_id:
        # 兜底：去找该用户关系为“本人”的成员
        member = db.exec(select(FamilyMember).where(FamilyMember.user_id == uid, FamilyMember.relation == "本人")).first()
    else:
        member = db.get(FamilyMember, target_member_id)

    if not member:
        print(f"❌ 错误：在 FamilyMember 表里找不到 ID 为 {target_member_id} 的数据！")
        raise HTTPException(status_code=400, detail="找不到对应的健康档案，请先完善个人资料")

    # 3. 准备投喂给 AI 的画像字典
    persona_data = {
        "gender": member.gender,
        "age": member.age,
        "height": member.height,
        "weight": member.weight,
        "tags_json": member.tags_json, # 既往病史
        "allergies": member.allergies, # 过敏红线
        "meds": member.meds,           # 常用药
        "special_status": member.special_status # 特殊时期
    }

    # 4. 存入用户刚刚说的话
    user_msg = ChatMessage(session_id=session_id, role="user", content=content)
    db.add(user_msg)
    db.commit()
    
    # 5. 查出历史记录并打包
    history = db.exec(
        select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at)
    ).all()
    payload = [{"role": m.role, "content": m.content} for m in history]
    
    # 6. 🚀 真正调真 AI (通义千问)
    # 注意：我们把历史对话和刚才准备的画像数据都传进去
    ai_result = chat_with_ai(payload, persona_data)
    
    # 7. 解析 AI 返回的 JSON 结果
    reply_text = ai_result.get("reply", "抱歉，我还没想好怎么回。")
    new_advices = ai_result.get("new_advice", [])
    new_tasks = ai_result.get("new_tasks", [])
    
    # 8. 【自动化闭环】建议入库
    for item in new_advices:
        advice = AdviceItem(
            user_id=uid,
            member_id=member.id,
            title=item.get("title", "健康建议"),
            reason=item.get("reason", ""),
            tags_json=json.dumps(item.get("tags", [])), # 转回 JSON 存
            detail_json="[]"
        )
        db.add(advice)
            
    # 9. 【自动化闭环】任务入库
    for item in new_tasks:
        task = TaskItem(
            user_id=uid,
            member_id=member.id,
            title=item.get("title", "健康任务"),
            freq=item.get("freq", ""),
            due=item.get("due", ""),
            done=False,
            detail_json="[]",
            logs_json="[]"
        )
        db.add(task)

    # 10. 存入 AI 的回复气泡
    ai_msg = ChatMessage(session_id=session_id, role="assistant", content=reply_text)
    db.add(ai_msg)
    
    db.commit()
    db.refresh(ai_msg)
    
    return ai_msg
    