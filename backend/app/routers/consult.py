# backend/app/routers/consult.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from datetime import datetime, timedelta
from .members import load_tags, dump_tags
from pydantic import BaseModel

import json

# 导入你的数据库依赖
from app.db import get_session
# 导入你的模型 (确保 models.py 里已经加了 ConsultSession 和 ChatMessage)
from app.models import ConsultSession, ChatMessage, AdviceItem, TaskItem, FamilyMember, WikiArticle
from app.core.auth import get_current_user_id
from app.services.llm import chat_with_ai_vision, summarize_session_title, generate_health_plan

router = APIRouter(prefix="/consult", tags=["Consult"])

def dump_json(obj):
    return json.dumps(obj, ensure_ascii=False)

class ChatRequest(BaseModel):
    content: str | None = None
    image_base64: str | None = None

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
    member_id: int | None = None,
    db: Session = Depends(get_session),
    uid: int = Depends(get_current_user_id)
):
    try:
        # 2. 构造查询语句
        statement = select(ConsultSession).where(ConsultSession.user_id == uid)
        
        # 💡 如果传了 member_id，就只查这个人的历史记录
        if member_id:
            statement = statement.where(ConsultSession.member_id == member_id)
            
        statement = statement.order_by(ConsultSession.created_at.desc())
        results = db.exec(statement).all()
        
        return results
    except Exception as e:
        print(f"❌ 列表查询失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取历史列表失败")

# --------------------------
# 3. 发送消息并获取回复 (Chat)
# --------------------------

@router.post("/{session_id}/chat")
def chat(
    session_id: int, 
    data: ChatRequest,
    db: Session = Depends(get_session), 
    uid: int = Depends(get_current_user_id)
):
    # --- A. 基础校验 ---
    content = data.content or "" 
    session_obj = db.get(ConsultSession, session_id)
    if not session_obj or session_obj.user_id != uid:
        raise HTTPException(status_code=404, detail="会话不存在")

    member = db.get(FamilyMember, session_obj.member_id)
    persona_data = {
        "name": member.name, "age": member.age, "gender": member.gender,
        "height": member.height, "weight": member.weight,
        "tags": load_tags(member.tags_json),
        "allergies": member.allergies, "meds": member.meds, "notes": member.notes
    }

    # --- B. 存入当前用户消息 ---
    user_msg = ChatMessage(session_id=session_id, role="user", content=content)
    db.add(user_msg)
    db.commit()

    # --- C. 构造历史上下文 ---
    history_rows = db.exec(
        select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at)
    ).all()
    payload = [{"role": m.role, "content": m.content} for m in history_rows]

    # --- D. 调用通义千问 (识图 + 提取标签) ---
    ai_result = chat_with_ai_vision(payload, persona_data, data.image_base64)
    ai_reply_text = ai_result.get("reply", "我正在思考...")

    # --- E. 【画像进化】识图提取新标签并存入 ---
    new_tags_found = ai_result.get("new_tags", [])
    if new_tags_found:
        current_tags = load_tags(member.tags_json)
        for t_name in new_tags_found:
            if t_name not in current_tags:
                current_tags[t_name] = {"level": 2, "score": 100}
        member.tags_json = dump_tags(current_tags)
        db.add(member)

    # --- F. 【重点修复】先创建 AI 回复对象 ---
    # 💡 必须先创建 ai_msg 变量，下面才能修改它的 content
    ai_msg = ChatMessage(session_id=session_id, role="assistant", content=ai_reply_text)

    # --- G. 【智能关联百科】 ---
    try:
        # 只在回复比较长时才去查，提高效率
        if len(ai_reply_text) > 5:
            all_wikis = db.exec(select(WikiArticle)).all()
            for wiki in all_wikis:
                wiki_tags = json.loads(wiki.tags_json) if wiki.tags_json else []
                # 如果 AI 回复里提到了百科的标签
                if any(tag in ai_reply_text for tag in wiki_tags):
                    # 💡 此时 ai_msg 已经存在，可以安全地追加暗号了
                    ai_msg.content += f"\n\n[[WIKI_LINK:{wiki.id}:{wiki.title}]]"
                    print(f"📖 成功关联百科: {wiki.title}")
                    break
    except Exception as e:
        print(f"⚠️ 关联百科小失败: {e}")

    # --- H. 存入 AI 回复并提交 ---
    db.add(ai_msg)
    
    # --- I. 自动占位首页标题 ---
    # 规则：如果是首轮对话，且标题还是默认的，立刻起名
    if session_obj.title == "新问诊会话":
        clean_user_msg = content.split("用户描述：")[-1] if "用户描述：" in content else content
        placeholder_title = clean_user_msg[:12].strip() + ("..." if len(clean_user_msg) > 12 else "")
        session_obj.title = placeholder_title
        db.add(session_obj)
        print(f"📌 已为会话快速重命名: {placeholder_title}")

    # 最后统一提交所有更改（消息、画像、标题）
    db.commit()
    db.refresh(ai_msg)
    
    return ai_msg

@router.post("/{session_id}/generate_plan")
def generate_plan(
    session_id: int, 
    db: Session = Depends(get_session), 
    uid: int = Depends(get_current_user_id)
):
    # 1. 验证权限
    session_obj = db.get(ConsultSession, session_id)
    if not session_obj or session_obj.user_id != uid:
        raise HTTPException(status_code=404, detail="会话不存在")

    # 2. 获取成员画像和对话历史
    member = db.get(FamilyMember, session_obj.member_id)
    history_rows = db.exec(
        select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at)
    ).all()
    history_payload = [{"role": m.role, "content": m.content} for m in history_rows]

    # 🚀 【核心逻辑 1】：延迟起名 (只有点击魔法棒时，才为会话定名)
    # 逻辑：如果当前还是默认标题，我们就总结一个
    
    try:
        print(f"🕵️‍♂️ 正在为会话 ID {session_id} 申请 AI 深度总结标题...")
        # 💡 技巧：把整场对话的前 5 句拼起来给 AI 看，起名最准
        chat_context = ""
        for m in history_rows[:6]:
            # 过滤掉指令干扰，只取内容
            text = m.content.split("用户描述：")[-1] if "用户描述：" in m.content else m.content
            chat_context += f"{m.role}: {text[:30]}\n"
            
            # 调用你写的总结函数
        new_title = summarize_session_title(chat_context)
        if new_title:
            session_obj.title = new_title
            db.add(session_obj)
            print(f"✨【成功】会话已更名为: {new_title}")
    except Exception as e:
            print(f"⚠️ 总结标题小失败: {e}")

    # 3. 准备画像数据投喂 AI
    persona_brief = {
        "name": member.name, "age": member.age, "gender": member.gender, 
        "tags": load_tags(member.tags_json), "notes": member.notes,
        "allergies": member.allergies, "meds": member.meds
    }

    # 4. 🚀 【核心逻辑 2】：调用 AI 生成建议和任务
    print(f"🤖 正在为 {member.name} 生成详细健康方案...")
    ai_plan = generate_health_plan(history_payload, persona_brief)

    # 5. 提取并清洗 AI 返回的 JSON 数据
    new_advices = ai_plan.get("new_advice", [])
    new_tasks = ai_plan.get("new_tasks", [])
    # 强制变数组，防止 AI 调皮返回字典
    if isinstance(new_advices, dict): new_advices = []
    if isinstance(new_tasks, dict): new_tasks = []

    # A. 遍历保存建议
    for item in new_advices:
        if not isinstance(item, dict): continue
        title = item.get("title") or item.get("name") or "建议"
        reason = item.get("reason") or item.get("content") or "问诊总结"
        tags = item.get("tags") or []
        
        advice = AdviceItem(
            user_id=uid, member_id=member.id, title=str(title), reason=str(reason),
            tags_json=json.dumps(tags, ensure_ascii=False),
            expire_at=datetime.utcnow() + timedelta(days=30), is_active=True
        )
        db.add(advice)

    # B. 遍历保存任务
    for item in new_tasks:
        if not isinstance(item, dict): continue
        t_title = item.get("title") or item.get("task") or "健康任务"
        task = TaskItem(
            user_id=uid, member_id=member.id, title=str(t_title),
            freq=item.get("freq") or "按时执行", due=item.get("due") or "尽快",
            done=False, detail_json="[]", logs_json="[]"
        )
        db.add(task)

    # 6. 一次性提交：标题更新 + 建议入库 + 任务入库
    db.commit()
    print(f"✅ 闭环完成：{len(new_advices)}条建议, {len(new_tasks)}条任务已存入 {member.name} 的名下")

    return {
        "ok": True, 
        "reply": ai_plan.get("reply", "方案已制定。"), 
        "count_advice": len(new_advices),
        "count_tasks": len(new_tasks)
    }

@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: int,
    db: Session = Depends(get_session),
    uid: int = Depends(get_current_user_id)
):
    # 🕵️‍♂️ 监控器 1：看后端到底在读哪里的数据库文件
    from app.db import engine
    db_url = str(engine.url)
    print(f"\n🚀 [DEBUG START] 开始尝试删除会话...")
    print(f"📂 后端正在连接的数据库: {db_url}")
    
    # 1. 查找该会话
    session_obj = db.get(ConsultSession, session_id)
    
    # 🕵️‍♂️ 监控器 2：看查找结果
    if session_obj is None:
        print(f"❌ [FAIL] 数据库里没找到 ID 为 {session_id} 的记录！")
        # 💡 这里我们返回 404，不返回 200，让前端报错
        raise HTTPException(status_code=404, detail=f"数据库文件中没有 ID {session_id}，请检查文件路径是否正确")

    print(f"🔍 [SUCCESS] 找到了会话：ID={session_obj.id}, 标题='{session_obj.title}'")

    # 权限检查
    if session_obj.user_id != uid:
        print(f"🚫 [DENIED] 权限不足：会话归属用户 {session_obj.user_id}，当前用户 {uid}")
        raise HTTPException(status_code=403, detail="无权删除此记录")

    # 3. 删掉关联的聊天消息
    statement = select(ChatMessage).where(ChatMessage.session_id == session_id)
    messages = db.exec(statement).all()
    print(f"🗑️ [PREPARE] 正在标记删除关联的 {len(messages)} 条聊天记录...")
    for msg in messages:
        db.delete(msg)

    # 4. 删掉会话本体
    db.delete(session_obj)
    
    # 5. 【临门一脚】提交
    print(f"💾 [ACTION] 执行 db.commit() ...")
    db.commit() 
    
    print(f"✅ [DONE] 删除操作已提交到硬盘！\n")
    return {"ok": True, "msg": "删除成功"}