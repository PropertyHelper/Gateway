from sqlalchemy.orm import Session

from src.db_models import Recognition
from src.engine import engine


def record_recognition_event(event_type: str):
    with Session(engine) as session:
        recognition = Recognition(type=event_type)
        session.add(recognition)
        session.commit()
