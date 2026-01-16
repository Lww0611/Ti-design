from fastapi import APIRouter, HTTPException
from schemas.request import PredictRequest, InverseRequest

# --- 修改引用路径 ---
from services.prediction.service import predict_with_registry
from services.inverse.service import mock_inverse_design
from fastapi import Depends
from sqlalchemy.orm import Session
from db.session import get_db
from db.db_models.prediction_task import PredictionTask
from db.db_models.prediction_result import PredictionResult


router = APIRouter()

@router.post("/predict")
def predict_performance(
    data: PredictRequest,
    db: Session = Depends(get_db)
):
    try:
        results = predict_with_registry(data.model_dump())

        # 1. 保存 task
        task = PredictionTask(
            mode=data.heatTreatmentMode,
            input_json=data.model_dump()
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        # 2. 保存 result
        for r in results:
            res = PredictionResult(
                task_id=task.id,
                model_name=r["model"],
                result_json=r
            )
            db.add(res)
        db.commit()

        # ✅ 正确返回
        return {
            "status": "success",
            "task_id": task.id,
            "data": results
        }

    except Exception as e:
        print("Predict error:", e)
        return {
            "status": "error",
            "message": str(e),
            "data": []
        }



@router.post("/inverse")
async def inverse_design(data: InverseRequest):
    """
    逆向设计接口
    """
    try:
        results = mock_inverse_design(data)
        return {
            "status": "success",
            "data": results
        }
    except Exception as e:
        print(f"Error in inverse: {e}")
        return {
            "status": "error",
            "message": str(e),
            "data": []
        }

