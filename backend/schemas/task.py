from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional, Any

class TaskItem(BaseModel):
    id: int
    task_type: Optional[str]
    status: str
    title: Optional[str]
    created_at: datetime

class PredictionResultItem(BaseModel):
    id: int
    model_name: str
    strength: float
    elongation: float
    result_json: Optional[Any]

class InverseResultItem(BaseModel):
    id: int
    rank: int
    score: float
    predicted_strength: float
    predicted_elongation: float
    elements: Any
    raw: Any
    created_at: datetime