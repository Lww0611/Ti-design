from pydantic import BaseModel
from typing import Optional

class CaseCreateRequest(BaseModel):
    case_name: str
    description: Optional[str]
    target: Optional[str]
    constraints: Optional[str]
    dataset_id: Optional[int]
    model_id: Optional[int]

class CaseUpdateRequest(BaseModel):
    case_name: Optional[str]
    description: Optional[str]
    target: Optional[str]
    constraints: Optional[str]
    dataset_id: Optional[int]
    model_id: Optional[int]

from pydantic import BaseModel
from typing import Optional

class CaseResponse(BaseModel):
    id: int
    case_name: str
    description: Optional[str]
    target: Optional[str]
    constraints: Optional[str]
    user_id: int
    dataset_id: Optional[int]
    model_id: Optional[int]
    current_step: int
    status: str
    created_at: str

    class Config:
        orm_mode = True