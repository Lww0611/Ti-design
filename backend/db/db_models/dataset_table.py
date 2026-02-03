from sqlalchemy import Integer, String, Float, JSON, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base


class Dataset(Base):
    __tablename__ = "dataset"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    # 基本信息
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    filename: Mapped[str] = mapped_column(String(256), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)

    # 数据来源
    source_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False   # "system" | "user"
    )

    # 数据统计信息
    n_rows: Mapped[int] = mapped_column(Integer)
    n_columns: Mapped[int] = mapped_column(Integer)

    numeric_columns: Mapped[list] = mapped_column(JSON)
    text_columns: Mapped[list] = mapped_column(JSON)
    target_candidates: Mapped[list] = mapped_column(JSON)

    missing_rate: Mapped[float] = mapped_column(Float)

    created_at: Mapped[str] = mapped_column(
        DateTime,
        server_default=func.now()
    )
