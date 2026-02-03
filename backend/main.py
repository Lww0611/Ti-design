from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.endpoints import router as api_router

# ✅ 新增：数据库相关
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

# 路由
app.include_router(api_router, prefix="/api")

# ✅ 启动时自动建表
from services.dataset_init import init_system_datasets

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    init_system_datasets()   # ✅ 自动导入系统数据集


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
