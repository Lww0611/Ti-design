from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, DateTime, JSON, ForeignKey, UniqueConstraint, LargeBinary
from db.base import Base

class Model(Base):
    __tablename__ = "model"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # ❌ 错误写法：ForeignKey("user_table.id")
    # ✅ 正确写法：改为 "user.id"，因为你的 SQL 日志显示表名是 user
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)

    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[bytes] = mapped_column(LargeBinary, nullable=True)
    model_file_path: Mapped[str] = mapped_column(String(200), nullable=True)
    features: Mapped[list] = mapped_column(JSON, nullable=False)
    target: Mapped[str] = mapped_column(String(50), nullable=False)
    task_type: Mapped[str] = mapped_column(String(50), default="regression")
    description: Mapped[str] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="uploaded")
    metrics: Mapped[dict] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint('user_id', 'model_name', name='uq_user_model_name'),
    )