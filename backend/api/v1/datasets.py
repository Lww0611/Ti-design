from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from db.session import get_db
from services.dataset.dataset_service import (
    save_uploaded_dataset, list_datasets, get_dataset,
    load_dataset_preview, delete_dataset
)

router = APIRouter(prefix="/datasets", tags=["Datasets"])

@router.get("")
def api_list_datasets(db: Session = Depends(get_db)):
    return list_datasets(db)

@router.post("/upload")
def api_upload_dataset(file: UploadFile = File(...), db: Session = Depends(get_db)):
    dataset = save_uploaded_dataset(db, file, source_type="user")
    return {
        "id": dataset.id, "name": dataset.name, "filename": dataset.filename,
        "source_type": dataset.source_type, "n_rows": dataset.n_rows,
        "n_columns": dataset.n_columns, "missing_rate": dataset.missing_rate,
        "created_at": dataset.created_at,
    }

@router.get("/{dataset_id}")
def api_get_dataset_detail(dataset_id: int, db: Session = Depends(get_db)):
    return get_dataset(db, dataset_id)

@router.get("/{dataset_id}/preview")
def api_preview_dataset(dataset_id: int, limit: int = 50, db: Session = Depends(get_db)):
    return load_dataset_preview(db, dataset_id, limit)

@router.delete("/{dataset_id}")
def api_delete_dataset(dataset_id: int, db: Session = Depends(get_db)):
    delete_dataset(db, dataset_id)
    return {"success": True}