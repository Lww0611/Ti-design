from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, DateTime, String, Text, ForeignKey

from db.base import Base

class Case(Base):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    case_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    target: Mapped[str | None] = mapped_column(Text, nullable=True)
    constraints: Mapped[str | None] = mapped_column(Text, nullable=True)

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"))

    dataset_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("dataset.id"), nullable=True)
    model_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("model.id"), nullable=True)

    current_step: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(50), default="initialized")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)