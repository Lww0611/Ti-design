from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ✅ 修改：改为引用重构后的总路由聚合器
from api.v1.router import api_router

# ✅ 数据库相关 (保持逻辑不变，路径改为绝对引用)
from db.session import engine
from db.base import Base
import db.db_models  # 必须导入，注册所有 ORM 表

app = FastAPI(title="Titanium Alloy Research API")

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ 路由挂载修改
# api_router 内部已经包含了 auth, predictions, datasets, tasks
app.include_router(api_router, prefix="/api/v1")

# ✅ 启动逻辑保持不变
from services.dataset_init import init_system_datasets

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    init_system_datasets()   # ✅ 自动导入系统数据集


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)