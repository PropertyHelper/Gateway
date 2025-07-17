from sqlalchemy import create_engine

from src.settings import settings

# create an engine to connect to the database
engine = create_engine(settings.db_connection_string)
