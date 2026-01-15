from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "mysql+pymysql://root:742590380025@localhost:3306/ti_alloy_ai"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=True   # 开发阶段建议打开
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

from sqlalchemy.orm import Session

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
