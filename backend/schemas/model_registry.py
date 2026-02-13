from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from datetime import datetime

# 这个保留，作为模型文件的“说明书”规范
class ModelMetadataV1(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    model_name: str
    description: Optional[str] = None
    task_type: Literal["regression"]
    target: str
    features: List[str]
    framework: Literal["sklearn", "xgboost", "torch"]
    model_format: Literal["pickle", "joblib", "pt"]
    created_by: str
    created_at: datetime

# 这个给 API 使用，增加 Config 允许转换
class ModelRegisterRequest(BaseModel):
    model_name: str
    description: Optional[str] = None
    target: str
    features: List[str]
    task_type: str = "regression"
    framework: str = "xgboost"

    class Config:
        from_attributes = True