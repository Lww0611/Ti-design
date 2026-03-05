from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, DateTime, JSON, String, ForeignKey

from db.base import Base


class TaskTable(Base):
    __tablename__ = "task_table"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )

    task_type: Mapped[str] = mapped_column(String(20), index=True)
    status: Mapped[str] = mapped_column(String(20), index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=True)

    input_json: Mapped[dict] = mapped_column(JSON)

    # ✅ 新增：科研流程绑定
    case_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("cases.id"),
        nullable=True,
        index=True
    )