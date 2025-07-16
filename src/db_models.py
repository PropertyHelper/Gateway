import datetime

from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    ...

class Recognition(Base):
    __tablename__ = "recognitions"
    record_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    at: Mapped[datetime.datetime] = mapped_column(default=func.now())
    type: Mapped[str]
