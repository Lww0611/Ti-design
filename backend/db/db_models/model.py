from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, DateTime, JSON, ForeignKey,UniqueConstraint
from db.base import Base

class Model(Base):
    __tablename__ = "model"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_file_path: Mapped[str] = mapped_column(String(200), nullable=False)
    features: Mapped[list] = mapped_column(JSON, nullable=False)  # 保存特征列
    target: Mapped[str] = mapped_column(String(50), nullable=False)
    task_type: Mapped[str] = mapped_column(String(50), default="regression")  # 回归/分类/逆向设计
    description: Mapped[str] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="uploaded")  # uploaded / evaluated / failed
    metrics: Mapped[dict] = mapped_column(JSON, nullable=True)  # 保存评估结果
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        # 保证同一个用户不能上传同名模型
        UniqueConstraint('user_id', 'model_name', name='uq_user_model_name'),
    )
