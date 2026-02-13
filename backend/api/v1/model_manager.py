import io
import pandas as pd
import traceback
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from sklearn.metrics import r2_score

from core import config
from db.session import get_db
from db.db_models.model import Model
from api.v1.auth import get_current_user
from utils.model_loader import try_load_model
# 请确保该文件路径正确
from services.model_registry.validator import validate_metadata_against_dataset

model_manager_router = APIRouter(prefix="/models", tags=["Model Registry"])

print("🔥 [SYSTEM] 钛合金融合网络模型管理模块（优化版）已就绪")

# --- 1. [新增] 契约公示：获取系统数据集可用列名 ---
@model_manager_router.get("/columns")
async def get_system_columns(user = Depends(get_current_user)):
    """获取 newdata3.csv 的所有列名，供前端多选框使用"""
    try:
        if not config.SYSTEM_DATASET_PATH.exists():
            raise HTTPException(status_code=404, detail="系统评估数据集缺失")

        # 只读取一行来获取表头
        df_header = pd.read_csv(config.SYSTEM_DATASET_PATH, nrows=0)
        return {"columns": df_header.columns.tolist()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取表头失败: {str(e)}")

# --- 2. [重构] 建立契约：模型注册 (带严格校验) ---
@model_manager_router.post("/register")
async def register_model_api(
    model_name: str = Form(...),
    features: str = Form(...),
    target: str = Form(...),
    description: str = Form(None),
    model_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    try:
        # 检查重名
        if db.query(Model).filter_by(user_id=user.id, model_name=model_name).first():
            raise HTTPException(status_code=400, detail="模型名称已存在")

        # ✅ 特征清洗
        features_list = [f.strip().strip('"').strip("'") for f in features.split(",") if f.strip()]
        cleaned_target = target.strip().strip('"').strip("'")

        # ✅ 核心约束：校验特征是否属于系统数据集子集
        df_header = pd.read_csv(config.SYSTEM_DATASET_PATH, nrows=0)
        system_cols = df_header.columns.tolist()
        try:
            validate_metadata_against_dataset(features_list, cleaned_target, system_cols)
        except ValueError as ve:
            raise HTTPException(status_code=400, detail=f"特征对齐失败: {str(ve)}")

        # 读取二进制并验证
        model_bytes = await model_file.read()
        try_load_model(model_bytes)

        new_model = Model(
            user_id=user.id,
            model_name=model_name,
            content=model_bytes,
            features=features_list,  # 存储干净的列表
            target=cleaned_target,
            description=description,
            status="uploaded",
            created_at=datetime.utcnow()
        )
        db.add(new_model)
        db.commit()

        return {
            "success": True,
            "message": "模型已通过对齐校验并存入数据库",
            "data": {"id": new_model.id, "model_name": model_name}
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        db.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"注册失败: {str(e)}")

# --- 3. [重构] 执行契约：模型评估 (精准切片) ---
@model_manager_router.post("/{model_id}/evaluate")
async def evaluate_model(model_id: int, db: Session = Depends(get_db), user = Depends(get_current_user)):
    # ... (查询模型记录和加载模型对象的代码)

    try:
        # 1. 加载数据集
        df = pd.read_csv(config.SYSTEM_DATASET_PATH)

        # 2. 调用外部 evaluator 函数（不再在 API 里手写计算过程）
        r2 = evaluate_model_on_data(
            model_obj=model_obj,
            df=df,
            features=model_rec.features,
            target_col=model_rec.target
        )

        # 3. 更新数据库记录
        model_rec.metrics = {"r2_score": r2}
        model_rec.status = "evaluated"
        model_rec.evaluated_at = datetime.utcnow()
        db.commit()

        return {"r2_score": r2, "status": "success"}
    except Exception as e:
        db.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"评估运行报错: {str(e)}")

# --- 4. 模型删除 (原有逻辑) ---
@model_manager_router.delete("/{model_id}")
async def delete_model(model_id: int, db: Session = Depends(get_db), user = Depends(get_current_user)):
    model_rec = db.query(Model).filter(Model.id == model_id, Model.user_id == user.id).first()
    if not model_rec:
        raise HTTPException(status_code=404, detail="无权删除该模型")

    try:
        db.delete(model_rec)
        db.commit()
        return {"success": True, "message": "模型已移除"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

# --- 5. 模型列表 (原有规避二进制逻辑) ---
@model_manager_router.get("")
def list_models(db: Session = Depends(get_db), user = Depends(get_current_user)):
    # 明确指定字段，排除 model.content 防止二进制流导致编码错误或响应过慢
    stmt = select(
        Model.id,
        Model.model_name,
        Model.features,
        Model.target,
        Model.status,
        Model.metrics,
        Model.description,
        Model.created_at
    ).order_by(Model.created_at.desc())

    results = db.execute(stmt).all()

    formatted_data = []
    for row in results:
        formatted_data.append({
            "id": row.id,
            "model_name": row.model_name,
            "features": row.features,
            "target": row.target,
            "status": row.status,
            "metrics": row.metrics,
            "description": row.description,
            "created_at": row.created_at
        })

    return {"data": formatted_data}