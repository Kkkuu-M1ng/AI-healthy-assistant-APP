from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
import json

from ..db import get_session
from ..models import FamilyMember
from ..core.auth import get_current_user_id

router = APIRouter(tags=["members"])

class MemberCreate(BaseModel):
    name: str
    relation: str
    gender: str | None = None
    age: int | None = None
    tags: list[str] = []

class MemberOut(BaseModel):
    id: int
    name: str
    relation: str
    gender: str | None = None
    age: int | None = None
    tags: list[str] = []

def dump_tags(tags: list[str]) -> str:
    return json.dumps(tags, ensure_ascii=False)

def load_tags(s: str) -> list[str]:
    try:
        return json.loads(s) if s else []
    except Exception:
        return []

@router.get("/members", response_model=list[MemberOut])
def list_members(
    session: Session = Depends(get_session),
    uid: int = Depends(get_current_user_id),
):
    rows = session.exec(
        select(FamilyMember).where(FamilyMember.user_id == uid).order_by(FamilyMember.id.desc())
    ).all()

    return [
        MemberOut(
            id=m.id,
            name=m.name,
            relation=m.relation,
            gender=m.gender,
            age=m.age,
            tags=load_tags(m.tags_json),
        )
        for m in rows
    ]

@router.post("/members", response_model=MemberOut)
def create_member(
    data: MemberCreate,
    session: Session = Depends(get_session),
    uid: int = Depends(get_current_user_id),
):
    m = FamilyMember(
        user_id=uid,
        name=data.name,
        relation=data.relation,
        gender=data.gender,
        age=data.age,
        tags_json=dump_tags(data.tags),
    )
    session.add(m)
    session.commit()
    session.refresh(m)

    return MemberOut(
        id=m.id,
        name=m.name,
        relation=m.relation,
        gender=m.gender,
        age=m.age,
        tags=load_tags(m.tags_json),
    )
