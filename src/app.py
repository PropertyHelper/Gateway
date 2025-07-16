from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from src.db_models import Base
from src.engine import engine
from src.user_service_route import router as user_router
from src.face_recognition_route import  router as face_recognition_router
from src.cashier_router import router as cashier_router
from src.shop_router import router as shop_router


def build_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """
        Application lifespan manager for startup/shutdown events.

        Startup: Initializes database schema
        """
        Base.metadata.create_all(engine)
        yield
    app = FastAPI(lifespan=lifespan)
    app.include_router(user_router, tags=["User"])
    app.include_router(face_recognition_router, tags=["Cashier"])
    app.include_router(cashier_router, tags=["Cashier"])
    app.include_router(shop_router, tags=["Shop"])
    app.add_middleware(CORSMiddleware,
                       allow_origins=["*"],
                       allow_methods=["*"],
                       allow_headers=["*"],
                       )
    Instrumentator(excluded_handlers=["/metrics"]).instrument(app).expose(app)
    return app
