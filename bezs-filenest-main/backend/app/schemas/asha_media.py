"""
Schemas for ASHA Frontline Multimodal Media, Chunked Audio Ingestion,
Paper Register OCR Archival, and Localized Health Education Catalog.
"""

from enum import StrEnum
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AudioCodec(StrEnum):
    OPUS = "opus"
    AAC = "aac"
    OGG = "ogg"
    M4A = "m4a"
    WAV = "wav"


class RegisterType(StrEnum):
    MCP_CARD = "register:mcp_card"  # Mother and Child Protection Card
    IMMUNIZATION = "register:immunization"  # Village Immunization Register
    RCH = "register:rch_register"  # Reproductive and Child Health Register
    ASHA_DIARY = "register:asha_diary"  # Daily field activity logbook
    CBAC_PAPER = "register:cbac_paper"  # Hand-filled CBAC NCD screening forms


class OcrStatus(StrEnum):
    PENDING = "ocr:pending"
    PROCESSING = "ocr:processing"
    EXTRACTED = "ocr:extracted"
    FAILED = "ocr:failed"


class ChunkedUploadInitRequest(BaseModel):
    filename: str = Field(..., description="Audio file name, e.g. visit_20261022_01.opus")
    content_type: str = Field(default="audio/opus", description="MIME type, e.g. audio/opus, audio/aac")
    total_size_bytes: int = Field(..., ge=1, description="Total expected size in bytes")
    chunk_size_bytes: int = Field(default=262144, ge=65536, description="Chunk size in bytes (default 256KB for 2G/3G resilience)")
    total_chunks: int = Field(..., ge=1, description="Total number of chunks to assemble")
    audio_codec: AudioCodec = Field(default=AudioCodec.OPUS)
    duration_seconds: Optional[float] = Field(default=None, description="Recording duration in seconds")
    visit_uuid: str = Field(..., description="Field visit idempotency UUID")
    patient_id: str = Field(..., description="Target patient ID")
    worker_id: str = Field(..., description="ASHA / ANM worker ID")
    village_lgd_code: str = Field(..., description="Local Government Directory village code")
    language_code: str = Field(default="hi", description="Spoken dialect/language code, e.g. hi, or, te, ta, mr, bn")


class ChunkedUploadInitResponse(BaseModel):
    session_id: str
    upload_url: str
    chunk_size_bytes: int
    total_chunks: int
    expires_at: str


class ChunkUploadResponse(BaseModel):
    session_id: str
    chunk_index: int
    bytes_received: int
    received_chunks: List[int]
    is_complete: bool


class ChunkedUploadCompleteRequest(BaseModel):
    session_id: str
    checksum_sha256: Optional[str] = None


class ChunkedUploadCompleteResponse(BaseModel):
    file_id: str
    filename: str
    storage_key: str
    size_bytes: int
    content_type: str
    category: str = "audio"
    tags: List[str]
    status: str
    metadata: Dict[str, str]


class RegisterPhotoUploadResponse(BaseModel):
    file_id: str
    filename: str
    storage_key: str
    size_bytes: int
    tags: List[str]
    ocr_status: str
    ocr_job_id: str
    village_lgd_code: str


class HealthEducationClip(BaseModel):
    clip_id: str
    title: str
    description: str
    condition_code: str  # SNOMED-CT or ICD-10 code
    condition_coding_system: str  # "SNOMED-CT" | "ICD-10"
    condition_name: str
    language_code: str  # "hi" | "or" | "te" | "ta" | "mr" | "bn" | "en"
    media_type: str = "audio"  # "audio" | "video"
    download_url: str
    file_size_bytes: int
    duration_seconds: int
    checksum_sha256: str
    recommended_target: str  # e.g. "pregnant_mothers", "infant_caregivers", "adults_30_plus"


class HealthEducationCatalogResponse(BaseModel):
    total: int
    supported_languages: List[str]
    clips: List[HealthEducationClip]
    sync_timestamp: str
