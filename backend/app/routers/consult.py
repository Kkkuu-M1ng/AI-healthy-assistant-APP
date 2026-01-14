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
from app.models import ConsultSession, ChatMessage, AdviceItem, TaskItem, FamilyMember
from app.core.auth import get_current_user_id
from app.services.llm import chat_with_ai_vision, summarize_session_title, generate_health_plan

router = APIRouter(prefix="/consult", tags=["Consult"])

def dump_json(obj):
    return json.dumps(obj, ensure_ascii=False)

class ChatRequest(BaseModel):
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
    content: str, 
    data: ChatRequest, 
    db: Session = Depends(get_session), 
    uid: int = Depends(get_current_user_id)
):
    # A. 基础校验
    session_obj = db.get(ConsultSession, session_id)
    if not session_obj or session_obj.user_id != uid:
        raise HTTPException(status_code=404, detail="会话不存在")

    member = db.get(FamilyMember, session_obj.member_id)
    # 构造给 AI 看的画像字典
    persona_data = {
        "name": member.name, "age": member.age, "gender": member.gender,
        "height": member.height, "weight": member.weight,
        "tags": load_tags(member.tags_json),
        "allergies": member.allergies, "meds": member.meds, "notes": member.notes
    }

    # B. 存用户消息
    user_msg = ChatMessage(session_id=session_id, role="user", content=content)
    db.add(user_msg)
    db.commit()

    # C. 打包历史记录
    history_rows = db.exec(select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at)).all()
    payload = [{"role": m.role, "content": m.content} for m in history_rows]

    # D. 🚀 调用通义千问 (识图 + 提取标签版本)
    ai_result = chat_with_ai_vision(payload, persona_data, data.image_base64)
    ai_reply_text = ai_result.get("reply", "我正在思考...")

    # E. 【画像进化】如果 AI 发现了新症状，自动打标签
    new_tags_found = ai_result.get("new_tags", [])
    if new_tags_found:
        current_tags = load_tags(member.tags_json)
        for t_name in new_tags_found:
            if t_name not in current_tags:
                current_tags[t_name] = {"level": 2, "score": 100} # 默认确诊级别
        member.tags_json = dump_tags(current_tags)
        db.add(member)

    # F. 存入 AI 回复气泡
    ai_msg = ChatMessage(session_id=session_id, role="assistant", content=ai_reply_text)
    db.add(ai_msg)

    # G. 🚀 【核心亮点】调用你写的标题总结函数
    # 逻辑：如果是第一轮有效的对话，且标题还是默认的
    if len(history_rows) <= 4:
        # 💡 只有当标题是初始值，或者还是空的，才起名
        if session_obj.title in ["新问诊会话", "新会话", "", None]:
            try:
                # 1. 清理指令，只留用户原话
                clean_content = content.split("用户描述：")[-1] if "用户描述：" in content else content
                
                # 2. 拼接上下文，让 AI 总结更准
                # 用户问 + AI 刚回复的话
                context_for_naming = f"用户问：{clean_content}\nAI答：{ai_reply_text[:40]}"
                
                print(f"🕵️‍♂️ 正在为会话 ID {session_id} 申请 AI 起名...")
                
                # 3. 调 LLM 函数
                new_title = summarize_session_title(context_for_naming)
                
                # 4. 强制写入并打印（方便你观察）
                if new_title and len(new_title) > 0:
                    session_obj.title = new_title
                    print(f"✨【成功】标题已进化为: {new_title}")
                
                # 必须 add 确保 SQLModel 追踪到这个修改
                db.add(session_obj) 
                
            except Exception as e:
                print(f"⚠️ 标题总结小失败(跳过): {e}")
                # 失败了也不要让程序死掉，给个默认标题
                if not session_obj.title:
                    session_obj.title = clean_content[:10]

    # H. 最终统一提交
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

    # 3. 🚀 【关键修复】：将 notes 字段喂给 AI，并处理标签格式
    # 之前 AI 0 建议是因为你没把家人备注传过去，AI 觉得没信息可总结
    persona_brief = {
        "name": member.name,
        "age": member.age, 
        "gender": member.gender, 
        "tags": load_tags(member.tags_json), # 使用我们写好的 load_tags 转成字典
        "allergies": member.allergies, 
        "meds": member.meds,
        "notes": member.notes # 👈 必须带上这个“全能备注”！
    }

    # 🔍 调试打印 1：看看发给 AI 的档案对不对
    print(f"📡 发送给 AI 的画像数据: {persona_brief}")

    # 4. 调用 AI 总结
    ai_plan = generate_health_plan(history_payload, persona_brief)

    # 🔍 调试打印 2：看看 AI 到底回了什么
    print(f"🤖 AI 返回的原始 JSON: {ai_plan}")

    # 5. 提取数据
    new_advices = ai_plan.get("new_advice", [])
    new_tasks = ai_plan.get("new_tasks", [])

    for item in new_advices:
        if not isinstance(item, dict): continue
        
        # 💡 尝试从多种可能的键名中抓取标题和理由
        title = item.get("title") or item.get("name") or "健康建议"
        reason = item.get("reason") or item.get("content") or item.get("principle") or "根据问诊生成"
        tags = item.get("tags") or []
        
        advice = AdviceItem(
            user_id=uid,
            member_id=member.id,
            title=str(title),
            reason=str(reason),
            tags_json=json.dumps(tags, ensure_ascii=False),
            expire_at=datetime.utcnow() + timedelta(days=30),
            is_active=True
        )
        db.add(advice)

    # --- B. 任务入库 (全兼容模式) ---
    for item in new_tasks:
        if not isinstance(item, dict): continue
        
        # 💡 关键：同时兼容 "title" 和 AI 刚才吐出的 "task"
        t_title = item.get("title") or item.get("task") or "健康任务"
        t_freq = item.get("freq") or item.get("time") or "由医生建议"
        t_due = item.get("due") or item.get("note") or "尽快开始"
        
        task = TaskItem(
            user_id=uid, 
            member_id=member.id, 
            title=str(t_title), # 👈 确保这里绝对不是 None
            freq=str(t_freq),
            due=str(t_due),
            done=False,
            detail_json="[]",
            logs_json="[]"
        )
        db.add(task)

    # 6. 提交
    db.commit()

    # 🔍 调试打印 3：确认最终入库数量
    print(f"✅ 成功入库：{len(new_advices)} 条建议, {len(new_tasks)} 条任务")

    return {
        "ok": True, 
        "reply": ai_plan.get("reply", "方案生成完毕。"), 
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