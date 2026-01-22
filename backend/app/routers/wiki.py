from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import List, Optional
from fastapi import Request
from sqlalchemy import func, text
import json

from ..db import get_session
from ..models import WikiArticle

router = APIRouter(tags=["Wiki"])

@router.get("/wiki/recommend")
def recommend_wiki(
    # 💡 2. 我们直接通过 request 拿原始数据，跳过 Pydantic 的验证
    request: Request, 
    session: Session = Depends(get_session)
):
    # 💡 3. 手动提取参数
    category = request.query_params.get("category", "common")
    print(f"📡【强力捕获】收到推荐请求，分类是: {category}")

    # 逻辑保持不变
    statement = select(WikiArticle).where(WikiArticle.category == category).order_by(func.random()).limit(3)
    results = session.exec(statement).all()
    
    if len(results) < 3 and category != "common":
        extras = session.exec(select(WikiArticle).where(WikiArticle.category == "common").limit(3 - len(results))).all()
        results.extend(extras)
        
    return results

@router.get("/wiki/search")
def search_wiki(
    q: str, # 接收前端传来的搜索关键词
    session: Session = Depends(get_session)
):
    """
    根据关键词模糊搜索文章标题和内容
    """
    if not q:
        return []
        
    # 1. 优先搜索标题匹配的文章
    title_matches = session.exec(
        select(WikiArticle).where(WikiArticle.title.contains(q)).limit(10)
    ).all()
    
    # 2. 获取已找到文章的 ID，防止重复
    found_ids = {article.id for article in title_matches}
    
    results = list(title_matches) # 先把头等奖装进去
    
    # 3. 如果头等奖还不够 10 个，再去内容里找
    if len(results) < 10:
        needed = 10 - len(results)
        
        content_matches = session.exec(
            select(WikiArticle).where(
                # 💡 确保内容匹配，且不是刚才已经找到的
                WikiArticle.content.contains(q),
                WikiArticle.id.not_in(found_ids) 
            ).limit(needed)
        ).all()
        
        # 把参与奖追加到后面
        results.extend(content_matches)
    
    return results

# 1. 获取百科列表 (支持按分类过滤)
@router.get("/wiki", response_model=List[WikiArticle])
def list_wiki(
    category: Optional[str] = None, 
    session: Session = Depends(get_session)
):
    statement = select(WikiArticle)
    if category and category != "all":
        statement = statement.where(WikiArticle.category == category)
    
    statement = statement.order_by(WikiArticle.id.desc())
    return session.exec(statement).all()

# 2. 获取文章详情
@router.get("/wiki/{article_id}", response_model=WikiArticle)
def get_wiki_detail(article_id: int, session: Session = Depends(get_session)):
    article = session.get(WikiArticle, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    return article

