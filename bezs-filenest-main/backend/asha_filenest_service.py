"""
Standalone ASHA Frontline Media & Health Education Service (Port 8080).
Part of bezs-filenest.
Provides low-bandwidth resumable audio uploads (asha-field-media) and localized health education assets.
"""

import os

# Default environment variables for local standalone execution
os.environ.setdefault("DATABASE_PRIMARY_URL", "postgresql+asyncpg://iam_user:iam_password@localhost:5433/iam_db")
os.environ.setdefault("STORAGE_BACKEND", "s3")
os.environ.setdefault("S3_ENDPOINT_URL", "http://localhost:9000")
os.environ.setdefault("S3_ACCESS_KEY_ID", "minioadmin")
os.environ.setdefault("S3_SECRET_ACCESS_KEY", "minioadmin_secure")
os.environ.setdefault("S3_BUCKET_NAME", "asha-field-media")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.routers.asha_media import router as asha_media_router

app = FastAPI(
    title="SevaFirst Frontline Media & Education Storage Service",
    description="Resumable chunked voice uploads, paper register archival, and localized health education audio.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(asha_media_router)


@app.get("/health")
def healthcheck():
    return {
        "status": "healthy",
        "service": "sevafirst-filenest",
        "storage_bucket": "asha-field-media",
        "supported_codecs": ["audio/opus", "audio/aac", "image/jpeg", "image/png"],
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
