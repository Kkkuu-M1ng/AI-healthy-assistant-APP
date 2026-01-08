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
from app.services.llm import chat_with_ai, summarize_session_title

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

@router.get("/sessions")
def list_sessions(
    db: Session = Depends(get_session),
    uid: int = Depends(get_current_user_id)
):
    # 查出当前用户所有的会话，按时间倒序排
    statement = select(ConsultSession).where(ConsultSession.user_id == uid).order_by(ConsultSession.created_at.desc())
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
    uid: int = Depends(get_current_user_id)
):
    # 1. 获取会话与成员画像
    session_obj = db.get(ConsultSession, session_id)
    if not session_obj or session_obj.user_id != uid:
        raise HTTPException(status_code=404, detail="会话不存在")

    member = db.get(FamilyMember, session_obj.member_id)
    persona_data = {
        "gender": member.gender, "age": member.age, "height": member.height,
        "weight": member.weight, "tags_json": member.tags_json,
        "allergies": member.allergies, "meds": member.meds
    }

    # 2. 存入用户消息
    user_msg = ChatMessage(session_id=session_id, role="user", content=content)
    db.add(user_msg)
    db.commit() 

    # 3. 查出历史记录
    history = db.exec(
        select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at)
    ).all()
    payload = [{"role": m.role, "content": m.content} for m in history]

    # 4. 【核心】调用 AI 聊天（这是最优先的任务）
    ai_reply_text = chat_with_ai(payload, persona_data)

    # 5. 存入 AI 回复
    ai_msg = ChatMessage(session_id=session_id, role="assistant", content=ai_reply_text)
    db.add(ai_msg)
    
    # 6. 🚀 【智能起名逻辑】合并并保护
    # 规则：如果是第一轮对话，且标题还是默认的
    if len(history) <= 2 and session_obj.title == "新问诊会话":
        try:
            # 💡 关键：找到“用户描述：”后面的真正内容
            clean_content = content
            if "用户描述：" in content:
                clean_content = content.split("用户描述：")[-1] # 只取后面那段
            
            # 调 AI 总结标题（用干净的内容）
            chat_summary_input = f"用户问：{clean_content}\nAI答：{ai_reply_text[:30]}"
            new_title = summarize_session_title(chat_summary_input)
            session_obj.title = new_title
        except:
            # 如果崩了，也用干净的内容截取
            clean_content = content.split("用户描述：")[-1] if "用户描述：" in content else content
            session_obj.title = clean_content[:10] + "..."
        
        db.add(session_obj)

    # 7. 最后统一提交所有更改
    db.commit()
    db.refresh(ai_msg)

    return ai_msg
    