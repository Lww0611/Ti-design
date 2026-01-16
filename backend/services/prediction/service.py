# backend/services/prediction_service.py

from models.registry import ModelRegistry
from services.features.builder import build_features
import logging

logger = logging.getLogger(__name__)

def predict_with_registry(payload: dict):
    # 1. 构造特征
    features = build_features(payload)

    # 2. 获取选择的模型列表（比如前端传来 ["BERT-Regression"]）
    selected_models = payload.get("selectedModels", ["BERT-Regression"])

    results = []
    for name in selected_models:
        # 3. 从你的 Registry 获取实例
        model_instance = ModelRegistry.get_model(name)

        if model_instance:
            # 4. 调用实例的 predict 方法
            pred = model_instance.predict(features)
            results.append(pred)

    return results