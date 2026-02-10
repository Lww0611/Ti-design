from datetime import datetime
from schemas.model import ModelMetadataV1


def register_model(
    user_id: str,
    request,
    model_file_bytes,
):
    metadata = ModelMetadataV1(
        model_name=request.model_name,
        description=request.description,
        task_type=request.task_type,
        target=request.target,
        features=request.features,
        framework=request.framework,
        model_format="pickle",
        created_by=user_id,
        created_at=datetime.utcnow()
    )

    return metadata
