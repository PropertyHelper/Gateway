from pydantic_settings import BaseSettings
from pydantic import HttpUrl


class Settings(BaseSettings):
    secret: str
    user_endpoint: HttpUrl
    face_recognition_endpoint: HttpUrl

settings = Settings()
