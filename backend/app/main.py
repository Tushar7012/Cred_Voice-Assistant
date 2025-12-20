import os
from fastapi import FastAPI

os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from app.api.voice import router as voice_router
from app.memory.memory_store import init_db

app = FastAPI(title="Voice Welfare Agent")

app.include_router(
    voice_router,
    prefix="/voice",
    tags=["Voice Agent"]
)

@app.get("/health")
def health():
    return {"status": "ok"}


@app.on_event("startup")
def startup_event():
    init_db()
