# services/model_service/registrar.py

from models.registry import ModelRegistry
from services.model_service.evaluator import evaluate_model_on_csv
from db.models import ModelRecord


def register_model(
    db,
    model_name: str,
    dataset,
    target_col: str
):
    """
    注册模型 + 评估
    """

    model = ModelRegistry.get_model(model_name)
    if model is None:
        raise ValueError(f"Model {model_name} not found")

    r2 = evaluate_model_on_csv(
        model=model,
        csv_path=dataset.file_path,
        target_col=target_col
    )

    record = ModelRecord(
        model_name=model_name,
        dataset_id=dataset.id,
        r2_score=r2
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record
