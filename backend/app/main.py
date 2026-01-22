# 后端入口文件，负责“启动 FastAPI + 注册中间件/路由 + 启动时初始化
import os
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
from .routers import wiki

app = FastAPI(title="AI问诊APP API")

# 允许前端本地开发访问（Vue 默认 5173）
app.add_middleware(
    CORSMiddleware,
    # allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "https://2e6c8f2.r21.vip.cpolar.cn"],
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(me.router, prefix="/api")
app.include_router(members.router, prefix="/api")
app.include_router(advice.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(consult.router, prefix="/api")
app.include_router(wiki.router, prefix="/api")

app.mount("/static", StaticFiles(directory="static"), name="static")



current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. 向上走两级，找到 frontend/dist
# 如果你的 dist 确实在 frontend 下，路径应该是这样的：
frontend_path = os.path.join(current_dir, "..", "..", "frontend", "dist")
if os.path.exists(frontend_path):
    print(f"🏠 成功找到前端网页！路径为: {frontend_path}")
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
else:
    print(f"❌ 警告：没找到前端文件夹，请确认执行过 npm run build。当前计算路径为: {frontend_path}")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/api/health")
def health():
    return {"ok": True}
