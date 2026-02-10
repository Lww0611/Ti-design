from pydantic import BaseModel, Field
from typing import List, Literal
from datetime import datetime


class ModelMetadataV1(BaseModel):
    schema_version: Literal["1.0"] = "1.0"

    model_name: str = Field(..., description="User defined model name")
    description: str | None = None

    task_type: Literal["regression"]
    output_type: Literal["scalar"] = "scalar"

    target: str
    features: List[str]

    framework: Literal["sklearn", "xgboost", "torch"]
    model_format: Literal["pickle", "joblib", "pt"]

    capabilities: dict = {
        "predict": True,
        "evaluate": True
    }

    created_by: str
    created_at: datetime

class ModelRegisterRequest(BaseModel):
    model_name: str
    description: str | None = None

#     task_type: Literal["regression"]
    task_type: str = "regression"   # 默认值

    target: str
    features: List[str]

#     framework: Literal["sklearn", "xgboost", "torch"]
    framework: str = "xgboost"   # 默认值
