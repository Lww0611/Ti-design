from db.session import SessionLocal
from db.db_models.task_table import TaskTable
from db.db_models.prediction_result import PredictionResult
from db.db_models.composition import Composition
from models.registry import ModelRegistry
from services.features.builder import build_features
import logging

logger = logging.getLogger(__name__)

def predict_with_registry(payload: dict):
    """
    统一预测接口：
    - 创建 task
    - 保存 composition
    - 调用模型预测
    - 保存结果
    - 返回 task_id + results
    """
    db = SessionLocal()
    try:
        # 1️⃣ 创建任务
        task = TaskTable(
            task_type="forward",
            status="running",
            title="Forward Prediction",
            input_json=payload
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        # 2️⃣ 保存 composition
        comp_payload = payload.get("composition", {})
        if comp_payload:
            composition = Composition(task_id=task.id, **comp_payload)
            db.add(composition)
            db.commit()

        # 3️⃣ 构造特征
        features = build_features(payload)
        selected_models = payload.get("selectedModels", ["BERT-Regression"])

        results = []

        for name in selected_models:
            model_instance = ModelRegistry.get_model(name)
            if not model_instance:
                logger.warning(f"Model {name} not found")
                continue

            pred_raw = model_instance.predict(features)
            print(f"[DEBUG] model={name}, type(pred_raw)={type(pred_raw)}, pred_raw={pred_raw}")

            # 确保返回 dict
            if not isinstance(pred_raw, dict):
                pred_raw = {"strength": pred_raw, "elongation": None, "raw": {}}

            # 保存数据库
            result = PredictionResult(
                task_id=task.id,
                model_name=name,
                strength=pred_raw.get("strength"),
                elongation=pred_raw.get("elongation"),
                result_json=pred_raw
            )
            db.add(result)
            db.commit()

            # 返回给前端
            results.append({
                "model": name,
                "strength": pred_raw.get("strength"),
                "elongation": pred_raw.get("elongation"),
                "raw": pred_raw.get("raw")
            })



        # 4️⃣ 更新任务状态为 success
        task.status = "success"
        db.commit()

        return {"task_id": task.id, "results": results}

    except Exception as e:
        logger.exception("Prediction failed")
        if "task" in locals():
            task.status = "failed"
            db.commit()
        raise e
    finally:
        db.close()
