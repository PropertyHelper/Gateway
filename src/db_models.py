import datetime

from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.

    Provides common functionality and metadata for all database entities.
    """
    ...

class Recognition(Base):
    """
    Encapsulate data on recognition for durability.
    """
    __tablename__ = "recognitions"
    record_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    at: Mapped[datetime.datetime] = mapped_column(default=func.now())
    type: Mapped[str]
