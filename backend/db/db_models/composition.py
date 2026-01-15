from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, Float, ForeignKey

from db.base import Base

class Composition(Base):
    __tablename__ = "composition"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("prediction_task.id"))

    Al: Mapped[float] = mapped_column(Float)
    Sn: Mapped[float] = mapped_column(Float)
    V: Mapped[float] = mapped_column(Float)
    Zr: Mapped[float] = mapped_column(Float)
    Mo: Mapped[float] = mapped_column(Float)
    Cr: Mapped[float] = mapped_column(Float)
    Nb: Mapped[float] = mapped_column(Float)
    Ta: Mapped[float] = mapped_column(Float)
    Fe: Mapped[float] = mapped_column(Float)
    Si: Mapped[float] = mapped_column(Float)
    O: Mapped[float] = mapped_column(Float)
    C: Mapped[float] = mapped_column(Float)
    N: Mapped[float] = mapped_column(Float)
