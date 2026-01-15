import random

# 定义支持的模型列表
SUPPORTED_MODELS = {
    "structured": ["XGBoost", "RandomForest", "SVM"],
    "text": ["BERT-Regression", "LLM-Parser", "TextCNN"]
}

def predict_with_xgboost(elements, hot_working, heat_treatment):
    """模拟 XGBoost 预测逻辑 (数值模式)"""
    base_rm = elements.get('Al', 0) * 50 + elements.get('V', 0) * 30 + 600

    ht_factor = 0
    if heat_treatment and heat_treatment.enabled:
        for stage in heat_treatment.stages:
            if stage.temperature > 800:
                ht_factor -= 50
            else:
                ht_factor += 20

    rm = base_rm + ht_factor + random.uniform(-20, 20)
    a = 20 - (rm / 100) + random.uniform(-1, 1)

    return {
        "model": "XGBoost",
        "rm": round(rm, 2),
        "rm_err": 15.0,
        "a": round(max(a, 0), 2),
        "a_err": 1.5
    }

def predict_with_random_forest(elements, hot_working, heat_treatment):
    """模拟 Random Forest 预测逻辑"""
    res = predict_with_xgboost(elements, hot_working, heat_treatment)
    res["model"] = "RandomForest"
    res["rm"] += random.uniform(-30, 30)
    res["a"] += random.uniform(-2, 2)
    return res

def predict_with_bert(elements, hot_working, text_input):
    """模拟 BERT 预测逻辑 (文本模式)"""
    text_len = len(text_input) if text_input else 0
    rm = 900 + (text_len % 100)
    a = 12.0

    return {
        "model": "BERT-Regression",
        "rm": round(rm, 2),
        "rm_err": 20.0,
        "a": round(a, 2),
        "a_err": 2.0
    }

def multi_model_predict(data):
    """
    多模型协同预测入口
    """
    results = []

    if hasattr(data, 'selectedModels'):
        selected_models = data.selectedModels
        mode = data.heatTreatmentMode
        elements = data.elements
        hot_working = data.hotWorking
        heat_treatment = data.heatTreatment
        text_input = data.heatTreatmentText
    else:
        selected_models = data.get("selectedModels", [])
        mode = data.get("heatTreatmentMode", "structured")
        elements = data.get("elements", {})
        hot_working = data.get("hotWorking", {})
        heat_treatment = data.get("heatTreatment", {})
        text_input = data.get("heatTreatmentText", "")

    if not selected_models:
        selected_models = ["XGBoost"] if mode == "structured" else ["BERT-Regression"]

    for model_name in selected_models:
        prediction = {}

        if mode == 'structured':
            if model_name == "XGBoost":
                prediction = predict_with_xgboost(elements, hot_working, heat_treatment)
            elif model_name == "RandomForest":
                prediction = predict_with_random_forest(elements, hot_working, heat_treatment)
            else:
                prediction = predict_with_xgboost(elements, hot_working, heat_treatment)
                prediction["model"] = model_name

        elif mode == 'text':
            if model_name == "BERT-Regression":
                prediction = predict_with_bert(elements, hot_working, text_input)
            else:
                prediction = predict_with_bert(elements, hot_working, text_input)
                prediction["model"] = model_name

        if prediction:
            results.append(prediction)

    return results

from sqlalchemy.orm import Session
from db.db_models.prediction_task import PredictionTask
from db.db_models.prediction_result import PredictionResult

def predict_and_log(req, db: Session):

    # 1. 原样调用你现有预测
    results = multi_model_predict(req)

    # 2. 保存任务快照
    task = PredictionTask(
        mode=req.heatTreatmentMode,
        input_json=req.dict()
    )
    db.add(task)
    db.flush()

    # 3. 保存结果快照
    for r in results:
        rec = PredictionResult(
            task_id=task.id,
            model_name=r["model"],
            result_json=r
        )
        db.add(rec)

    db.commit()

    return {
        "task_id": task.id,
        "results": results
    }
