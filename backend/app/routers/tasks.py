from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select
import json

from ..db import get_session
from ..core.auth import get_current_user_id
from ..models import TaskItem, FamilyMember 
from app.core.engine import update_persona_risk 
from app.routers.members import load_tags, dump_tags
from app.services.risk_engine import apply_task_checkin, checkin_with_rebound
from datetime import datetime, date, timedelta

router = APIRouter(tags=["tasks"])

def dump_list(v: list[str]) -> str:
    return json.dumps(v, ensure_ascii=False)

def load_list(s: str) -> list[str]:
    try:
        return json.loads(s) if s else []
    except Exception:
        return []

class TaskCreate(BaseModel):
    member_id: int
    title: str
    freq: str = ""
    due: str = ""
    detail: list[str] = []

class TaskListOut(BaseModel):
    id: int
    member_id: int
    title: str
    freq: str
    due: str
    done: bool
    created_at: datetime

class TaskDetailOut(BaseModel):
    id: int
    member_id: int
    title: str
    freq: str
    due: str
    done: bool
    detail: list[str]
    logs: list[str]
    score: int | None
    current_level: int | None
    safe_days_needed: int
    safe_days: int
    doneToday: bool
    streak: int
    delta: dict
    repeating: bool
    safe_levels: list
    created_at: datetime

@router.post("/tasks/{task_id}/complete")
def complete_task(
    task_id: int,
    session: Session = Depends(get_session),
    uid: int = Depends(get_current_user_id),
):
    # 1. 获取任务并进行安全检查
    task = session.get(TaskItem, task_id)
    if not task or task.user_id != uid:
        raise HTTPException(status_code=404, detail="任务不存在或无权操作")

    # 2. 判断任务是否允许再次打卡
    # 一次性任务如果做完了，直接返回
    if not task.repeating and task.done:
        return {"ok": False, "msg": "该任务已永久完成"}
    # 循环任务如果今天打过卡了，也直接返回
    if task.repeating and task.last_completed_at and task.last_completed_at.date() == date.today():
        return {"ok": False, "msg": "今日已打卡，请明天再来"}

    # 3. 核心：计算连续打卡天数
    yesterday = datetime.utcnow().date() - timedelta(days=1)
    if task.last_completed_at and task.last_completed_at.date() == yesterday:
        task.streak += 1 # 昨天打了，是连续的
    else:
        task.streak = 1 # 中断了，重新从 1 开始

    # 4. 更新任务自身状态
    task.last_completed_at = datetime.utcnow()
    logs = json.loads(task.logs_json or "[]")
    logs.append(task.last_completed_at.strftime("%Y-%m-%d %H:%M"))
    task.logs_json = json.dumps(logs)
    if not task.repeating:
        task.done = True
    
    session.add(task)

    # 5. 核心：调用进化引擎，更新用户画像
    member = session.get(FamilyMember, task.member_id)
    if member:
        tags_before = load_tags(member.tags_json)
        # 💡 把任务的“连续天数”传给引擎，让它计算额外奖励
        # 注意：你的 risk_engine 也需要能接收 streak 参数
        result = checkin_with_rebound(tags_before, task.title)
        
        # 把进化后的新画像存回数据库
        member.tags_json = dump_tags(result["tags"])
        session.add(member)
    
    # 6. 一次性提交所有更改
    session.commit()
    
    # 7. 把分数变化返回给前端
    return { "ok": True, "delta": result.get("delta") }

@router.get("/tasks/{task_id}")
def get_task_detail(
    task_id: int,
    session: Session = Depends(get_session),
    uid: int = Depends(get_current_user_id),
):
    task = session.get(TaskItem, task_id)
    if not task: raise HTTPException(404)

    # 💡 1. 去查这个任务对应的家人画像
    member = session.get(FamilyMember, task.member_id)
    tags_data = load_tags(member.tags_json)
    
    # 2. 找到任务关联的那个标签
    related_tag_data = {}
    for tag_name, tag_info in tags_data.items():
        if tag_name in task.title:
            related_tag_data = tag_info
            break

    # 3. 构造“豪华套餐”返回给前端
    return {
        "id": task.id,
        "title": task.title,
        "freq": task.freq,
        "detail": json.loads(task.detail_json or "[]"),
        "logs": json.loads(task.logs_json or "[]"),
        "done": task.done,
        "repeating": task.repeating,
        "streak": task.streak,
        "safe_levels": [
            {"level": 3, "min_score": 70, "max_score": 100},
            {"level": 2, "min_score": 40, "max_score": 69},
            {"level": 1, "min_score": 15, "max_score": 39},
        ],
        # 👇👇👇 重点：把画像里的数据“借”过来 👇👇👇
        "score": related_tag_data.get("score"),
        "current_level": related_tag_data.get("level"),
        "safe_days": related_tag_data.get("safe_days", 0),
        "safe_days_needed": 7, # 暂时写死
        
        # 动态计算“今天打卡了吗”
        "doneToday": task.last_completed_at and task.last_completed_at.date() == date.today(),
    }

@router.get("/tasks", response_model=list[TaskListOut])
def list_tasks(
    member_id: int = Query(...),
    session: Session = Depends(get_session),
    uid: int = Depends(get_current_user_id),
):
    print(f"📥 后端收到请求，正在查找成员 ID 为: {member_id} 的任务")
    rows = session.exec(
        select(TaskItem)
        .where(TaskItem.user_id == uid, TaskItem.member_id == member_id)
        .order_by(TaskItem.id.desc())
    ).all()

    return [
        TaskListOut(
            id=t.id,
            member_id=t.member_id,
            title=t.title,
            freq=t.freq,
            due=t.due,
            done=t.done,
            created_at=t.created_at,
        )
        for t in rows
    ]

@router.delete("/tasks/{task_id}")  # 💡 既然 main.py 已经有了 /api/tasks 前缀，这里只需收 ID
def delete_task(
    task_id: int,
    db: Session = Depends(get_session),
    uid: int = Depends(get_current_user_id)
):
    # 1. 查找任务
    task = db.get(TaskItem, task_id)
    
    # 2. 安全检查：必须存在且属于当前用户
    if not task or task.user_id != uid:
        raise HTTPException(status_code=404, detail="任务不存在或无权操作")
    
    # 3. 执行删除
    db.delete(task)
    db.commit()
    
    return {"ok": True, "msg": "任务已删除"}