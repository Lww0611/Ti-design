from pydantic import BaseModel
from typing import Optional

class RegisterRequest(BaseModel):
    username: str
    password: str
    lab: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str
