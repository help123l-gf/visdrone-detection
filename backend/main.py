from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.config import settings
from app import config
from app.database import engine, SessionLocal, Base
from app.models import db_models  # noqa: ensure models loaded
from app.api.detection import router as detection_router
from app.api.auth import router as auth_router
from app.utils.file_utils import ensure_directories


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_directories()
    try:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            existing = db.execute(text("SELECT 1 FROM users WHERE username='admin'")).fetchone()
            if not existing:
                from app.utils.security import hash_password
                db.execute(
                    text("INSERT INTO users (username, email, password_hash, role) VALUES (:u, :e, :p, :r)"),
                    {"u": "admin", "e": "admin@visdrone.cn", "p": hash_password("admin123"), "r": "admin"},
                )
                db.commit()
                print("DB: tables created, admin user seeded")
        finally:
            db.close()
        config.db_available = True
    except Exception as e:
        print(f"WARNING: Database unavailable ({e}), auth/history features disabled")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="无人机视觉检测平台后端API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")

app.include_router(detection_router, prefix="/api")
app.include_router(auth_router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
