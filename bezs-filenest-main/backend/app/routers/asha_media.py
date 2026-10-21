"""
API Router for ASHA Frontline Media Storage, Resumable Chunked Audio Ingestion,
Paper Register Archival with OCR Tags, and Localized Health Education Catalog.
"""

from typing import List, Optional
from fastapi import APIRouter, File, Form, HTTPException, Query, Request, UploadFile, status

from app.schemas.asha_media import (
    ChunkedUploadInitRequest,
    ChunkedUploadInitResponse,
    ChunkUploadResponse,
    ChunkedUploadCompleteRequest,
    ChunkedUploadCompleteResponse,
    HealthEducationCatalogResponse,
    RegisterPhotoUploadResponse,
    RegisterType,
)
from app.services.asha_media_service import AshaMediaService

router = APIRouter(tags=["ASHA Frontline Media"])


# ── 1. Resumable Chunked Audio Uploads ─────────────────────────────────────────

@router.post("/asha-media/upload/init", response_model=ChunkedUploadInitResponse, status_code=status.HTTP_201_CREATED)
async def init_chunked_upload(req: ChunkedUploadInitRequest) -> ChunkedUploadInitResponse:
    """
    Initiates a low-bandwidth resumable chunked upload for compressed .opus / .aac
    voice recordings captured during rural household visits.
    """
    try:
        return AshaMediaService.init_chunked_upload(req)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.put("/asha-media/upload/{session_id}/chunk/{chunk_index}", response_model=ChunkUploadResponse)
async def upload_audio_chunk(
    session_id: str,
    chunk_index: int,
    request: Request,
) -> ChunkUploadResponse:
    """
    Uploads a single chunk of compressed voice recording.
    Handles partial binary streams resilient to rural 2G/3G network drops.
    """
    try:
        chunk_data = await request.body()
        if not chunk_data:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Chunk body cannot be empty")
        return AshaMediaService.upload_chunk(session_id, chunk_index, chunk_data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/asha-media/upload/{session_id}/complete", response_model=ChunkedUploadCompleteResponse)
async def complete_chunked_upload(
    session_id: str,
    body: Optional[ChunkedUploadCompleteRequest] = None,
) -> ChunkedUploadCompleteResponse:
    """
    Assembles, verifies checksum, and commits the finalized audio asset
    into the `asha-field-media` bucket with clinical visit tags.
    """
    try:
        checksum = body.checksum_sha256 if body else None
        return AshaMediaService.complete_chunked_upload(session_id, checksum_sha256=checksum)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


# ── 2. Paper Register Snapshots with OCR Archival Tags ─────────────────────────

@router.post("/asha-media/registers/photo", response_model=RegisterPhotoUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_register_photo(
    file: UploadFile = File(...),
    register_type: RegisterType = Form(RegisterType.MCP_CARD),
    village_lgd_code: str = Form(...),
    worker_id: str = Form(...),
    patient_id: Optional[str] = Form(None),
    subcentre_id: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
) -> RegisterPhotoUploadResponse:
    """
    Uploads a photographed rural paper register (MCP card, Mamta card, immunization register)
    stamped with automatic searchable tags (`register:mcp_card`, `ocr:pending`, `village:{code}`)
    for downstream automated OCR archival and digitization.
    """
    contents = await file.read()
    return AshaMediaService.process_register_photo(
        filename=file.filename or "register_scan.jpg",
        content_type=file.content_type or "image/jpeg",
        size_bytes=len(contents),
        register_type=register_type.value,
        village_lgd_code=village_lgd_code,
        worker_id=worker_id,
        patient_id=patient_id,
        subcentre_id=subcentre_id,
        notes=notes,
    )


# ── 3. Pre-Cached Localized Health Education Clips ────────────────────────────

@router.get("/media/health-education", response_model=HealthEducationCatalogResponse)
async def get_health_education_catalog(
    language_code: Optional[str] = Query(None, description="ISO language code, e.g. hi, or, te, ta, mr, bn"),
    condition_code: Optional[str] = Query(None, description="Clinical SNOMED-CT or ICD-10 condition code"),
    target: Optional[str] = Query(None, description="Target demographic, e.g. pregnant_mothers, infant_caregivers"),
) -> HealthEducationCatalogResponse:
    """
    Serves pre-cached, localized audio/visual health education clips indexed by
    clinical condition code (SNOMED-CT / ICD-10) in Hindi, Odia, Tamil, Telugu, Marathi, Bengali.
    The mobile client syncs these clips for offline playback during household visits.
    """
    return AshaMediaService.get_health_education_catalog(
        language_code=language_code,
        condition_code=condition_code,
        target=target,
    )
