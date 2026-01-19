from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, DateTime, JSON, String

from db.base import Base


class TaskTable(Base):
    __tablename__ = "task_table"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    # 新增字段
    task_type: Mapped[str] = mapped_column(String(20), index=True)
    status: Mapped[str] = mapped_column(String(20), index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=True)

    # 原始输入
    input_json: Mapped[dict] = mapped_column(JSON)
