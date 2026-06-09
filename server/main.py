from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from routers.answers import router as answers_router
from routers.auth import router as auth_router
from routers.questions import router as questions_router
from routers.research import router as research_router
from routers.report import router as report_router
from routers.users import router as users_router

app = FastAPI(title="AI炼金 API", version="0.1.0")

origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(questions_router)
app.include_router(research_router)
app.include_router(answers_router)
app.include_router(report_router)
app.include_router(auth_router)
app.include_router(users_router)

upload_root = Path(settings.upload_dir)
upload_root.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_root)), name="uploads")


@app.get("/api/v1/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
