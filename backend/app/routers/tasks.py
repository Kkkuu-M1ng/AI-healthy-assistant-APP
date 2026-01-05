from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select
import json

from ..db import get_session
from ..core.auth import get_current_user_id
from ..models import TaskItem, FamilyMember 
from app.core.engine import update_persona_risk 
from app.routers.members import load_tags, dump_tags

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

class TaskDetailOut(BaseModel):
    id: int
    member_id: int
    title: str
    freq: str
    due: str
    done: bool
    detail: list[str]
    logs: list[str]

@router.get("/tasks", response_model=list[TaskListOut])
def list_tasks(
    member_id: int = Query(...),
    session: Session = Depends(get_session),
    uid: int = Depends(get_current_user_id),
):
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
        )
        for t in rows
    ]

@router.get("/tasks/{task_id}", response_model=TaskDetailOut)
def get_task_detail(
    task_id: int,
    session: Session = Depends(get_session),
    uid: int = Depends(get_current_user_id),
):
    t = session.get(TaskItem, task_id)
    if not t or t.user_id != uid:
        raise HTTPException(status_code=404, detail="任务不存在")

    return TaskDetailOut(
        id=t.id,
        member_id=t.member_id,
        title=t.title,
        freq=t.freq,
        due=t.due,
        done=t.done,
        detail=load_list(t.detail_json),
        logs=load_list(t.logs_json),
    )

@router.post("/tasks/{task_id}/complete")
def complete_task(
    task_id: int,
    session: Session = Depends(get_session),
    uid: int = Depends(get_current_user_id),
):
    # A. 找到任务
    task = session.get(TaskItem, task_id)
    if not task or task.user_id != uid:
        raise HTTPException(status_code=404, detail="任务不存在")
    if task.done:
        return {"ok": True, "msg": "已完成"}

    # B. 标记任务完成
    task.done = True
    
    # C. 【重点】驱动画像进化
    member = session.get(FamilyMember, task.member_id)
    if member:
        # 1. 解析当前标签字典
        current_tags = load_tags(member.tags_json)
        
        # 2. 调用引擎计算新画像
        # 我们把任务标题传进去，让引擎判断该给谁减分
        new_tags = update_persona_risk(current_tags, task.title)
        
        # 3. 存回数据库
        member.tags_json = dump_tags(new_tags)
        session.add(member)

    session.commit()
    return {"ok": True, "msg": "打卡成功，画像已自动进化"}

# （测试用）创建任务：方便你在 Swagger 里先验证 list/detail
@router.post("/tasks", response_model=TaskDetailOut)
def create_task(
    data: TaskCreate,
    session: Session = Depends(get_session),
    uid: int = Depends(get_current_user_id),
):
    t = TaskItem(
        user_id=uid,
        member_id=data.member_id,
        title=data.title,
        freq=data.freq,
        due=data.due,
        done=False,
        detail_json=dump_list(data.detail),
        logs_json="[]",
    )
    session.add(t)
    session.commit()
    session.refresh(t)

    return TaskDetailOut(
        id=t.id,
        member_id=t.member_id,
        title=t.title,
        freq=t.freq,
        due=t.due,
        done=t.done,
        detail=data.detail,
        logs=[],
    )
