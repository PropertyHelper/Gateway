from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.user_service_route import router as user_router
from src.face_recognition_route import  router as face_recognition_router

def build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(user_router, tags=["User"])
    app.include_router(face_recognition_router, tags=["Cashier"])
    app.add_middleware(CORSMiddleware,
                       allow_origins=["*"])
    return app
