from fastapi import APIRouter, HTTPException
from schemas.request import PredictRequest, InverseRequest
from services.prediction.service import predict_with_registry
from services.inverse.service import inverse_with_registry

router = APIRouter(tags=["Predictions"])

@router.post("/predict")
def predict_performance(data: PredictRequest):
    try:
        res = predict_with_registry(data.model_dump())
        return {"status": "success", "task_id": res["task_id"], "data": res["results"]}
    except Exception as e:
        print("Predict error:", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/inverse")
def inverse_design(data: InverseRequest):
    try:
        res = inverse_with_registry(data.model_dump())
        return {"status": "success", "task_id": res["task_id"], "data": res["results"]}
    except Exception as e:
        print("Inverse error:", e)
        raise HTTPException(status_code=500, detail=str(e))