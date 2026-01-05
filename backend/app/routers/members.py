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
    height: float | None = None 
    weight: float | None = None 
    tags: list[str] | dict[str, dict] | None = None
    allergies: str | None = None 
    meds: str | None = None      

# 2. 新增 MemberUpdate (用于编辑，所有字段都是选填)
class MemberUpdate(BaseModel):
    name: str | None = None
    relation: str | None = None
    gender: str | None = None
    age: int | None = None
    height: float | None = None # 🆕
    weight: float | None = None # 🆕
    tags: list[str] | dict[str, dict] | None = None
    allergies: str | None = None # 🆕
    meds: str | None = None      # 🆕

class MemberOut(BaseModel):
    id: int
    name: str
    relation: str
    gender: str | None = None
    age: int | None = None
    height: float | None = None # 🆕
    weight: float | None = None # 🆕
    tags: dict[str, dict] = {}
    allergies: str | None = None # 🆕
    meds: str | None = None      # 🆕

def dump_tags(tags: list[str]) -> str:
    # 如果前端传的是原来的列表格式 ['高血压', '肥胖']
    if isinstance(tags, list):
        # 自动为每个标签初始化：Level 2 (确诊), Score 100 (起始风险满分)
        structured_data = {
            tag: {"level": 2, "score": 100} for tag in tags
        }
        return json.dumps(structured_data, ensure_ascii=False)
    
    # 如果已经是字典格式了，直接存
    return json.dumps(tags, ensure_ascii=False)

def load_tags(s: str) -> list[str]:
    try:
        data = json.loads(s) if s else {}
        
        # 核心兼容逻辑：如果读出来还是旧的列表格式 ['高血压']
        if isinstance(data, list):
            # 瞬间把它升级为新格式返回给前端
            return {tag: {"level": 2, "score": 100} for tag in data}
            
        return data
    except Exception:
        return {}

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
            height=m.height,   # 🆕 记得加上这几行
            weight=m.weight,   # 🆕
            allergies=m.allergies, # 🆕
            meds=m.meds,       # 🆕
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
        height=data.height,   # 🆕
        weight=data.weight,   # 🆕
        allergies=data.allergies, # 🆕
        meds=data.meds,       # 🆕
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
        height=m.height,   # 🆕
        weight=m.weight,   # 🆕
        allergies=m.allergies, # 🆕
        meds=m.meds,       # 🆕
        tags=load_tags(m.tags_json),
    )

# 更新成员信息
@router.put("/members/{member_id}")
def update_member(
    member_id: int,
    data: MemberUpdate,
    session: Session = Depends(get_session),
    uid: int = Depends(get_current_user_id),
):
    member = session.get(FamilyMember, member_id)
    if not member or member.user_id != uid:
        raise HTTPException(status_code=404, detail="成员不存在")

    update_data = data.model_dump(exclude_unset=True)
    
    # 特殊处理 tags -> tags_json
    if "tags" in update_data:
        member.tags_json = dump_tags(update_data.pop("tags"))
        
    for k, v in update_data.items():
        setattr(member, k, v)
        
    session.add(member)
    session.commit()
    return {"ok": True}

# 删除成员
@router.delete("/members/{member_id}")
def delete_member(member_id: int, session: Session = Depends(get_session)):
    # 1. 直接按 ID 找人
    member = session.get(FamilyMember, member_id)
    
    if not member:
        raise HTTPException(status_code=404, detail="找不到该成员")

    # 2. 【核心逻辑】只看关系，如果是本人，直接拦截
    if member.relation == "本人":
        raise HTTPException(status_code=400, detail="本人账号无法删除")

    # 3. 其他的一律删除
    session.delete(member)
    session.commit()
    
    return {"ok": True}