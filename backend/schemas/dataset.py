from pydantic import BaseModel
from datetime import datetime
from typing import List

class DatasetOut(BaseModel):
    id: int
    name: str
    filename: str
    file_path: str
    source_type: str
    n_rows: int
    n_columns: int
    numeric_columns: List[str]
    text_columns: List[str]
    target_candidates: List[str]
    missing_rate: float
    created_at: datetime

    class Config:
        from_attributes = True # 保持你的原始配置