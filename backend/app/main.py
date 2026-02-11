from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_ai import router as ai_router
from app.api.routes_assets import router as assets_router
from app.api.routes_feed import router as feed_router
from app.api.routes_health import router as health_router
from app.api.routes_knowledge import router as knowledge_router
from app.api.routes_settings import router as settings_router
from app.api.routes_tasks import router as tasks_router
from app.core.config import settings

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(ai_router)
app.include_router(assets_router)
app.include_router(tasks_router)
app.include_router(feed_router)
app.include_router(knowledge_router)
app.include_router(settings_router)


@app.get("/")
def root() -> dict[str, str]:
    return {"service": settings.app_name, "status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.app_host, port=settings.app_port)
