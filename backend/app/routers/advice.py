from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select
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
    detail: list[str]

@router.get("/advice", response_model=list[AdviceListOut])
def list_advice(
    member_id: int = Query(...),
    session: Session = Depends(get_session),
    uid: int = Depends(get_current_user_id),
):
    rows = session.exec(
        select(AdviceItem)
        .where(AdviceItem.user_id == uid, AdviceItem.member_id == member_id)
        .order_by(AdviceItem.id.desc())
    ).all()

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
        detail=load_list(a.detail_json),
    )

# （测试用）创建建议：方便你在 Swagger 里先验证 list/detail
@router.post("/advice", response_model=AdviceDetailOut)
def create_advice(
    data: AdviceCreate,
    session: Session = Depends(get_session),
    uid: int = Depends(get_current_user_id),
):
    a = AdviceItem(
        user_id=uid,
        member_id=data.member_id,
        title=data.title,
        reason=data.reason,
        tags_json=dump_list(data.tags),
        detail_json=dump_list(data.detail),
    )
    session.add(a)
    session.commit()
    session.refresh(a)

    return AdviceDetailOut(
        id=a.id,
        member_id=a.member_id,
        title=a.title,
        reason=a.reason,
        tags=data.tags,
        detail=data.detail,
    )
