from sqlalchemy import create_engine

from src.settings import settings

engine = create_engine(settings.db_connection_string)
