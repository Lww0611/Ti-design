from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from schemas.request import PredictRequest, InverseRequest
from services.prediction.service import predict_with_registry
from services.inverse.service import inverse_with_registry
from db.db_models.task_table import TaskTable
from db.db_models.prediction_result import PredictionResult
from db.db_models.inverse_result import InverseResult

from typing import Optional


from db.session import get_db
from services.dataset_service import (
    save_uploaded_dataset,
    list_datasets,
    get_dataset,
    load_dataset_preview,
    delete_dataset
)

router = APIRouter()

# ===============================
# Prediction APIs
# ===============================

@router.post("/predict")
def predict_performance(data: PredictRequest):
    try:
        res = predict_with_registry(data.model_dump())
        return {
            "status": "success",
            "task_id": res["task_id"],
            "data": res["results"]
        }
    except Exception as e:
        print("Predict error:", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/inverse")
def inverse_design(data: InverseRequest):
    try:
        res = inverse_with_registry(data.model_dump())
        return {
            "status": "success",
            "task_id": res["task_id"],
            "data": res["results"]
        }
    except Exception as e:
        print("Inverse error:", e)
        raise HTTPException(status_code=500, detail=str(e))


# ===============================
# Dataset Management APIs
# ===============================

@router.get("/datasets")
def api_list_datasets(db: Session = Depends(get_db)):
    """
    返回：
    [
      {
        id, name, filename, source_type,
        n_rows, n_columns, missing_rate, created_at
      }
    ]
    """
    return list_datasets(db)


@router.post("/datasets/upload")
def api_upload_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    dataset = save_uploaded_dataset(db, file, source_type="user")

    return {
        "id": dataset.id,
        "name": dataset.name,
        "filename": dataset.filename,
        "source_type": dataset.source_type,
        "n_rows": dataset.n_rows,
        "n_columns": dataset.n_columns,
        "missing_rate": dataset.missing_rate,
        "created_at": dataset.created_at,
    }


@router.get("/datasets/{dataset_id}")
def api_get_dataset_detail(
    dataset_id: int,
    db: Session = Depends(get_db)
):
    return get_dataset(db, dataset_id)


@router.get("/datasets/{dataset_id}/preview")
def api_preview_dataset(
    dataset_id: int,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    return load_dataset_preview(db, dataset_id, limit)


@router.delete("/datasets/{dataset_id}")
def api_delete_dataset(
    dataset_id: int,
    db: Session = Depends(get_db)
):
    delete_dataset(db, dataset_id)
    return {"success": True}

# ===============================
# Task History APIs（分页 + 搜索 + 时间范围）
# ===============================
@router.get("/tasks")
def api_list_tasks(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1),
    keyword: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """
    返回任务列表，支持分页、搜索和日期筛选
    """
    query = db.query(TaskTable)

    # 搜索标题或 task_type
    if keyword:
        query = query.filter(TaskTable.title.ilike(f"%{keyword}%"))

    # 日期范围过滤
    if start_date:
        query = query.filter(TaskTable.created_at >= start_date)
    if end_date:
        query = query.filter(TaskTable.created_at <= end_date)

    # 总数
    total = query.count()

    # 按创建时间倒序 + 分页
    tasks = query.order_by(TaskTable.created_at.desc()) \
                 .offset((page - 1) * page_size) \
                 .limit(page_size) \
                 .all()

    return {
        "total": total,
        "items": [
            {
                "id": t.id,
                "task_type": t.task_type,
                "status": t.status,
                "title": t.title,
                "created_at": t.created_at,
            }
            for t in tasks
        ]
    }


# ===============================
# Prediction Results by Task
# ===============================
@router.get("/tasks/{task_id}/results")
def api_get_prediction_results(
    task_id: int,
    db: Session = Depends(get_db)
):
    results = db.query(PredictionResult).filter(PredictionResult.task_id == task_id).all()

    return [
        {
            "id": r.id,
            "model_name": r.model_name,
            "strength": r.strength,
            "elongation": r.elongation,
            "result_json": r.result_json,
        }
        for r in results
    ]


# ===============================
# Inverse Results by Task
# ===============================
@router.get("/tasks/{task_id}/inverse-results")
def api_get_inverse_results(
    task_id: int,
    db: Session = Depends(get_db)
):
    results = (
        db.query(InverseResult)
        .filter(InverseResult.task_id == task_id)
        .order_by(InverseResult.rank.asc())
        .all()
    )

    return [
        {
            "id": r.id,
            "rank": r.rank,
            "score": r.score,
            "predicted_strength": r.predicted_strength,
            "predicted_elongation": r.predicted_elongation,
            "elements": r.elements,
            "raw": r.raw,
            "created_at": r.created_at,
        }
        for r in results
    ]


# ===============================
# Delete Task (级联删除)
# ===============================
@router.delete("/tasks/{task_id}")
def api_delete_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    task = db.query(TaskTable).filter(TaskTable.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()
    return {"success": True}