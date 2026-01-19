from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, ForeignKey, String, JSON, Float

from db.base import Base


class PredictionResult(Base):
    __tablename__ = "prediction_result"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("task_table.id"), index=True
    )

    model_name: Mapped[str] = mapped_column(String(50))

    # 新增结构化指标
    strength: Mapped[float] = mapped_column(Float, nullable=True)
    elongation: Mapped[float] = mapped_column(Float, nullable=True)

    # 原始结果
    result_json: Mapped[dict] = mapped_column(JSON)
