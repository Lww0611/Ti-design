from pydantic import BaseModel
from typing import Optional

class RegisterRequest(BaseModel):
    username: str
    password: str
    lab: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    lab: Optional[str]

    class Config:
        from_attributes = True # 允许从 SQLAlchemy 模型直接转化