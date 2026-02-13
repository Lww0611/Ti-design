import os
import shutil
import uuid
import io
import pandas as pd
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

# 根据你的项目结构，请确保路径正确
from db.db_models.dataset_table import Dataset

# 建议使用相对路径，避免 D:\ 这种绝对路径
BASE_DATASET_DIR = "data/datasets"

def save_uploaded_dataset(
    db: Session,
    file: UploadFile,
    source_type: str = "user"
) -> Dataset:
    """
    保存数据集：用户数据存入数据库 BLOB，系统数据存入本地文件
    """
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")

    # 1. 读取文件内容
    try:
        file_bytes = file.file.read()
        # 验证是否为合法 CSV
        df = pd.read_csv(io.BytesIO(file_bytes))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CSV parse failed: {e}")

    if df.empty:
        raise HTTPException(status_code=400, detail="CSV file is empty.")

    file_path = None
    db_content = None

    # 2. 根据类型选择存储方案
    if source_type == "user":
        # 用户数据：直接存二进制
        db_content = file_bytes
    else:
        # 系统数据：存本地文件
        os.makedirs(os.path.join(BASE_DATASET_DIR, "system"), exist_ok=True)
        dataset_id = str(uuid.uuid4())[:8]
        dataset_dir = os.path.join(BASE_DATASET_DIR, "system", dataset_id)
        os.makedirs(dataset_dir, exist_ok=True)
        file_path = os.path.join(dataset_dir, file.filename)
        with open(file_path, "wb") as f:
            f.write(file_bytes)

    # 3. 统计元数据
    n_rows = len(df)
    n_columns = len(df.columns)
    numeric_columns = df.select_dtypes(include="number").columns.tolist()
    text_columns = df.select_dtypes(exclude="number").columns.tolist()
    missing_rate = float(df.isna().sum().sum()) / (n_rows * n_columns) if n_rows > 0 else 0
    target_candidates = [
        col for col in df.columns
        if any(k in col.lower() for k in ["strength", "elongation", "yield"])
    ]

    # 4. 写入数据库
    dataset = Dataset(
        name=file.filename.replace(".csv", ""),
        filename=file.filename,
        file_path=file_path,
        content=db_content,      # 数据库二进制字段
        source_type=source_type,
        n_rows=n_rows,
        n_columns=n_columns,
        numeric_columns=numeric_columns,
        text_columns=text_columns,
        target_candidates=target_candidates,
        missing_rate=missing_rate,
    )

    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset

# ✅ 补回缺失的 list_datasets
def list_datasets(db: Session):
    return db.query(Dataset).order_by(Dataset.created_at.desc()).all()

# ✅ 补回缺失的 get_dataset
def get_dataset(db: Session, dataset_id: int) -> Dataset:
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    return dataset

def load_dataset_preview(db: Session, dataset_id: int, limit: int = 50):
    dataset = get_dataset(db, dataset_id)

    # 优先从数据库二进制内容读取
    if dataset.content:
        df = pd.read_csv(io.BytesIO(dataset.content))
    elif dataset.file_path and os.path.exists(dataset.file_path):
        df = pd.read_csv(dataset.file_path)
    else:
        raise HTTPException(status_code=404, detail="Dataset data not found.")

    preview_df = df.head(limit)
    return {
        "columns": preview_df.columns.tolist(),
        "rows": preview_df.fillna("").values.tolist()
    }

def delete_dataset(db: Session, dataset_id: int):
    dataset = get_dataset(db, dataset_id)

    # 只有系统数据（有路径的）才删除物理文件
    if dataset.file_path:
        dataset_dir = os.path.dirname(dataset.file_path)
        if os.path.exists(dataset_dir):
            shutil.rmtree(dataset_dir)

    db.delete(dataset)
    db.commit()