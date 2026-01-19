from sqlalchemy import Integer, Float, ForeignKey, JSON, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base

class InverseResult(Base):
    __tablename__ = "inverse_result"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    task_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("task_table.id", ondelete="CASCADE"),
        index=True
    )

    rank: Mapped[int] = mapped_column(Integer)
    score: Mapped[float] = mapped_column(Float)

    predicted_strength: Mapped[float] = mapped_column(Float)
    predicted_elongation: Mapped[float] = mapped_column(Float)

    elements: Mapped[dict] = mapped_column(JSON)
    raw: Mapped[dict] = mapped_column(JSON)

    created_at: Mapped[str] = mapped_column(
        DateTime,
        server_default=func.now()
    )
