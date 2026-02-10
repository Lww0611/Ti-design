# deps/auth.py
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from db.session import get_db
from db.db_models.user_table import User
from fastapi import Header

def get_current_user(token: str = Header(...), db: Session = Depends(get_db)) -> User:
    try:
        user_id, _ = token.split("-", 1)
    except:
        raise HTTPException(status_code=401, detail="无效 token")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user