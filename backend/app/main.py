# 后端入口文件，负责“启动 FastAPI + 注册中间件/路由 + 启动时初始化

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles 

from .db import create_db_and_tables

from .routers import auth
from .routers import me
from .routers import members
from .routers import advice
from .routers import tasks
from .routers import consult 




app = FastAPI(title="AI问诊APP API")

app.include_router(auth.router, prefix="/api")
app.include_router(me.router, prefix="/api")
app.include_router(members.router, prefix="/api")
app.include_router(advice.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(consult.router, prefix="/api")

app.mount("/static", StaticFiles(directory="static"), name="static")

# 允许前端本地开发访问（Vue 默认 5173）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/api/health")
def health():
    return {"ok": True}

