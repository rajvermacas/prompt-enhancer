from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes import pages, workspaces, news, prompts, workflows

app = FastAPI(title="Prompt Enhancer", version="0.1.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(pages.router)
app.include_router(workspaces.router, prefix="/api")
app.include_router(news.router, prefix="/api")
app.include_router(prompts.router, prefix="/api")
app.include_router(workflows.router, prefix="/api")


@app.get("/health")
def health_check():
    return {"status": "healthy"}
