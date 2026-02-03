import os
import shutil
import uuid
import pandas as pd
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from db.dataset_models import Dataset

BASE_DATASET_DIR = "backend/data/datasets"


def _ensure_dirs():
    os.makedirs(os.path.join(BASE_DATASET_DIR, "system"), exist_ok=True)
    os.makedirs(os.path.join(BASE_DATASET_DIR, "user"), exist_ok=True)


def save_uploaded_dataset(
    db: Session,
    file: UploadFile,
    source_type: str = "user"
) -> Dataset:
    """
    保存上传的 CSV 数据集并解析元数据
    """

    _ensure_dirs()

    # ---------- 1. 校验文件 ----------
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")

    dataset_id = str(uuid.uuid4())[:8]
    dataset_dir = os.path.join(BASE_DATASET_DIR, source_type, dataset_id)
    os.makedirs(dataset_dir, exist_ok=True)

    file_path = os.path.join(dataset_dir, file.filename)

    # ---------- 2. 保存文件 ----------
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # ---------- 3. 解析 CSV ----------
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"CSV parse failed: {e}")

    if df.empty:
        raise HTTPException(status_code=400, detail="CSV file is empty.")

    # ---------- 4. 自动统计 ----------
    n_rows = len(df)
    n_columns = len(df.columns)

    numeric_columns = df.select_dtypes(include="number").columns.tolist()
    text_columns = df.select_dtypes(exclude="number").columns.tolist()

    missing_rate = float(df.isna().sum().sum()) / (n_rows * n_columns)

    target_candidates = [
        col for col in df.columns
        if any(k in col.lower() for k in ["strength", "elongation", "yield"])
    ]

    # ---------- 5. 写入数据库 ----------
    dataset = Dataset(
        name=file.filename.replace(".csv", ""),
        filename=file.filename,
        file_path=file_path,
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


def list_datasets(db: Session):
    return db.query(Dataset).order_by(Dataset.created_at.desc()).all()


def get_dataset(db: Session, dataset_id: int) -> Dataset:
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    return dataset


def load_dataset_preview(db: Session, dataset_id: int, limit: int = 50):
    dataset = get_dataset(db, dataset_id)

    df = pd.read_csv(dataset.file_path)
    preview_df = df.head(limit)

    return {
        "columns": preview_df.columns.tolist(),
        "rows": preview_df.fillna("").values.tolist()
    }


def delete_dataset(db: Session, dataset_id: int):
    dataset = get_dataset(db, dataset_id)

    # 删除文件目录
    dataset_dir = os.path.dirname(dataset.file_path)
    if os.path.exists(dataset_dir):
        shutil.rmtree(dataset_dir)

    db.delete(dataset)
    db.commit()
