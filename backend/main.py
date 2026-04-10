import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ✅ 修改：改为引用重构后的总路由聚合器
from api.v1.router import api_router

# ✅ 数据库相关 (保持逻辑不变，路径改为绝对引用)
from db.session import engine
from db.base import Base
import db.db_models  # 必须导入，注册所有 ORM 表
# main.py
from db.db_models.case_table import Case

app = FastAPI(title="Titanium Alloy Research API")

# 允许跨域（Render + Vercel 建议用 CORS_ORIGINS 精确配置）
# 例如：
# CORS_ORIGINS=https://your-app.vercel.app,https://www.your-domain.com
raw_cors = os.getenv("CORS_ORIGINS", "*").strip()
allow_origins = ["*"] if raw_cors == "*" else [
    origin.strip() for origin in raw_cors.split(",") if origin.strip()
]
# 允许 Vercel 预览域名（每次部署子域会变化），可按需覆盖为更严格正则
# 例如：^https://ti-design(-[a-z0-9-]+)?\\.vercel\\.app$
raw_cors_regex = os.getenv("CORS_ORIGIN_REGEX", r"^https://.*\.vercel\.app$")
allow_origin_regex = None if raw_cors == "*" else (raw_cors_regex or None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_origin_regex=allow_origin_regex,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ 路由挂载修改
# api_router 内部已经包含了 auth, predictions, datasets, tasks
app.include_router(api_router, prefix="/api/v1")

# ✅ 启动逻辑保持不变
from services.dataset.dataset_init import init_system_datasets
from services.builtin_models import init_builtin_models

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    init_system_datasets()   # ✅ 自动导入系统数据集
    init_builtin_models()    # ✅ 内置预测模型写入 model 表


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload_enabled = os.getenv("RELOAD", "false").lower() in {"1", "true", "yes", "on"}
    uvicorn.run("main:app", host=host, port=port, reload=reload_enabled)