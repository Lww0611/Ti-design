from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, DateTime, JSON, String

from db.base import Base

class PredictionTask(Base):
    __tablename__ = "prediction_task"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    mode: Mapped[str] = mapped_column(String(20))
    input_json: Mapped[dict] = mapped_column(JSON)
