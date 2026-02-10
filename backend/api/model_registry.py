# backend/api/models.py
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from db.db_models.model import Model
from datetime import datetime
import uuid
import pickle
import pandas as pd
from sklearn.metrics import r2_score, mean_absolute_error
from pathlib import Path
from db.db_models.user_table import User  # 你的用户表
from api.auth import get_current_user

router = APIRouter(prefix="/models", tags=["Model Registry"])

# 系统数据集路径
SYSTEM_DATASET_PATH = r"D:\vueproject\Ti-design\backend\data\datasets\system\newdata3.csv"

# -------------------------------
# 上传模型
# -------------------------------
@router.post("/register")
def register_model_api(
    model_name: str = Form(...),
    features: str = Form(...),
    target: str = Form(...),
    model_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user) # 这里接你的用户认证依赖
):
    try:
        # 解析特征列表
        features_list = [f.strip() for f in features.split(",") if f.strip()]
        if not features_list:
            raise HTTPException(status_code=400, detail="Features list cannot be empty")

        # 检查用户是否已上传同名模型
        existing = db.query(Model).filter_by(
            user_id=user.id,
            model_name=model_name
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="You have already uploaded a model with this name")

        # 创建存储路径
        model_uuid = str(uuid.uuid4())
        model_dir = Path(
            f"backend/data/models/user_{user.id}/{model_uuid}_{model_name}"
        )
        model_dir.mkdir(parents=True, exist_ok=True)
        model_path = model_dir / "model.pkl"

        # 保存模型文件
        with open(model_path, "wb") as f:
            f.write(model_file.file.read())

        # 创建数据库记录
        new_model = Model(
            user_id=user.id,
            model_name=model_name,
            model_file_path=str(model_path),
            features=features_list,
            target=target,
            status="uploaded",
            task_type="regression",  # 可以前端扩展传 task_type
            created_at=datetime.utcnow()
        )
        db.add(new_model)
        db.commit()
        db.refresh(new_model)

        return {"message": "Model registered successfully", "model_id": new_model.id}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------
# 评估模型
# -------------------------------
@router.post("/evaluate/{model_id}")
def evaluate_model(model_id: int, db: Session = Depends(get_db)):
    model = db.query(Model).filter_by(id=model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    model_path = Path(model.model_file_path)
    if not model_path.exists():
        raise HTTPException(status_code=404, detail="Model file not found on server")

    try:
        print(f"Evaluating model: {model.model_name}")
        print(f"Model path: {model_path}")
        print(f"Features: {model.features}")
        print(f"Target: {model.target}")

        # 安全加载 pickle 模型
        with open(model_path, "rb") as f:
            loaded_model = pickle.load(f)

        # 读取系统数据集
        df = pd.read_csv(SYSTEM_DATASET_PATH)
        print("Dataset columns:", df.columns.tolist())

        missing_features = [f for f in model.features if f not in df.columns]
        if missing_features:
            raise HTTPException(
                status_code=400,
                detail=f"Missing feature columns in dataset: {missing_features}"
            )

        X = df[model.features]
        y = df[model.target]

        y_pred = loaded_model.predict(X)

        # 计算指标
        r2 = r2_score(y, y_pred)
        mae = mean_absolute_error(y, y_pred)

        model.metrics = {"r2_score": r2, "mae": mae}
        model.status = "evaluated"
        model.evaluated_at = datetime.utcnow()
        db.commit()
        db.refresh(model)

        return {
            "model_id": model.id,
            "r2_score": r2,
            "mae": mae,
            "predictions": y_pred[:10].tolist()
        }

    except Exception as e:
        print("Error during evaluation:", e)
        import traceback
        traceback.print_exc()

        model.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Model evaluation failed: {str(e)}")


    except Exception as e:
        model.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=f"Model evaluation failed: {str(e)}")


# -------------------------------
# 列出模型
# -------------------------------
@router.get("/")
def list_models(db: Session = Depends(get_db)):
    models = db.query(Model).all()
    return {
        "data": [
            {
                "model_id": m.id,
                "user_id": m.user_id,
                "model_name": m.model_name,
                "task_type": m.task_type,
                "status": m.status,
                "metrics": m.metrics,
                "created_at": m.created_at,
                "evaluated_at": m.evaluated_at
            }
            for m in models
        ]
    }
