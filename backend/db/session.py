import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Render / 生产环境请通过环境变量注入数据库连接串
# 例如：mysql+pymysql://user:password@host:3306/dbname
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:root@127.0.0.1:3306/ti_alloy_ai",
)

# SQL 日志默认关闭，调试时可设 DB_ECHO=true
DB_ECHO = os.getenv("DB_ECHO", "false").lower() in {"1", "true", "yes", "on"}

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    echo=DB_ECHO,
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
