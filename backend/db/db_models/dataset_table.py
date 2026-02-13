from sqlalchemy import Integer, String, Float, JSON, DateTime, func, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base

class Dataset(Base):
    __tablename__ = "dataset"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    filename: Mapped[str] = mapped_column(String(256), nullable=False)

    # 修改：file_path 对于用户上传的数据现在可以为 null
    file_path: Mapped[str] = mapped_column(String(512), nullable=True)

    # ✅ 新增：用于存储二进制文件内容
    content: Mapped[bytes] = mapped_column(LargeBinary, nullable=True)

    source_type: Mapped[str] = mapped_column(String(32), nullable=False) # "system" | "user"
    n_rows: Mapped[int] = mapped_column(Integer)
    n_columns: Mapped[int] = mapped_column(Integer)
    numeric_columns: Mapped[list] = mapped_column(JSON)
    text_columns: Mapped[list] = mapped_column(JSON)
    target_candidates: Mapped[list] = mapped_column(JSON)
    missing_rate: Mapped[float] = mapped_column(Float)
    created_at: Mapped[str] = mapped_column(DateTime, server_default=func.now())