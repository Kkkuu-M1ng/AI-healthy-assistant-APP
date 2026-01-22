from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select
from datetime import datetime
import json

from ..db import get_session
from ..core.auth import get_current_user_id
from ..models import AdviceItem

router = APIRouter(tags=["advice"])

def dump_list(v: list[str]) -> str:
    return json.dumps(v, ensure_ascii=False)

def load_list(s: str) -> list[str]:
    try:
        return json.loads(s) if s else []
    except Exception:
        return []

class AdviceCreate(BaseModel):
    member_id: int
    title: str
    reason: str = ""
    tags: list[str] = []
    detail: list[str] = []

class AdviceListOut(BaseModel):
    id: int
    member_id: int
    title: str
    reason: str
    tags: list[str]

class AdviceDetailOut(BaseModel):
    id: int
    member_id: int
    title: str
    reason: str
    tags: list[str]
    detail_json: str | None = None

@router.get("/advice", response_model=list[AdviceListOut])
def list_advice(
    member_id: int = Query(...),
    session: Session = Depends(get_session),
    uid: int = Depends(get_current_user_id),
):
    # 💡 核心过滤逻辑：
    # 1. 属于当前用户和成员
    # 2. is_active 为 True
    # 3. (expire_at 为空) 或者 (expire_at 大于当前时间)
    now = datetime.utcnow()
    
    statement = select(AdviceItem).where(
        AdviceItem.user_id == uid,
        AdviceItem.member_id == member_id,
        AdviceItem.is_active == True,
        (AdviceItem.expire_at == None) | (AdviceItem.expire_at > now) # 👈 过滤过期数据
    ).order_by(AdviceItem.id.desc())
    
    rows = session.exec(statement).all()

    return [
        AdviceListOut(
            id=a.id,
            member_id=a.member_id,
            title=a.title,
            reason=a.reason,
            tags=load_list(a.tags_json),
        )
        for a in rows
    ]

@router.get("/advice/{advice_id}", response_model=AdviceDetailOut)
def get_advice_detail(
    advice_id: int,
    session: Session = Depends(get_session),
    uid: int = Depends(get_current_user_id),
):
    a = session.get(AdviceItem, advice_id)
    if not a or a.user_id != uid:
        raise HTTPException(status_code=404, detail="建议不存在")

    return AdviceDetailOut(
        id=a.id,
        member_id=a.member_id,
        title=a.title,
        reason=a.reason,
        tags=load_list(a.tags_json),
        detail_json=a.detail_json, # 👈 直接把 JSON 字符串给前端
    )

@router.delete("/{advice_id}") # 💡 同理，这里只需收 ID
def delete_advice(
    advice_id: int,
    db: Session = Depends(get_session),
    uid: int = Depends(get_current_user_id)
):
    advice = db.get(AdviceItem, advice_id)
    
    if not advice or advice.user_id != uid:
        raise HTTPException(status_code=404, detail="建议不存在或无权操作")
    
    db.delete(advice)
    db.commit()
    
    return {"ok": True, "msg": "建议已删除"}