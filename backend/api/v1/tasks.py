from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from db.session import get_db
from db.db_models.task_table import TaskTable
from db.db_models.prediction_result import PredictionResult
from db.db_models.inverse_result import InverseResult

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.get("")
def api_list_tasks(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1),
    keyword: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    query = db.query(TaskTable)
    if keyword:
        query = query.filter(TaskTable.title.ilike(f"%{keyword}%"))
    if start_date:
        query = query.filter(TaskTable.created_at >= start_date)
    if end_date:
        query = query.filter(TaskTable.created_at <= end_date)

    total = query.count()
    tasks = query.order_by(TaskTable.created_at.desc()) \
                 .offset((page - 1) * page_size) \
                 .limit(page_size).all()

    return {
        "total": total,
        "items": [{"id": t.id, "task_type": t.task_type, "status": t.status,
                   "title": t.title, "created_at": t.created_at} for t in tasks]
    }

@router.get("/{task_id}/results")
def api_get_prediction_results(task_id: int, db: Session = Depends(get_db)):
    results = db.query(PredictionResult).filter(PredictionResult.task_id == task_id).all()
    return [{"id": r.id, "model_name": r.model_name, "strength": r.strength,
             "elongation": r.elongation, "result_json": r.result_json} for r in results]

@router.get("/{task_id}/inverse-results")
def api_get_inverse_results(task_id: int, db: Session = Depends(get_db)):
    results = db.query(InverseResult).filter(InverseResult.task_id == task_id).order_by(InverseResult.rank.asc()).all()
    return [{"id": r.id, "rank": r.rank, "score": r.score, "predicted_strength": r.predicted_strength,
             "predicted_elongation": r.predicted_elongation, "elements": r.elements, "raw": r.raw, "created_at": r.created_at} for r in results]

@router.delete("/{task_id}")
def api_delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(TaskTable).filter(TaskTable.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return {"success": True}