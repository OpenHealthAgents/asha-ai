"""
Service layer for ASHA Frontline Media, Chunked Audio Assembly,
Register OCR Archival Tagging, and Localized Health Education Catalog.
"""

from datetime import datetime, timezone, timedelta
import hashlib
import io
import json
from typing import Dict, List, Optional
import uuid

from app.core.config import settings
from app.schemas.asha_media import (
    ChunkedUploadInitRequest,
    ChunkedUploadInitResponse,
    ChunkUploadResponse,
    ChunkedUploadCompleteResponse,
    HealthEducationClip,
    HealthEducationCatalogResponse,
    RegisterPhotoUploadResponse,
    RegisterType,
    OcrStatus,
)

# In-memory session tracking for chunked uploads
_ACTIVE_CHUNK_SESSIONS: Dict[str, dict] = {}
_CHUNK_STORE: Dict[str, Dict[int, bytes]] = {}

# Pre-cached Localized Health Education Catalog
LOCALIZED_HEALTH_EDUCATION_CLIPS: List[HealthEducationClip] = [
    # 1. Antenatal Care - Pre-eclampsia & Danger Signs (ICD-10: O14.1, SNOMED: 398254007)
    HealthEducationClip(
        clip_id="he-anc-preeclampsia-hi",
        title="गर्भावस्था में उच्च रक्तचाप और खतरे के संकेत",
        description="पहचानें सिरदर्द, आंखों में धुंधलापन और सूजन के खतरे को (Hindi)",
        condition_code="398254007",
        condition_coding_system="SNOMED-CT",
        condition_name="Pre-eclampsia in Pregnancy",
        language_code="hi",
        media_type="audio",
        download_url="/static/health-education/hi/anc_preeclampsia.opus",
        file_size_bytes=342150,
        duration_seconds=95,
        checksum_sha256="a1b2c3d4e5f67890abcdef1234567890abcdef1234567890abcdef1234567890",
        recommended_target="pregnant_mothers",
    ),
    HealthEducationClip(
        clip_id="he-anc-preeclampsia-or",
        title="ଗର୍ଭାବସ୍ଥାରେ ଉଚ୍ଚ ରକ୍ତଚାପ ଏବଂ ବିପଦ ସଙ୍କେତ",
        description="ମୁଣ୍ଡବିନ୍ଧା, ଆଖି ଝାପସା ଏବଂ ଗୋଡ଼ ଫୁଲିବାର ଚେତାବନୀ (Odia)",
        condition_code="398254007",
        condition_coding_system="SNOMED-CT",
        condition_name="Pre-eclampsia in Pregnancy",
        language_code="or",
        media_type="audio",
        download_url="/static/health-education/or/anc_preeclampsia.opus",
        file_size_bytes=328400,
        duration_seconds=92,
        checksum_sha256="b2c3d4e5f6a17890abcdef1234567890abcdef1234567890abcdef1234567890",
        recommended_target="pregnant_mothers",
    ),
    HealthEducationClip(
        clip_id="he-anc-preeclampsia-ta",
        title="கர்ப்ப காலத்தில் உயர் இரத்த அழுத்தம் மற்றும் எச்சரிக்கை அறிகுறிகள்",
        description="தலைவலி, பார்வை மங்குதல் மற்றும் பாத வீக்கம் பற்றிய விழிப்புணர்வு (Tamil)",
        condition_code="398254007",
        condition_coding_system="SNOMED-CT",
        condition_name="Pre-eclampsia in Pregnancy",
        language_code="ta",
        media_type="audio",
        download_url="/static/health-education/ta/anc_preeclampsia.opus",
        file_size_bytes=351200,
        duration_seconds=98,
        checksum_sha256="c3d4e5f6a1b27890abcdef1234567890abcdef1234567890abcdef1234567890",
        recommended_target="pregnant_mothers",
    ),
    HealthEducationClip(
        clip_id="he-anc-preeclampsia-te",
        title="గర్భధారణ సమయంలో అధిక రక్తపోటు మరియు ప్రమాద సంకేతాలు",
        description="తీవ్రమైన తలనొప్పి, కంటి చూపు మందగించడం మరియు కాళ్ళ వాపుల నివారణ (Telugu)",
        condition_code="398254007",
        condition_coding_system="SNOMED-CT",
        condition_name="Pre-eclampsia in Pregnancy",
        language_code="te",
        media_type="audio",
        download_url="/static/health-education/te/anc_preeclampsia.opus",
        file_size_bytes=346500,
        duration_seconds=94,
        checksum_sha256="d4e5f6a1b2c37890abcdef1234567890abcdef1234567890abcdef1234567890",
        recommended_target="pregnant_mothers",
    ),

    # 2. Maternal Anemia & IFA Supplementation (ICD-10: O99.0, SNOMED: 761000119102)
    HealthEducationClip(
        clip_id="he-anc-anemia-hi",
        title="गर्भावस्था में खून की कमी (एनीमिया) और आयरन की गोलियां",
        description="रोजाना 1 लाल आयरन गोली और पौष्टिक आहार का महत्व (Hindi)",
        condition_code="O99.0",
        condition_coding_system="ICD-10",
        condition_name="Anemia in Pregnancy",
        language_code="hi",
        media_type="audio",
        download_url="/static/health-education/hi/anc_anemia.opus",
        file_size_bytes=312000,
        duration_seconds=88,
        checksum_sha256="e5f6a1b2c3d47890abcdef1234567890abcdef1234567890abcdef1234567890",
        recommended_target="pregnant_mothers",
    ),
    HealthEducationClip(
        clip_id="he-anc-anemia-bn",
        title="গর্ভাবস্থায় রক্তস্বল্পতা (অ্যানিমিয়া) এবং আয়রন ট্যাবলেট",
        description="প্রতিদিন আয়রন ট্যাবলেট এবং পুষ্টিকর খাবারের গুরুত্ব (Bengali)",
        condition_code="O99.0",
        condition_coding_system="ICD-10",
        condition_name="Anemia in Pregnancy",
        language_code="bn",
        media_type="audio",
        download_url="/static/health-education/bn/anc_anemia.opus",
        file_size_bytes=324000,
        duration_seconds=90,
        checksum_sha256="f6a1b2c3d4e57890abcdef1234567890abcdef1234567890abcdef1234567890",
        recommended_target="pregnant_mothers",
    ),
    HealthEducationClip(
        clip_id="he-anc-anemia-mr",
        title="गरोदरपणातील रक्तक्षय (ॲनिमिया) आणि लोहाच्या गोळ्या",
        description="दररोज एक आयर्न गोळी आणि सकस आहाराचे फायदे (Marathi)",
        condition_code="O99.0",
        condition_coding_system="ICD-10",
        condition_name="Anemia in Pregnancy",
        language_code="mr",
        media_type="audio",
        download_url="/static/health-education/mr/anc_anemia.opus",
        file_size_bytes=319000,
        duration_seconds=89,
        checksum_sha256="a2b3c4d5e6f77890abcdef1234567890abcdef1234567890abcdef1234567890",
        recommended_target="pregnant_mothers",
    ),

    # 3. IMNCI Pediatric Pneumonia & Chest Indrawing (ICD-10: J18.9, SNOMED: 233604007)
    HealthEducationClip(
        clip_id="he-ped-pneumonia-hi",
        title="बच्चों में निमोनिया और पसली चलने के लक्षण",
        description="तेज सांस और छाती धंसने पर तुरंत अस्पताल ले जाने की सलाह (Hindi)",
        condition_code="233604007",
        condition_coding_system="SNOMED-CT",
        condition_name="Pediatric Pneumonia",
        language_code="hi",
        media_type="audio",
        download_url="/static/health-education/hi/ped_pneumonia.opus",
        file_size_bytes=378000,
        duration_seconds=105,
        checksum_sha256="b3c4d5e6f7a27890abcdef1234567890abcdef1234567890abcdef1234567890",
        recommended_target="infant_caregivers",
    ),
    HealthEducationClip(
        clip_id="he-ped-pneumonia-or",
        title="ଶିଶୁର ନିମୋନିଆ ଏବଂ ଛାତି ଧସିବାର ଲକ୍ଷଣ",
        description="ଦ୍ରୁତ ଶ୍ୱାସକ୍ରିୟା ଏବଂ ବିପଦ ସମୟରେ ତୁରନ୍ତ ଡାକ୍ତରଖାନା ଯିବା (Odia)",
        condition_code="233604007",
        condition_coding_system="SNOMED-CT",
        condition_name="Pediatric Pneumonia",
        language_code="or",
        media_type="audio",
        download_url="/static/health-education/or/ped_pneumonia.opus",
        file_size_bytes=365000,
        duration_seconds=102,
        checksum_sha256="c4d5e6f7a2b37890abcdef1234567890abcdef1234567890abcdef1234567890",
        recommended_target="infant_caregivers",
    ),

    # 4. Pediatric Diarrhea, Dehydration & ORS/Zinc (ICD-10: A09, SNOMED: 66541003)
    HealthEducationClip(
        clip_id="he-ped-diarrhea-hi",
        title="दस्त में ओआरएस (ORS) और जिंक का घोल कैसे बनाएं",
        description="निर्जलीकरण से बचाव और जीवनरक्षक घोल तैयार करने की सही विधि (Hindi)",
        condition_code="66541003",
        condition_coding_system="SNOMED-CT",
        condition_name="Acute Diarrhea & Dehydration",
        language_code="hi",
        media_type="audio",
        download_url="/static/health-education/hi/ped_ors_zinc.opus",
        file_size_bytes=298000,
        duration_seconds=84,
        checksum_sha256="d5e6f7a2b3c47890abcdef1234567890abcdef1234567890abcdef1234567890",
        recommended_target="infant_caregivers",
    ),

    # 5. Non-Communicable Diseases - Hypertension & Diabetes (ICD-10: I10, SNOMED: 38341003)
    HealthEducationClip(
        clip_id="he-ncd-hypertension-hi",
        title="उच्च रक्तचाप (बीपी) और शुगर की नियमित जांच और परहेज",
        description="नमक कम करें, तंबाकू छोड़ें और पीएचसी में निशुल्क जांच करवाएं (Hindi)",
        condition_code="38341003",
        condition_coding_system="SNOMED-CT",
        condition_name="Hypertension Screening",
        language_code="hi",
        media_type="audio",
        download_url="/static/health-education/hi/ncd_hypertension.opus",
        file_size_bytes=389000,
        duration_seconds=110,
        checksum_sha256="e6f7a2b3c4d57890abcdef1234567890abcdef1234567890abcdef1234567890",
        recommended_target="adults_30_plus",
    ),
]


class AshaMediaService:
    """
    Manages chunked audio ingestion, paper register snapshot tagging for OCR,
    and localized clinical health education catalogs.
    """

    @staticmethod
    def init_chunked_upload(req: ChunkedUploadInitRequest) -> ChunkedUploadInitResponse:
        session_id = f"chunk-sess-{uuid.uuid4().hex[:16]}"
        now = datetime.now(timezone.utc)
        expires_at = (now + timedelta(hours=24)).isoformat()

        _ACTIVE_CHUNK_SESSIONS[session_id] = {
            "req": req.model_dump(),
            "created_at": now.isoformat(),
            "expires_at": expires_at,
            "received_chunks": set(),
            "bucket": settings.asha_media_bucket_name,
        }
        _CHUNK_STORE[session_id] = {}

        return ChunkedUploadInitResponse(
            session_id=session_id,
            upload_url=f"/v1/asha-media/upload/{session_id}/chunk",
            chunk_size_bytes=req.chunk_size_bytes,
            total_chunks=req.total_chunks,
            expires_at=expires_at,
        )

    @staticmethod
    def upload_chunk(session_id: str, chunk_index: int, chunk_data: bytes) -> ChunkUploadResponse:
        if session_id not in _ACTIVE_CHUNK_SESSIONS:
            raise ValueError(f"Invalid or expired upload session: {session_id}")

        session_meta = _ACTIVE_CHUNK_SESSIONS[session_id]
        total_chunks = session_meta["req"]["total_chunks"]

        if chunk_index < 0 or chunk_index >= total_chunks:
            raise ValueError(f"Chunk index {chunk_index} out of range [0, {total_chunks - 1}]")

        _CHUNK_STORE[session_id][chunk_index] = chunk_data
        session_meta["received_chunks"].add(chunk_index)

        received_sorted = sorted(list(session_meta["received_chunks"]))
        is_complete = len(received_sorted) == total_chunks

        return ChunkUploadResponse(
            session_id=session_id,
            chunk_index=chunk_index,
            bytes_received=len(chunk_data),
            received_chunks=received_sorted,
            is_complete=is_complete,
        )

    @staticmethod
    def complete_chunked_upload(session_id: str, checksum_sha256: Optional[str] = None) -> ChunkedUploadCompleteResponse:
        if session_id not in _ACTIVE_CHUNK_SESSIONS:
            raise ValueError(f"Invalid or expired upload session: {session_id}")

        session_meta = _ACTIVE_CHUNK_SESSIONS[session_id]
        req = session_meta["req"]
        total_chunks = req["total_chunks"]
        chunks = _CHUNK_STORE.get(session_id, {})

        if len(chunks) < total_chunks:
            missing = sorted(list(set(range(total_chunks)) - set(chunks.keys())))
            raise ValueError(f"Incomplete upload: missing chunks {missing}")

        # Reassemble audio chunks in sequential order
        buffer = io.BytesIO()
        hasher = hashlib.sha256()
        for idx in range(total_chunks):
            chunk = chunks[idx]
            buffer.write(chunk)
            hasher.update(chunk)

        assembled_bytes = buffer.getvalue()
        computed_checksum = hasher.hexdigest()

        if checksum_sha256 and checksum_sha256.lower() != computed_checksum.lower():
            raise ValueError(f"SHA-256 checksum mismatch: expected {checksum_sha256}, computed {computed_checksum}")

        file_id = f"file-audio-{uuid.uuid4().hex[:12]}"
        storage_key = f"{settings.asha_media_bucket_name}/voice/{req['village_lgd_code']}/{req['visit_uuid']}/{req['filename']}"

        tags = [
            "asha:field_voice",
            f"codec:{req['audio_codec']}",
            f"lang:{req['language_code']}",
            f"village:{req['village_lgd_code']}",
            f"worker:{req['worker_id']}",
            f"patient:{req['patient_id']}",
            f"visit:{req['visit_uuid']}",
        ]

        metadata = {
            "visit_uuid": req["visit_uuid"],
            "patient_id": req["patient_id"],
            "worker_id": req["worker_id"],
            "village_lgd_code": req["village_lgd_code"],
            "language_code": req["language_code"],
            "audio_codec": req["audio_codec"],
            "duration_seconds": str(req.get("duration_seconds") or ""),
            "checksum_sha256": computed_checksum,
        }

        # Clean up session memory cache
        del _ACTIVE_CHUNK_SESSIONS[session_id]
        del _CHUNK_STORE[session_id]

        return ChunkedUploadCompleteResponse(
            file_id=file_id,
            filename=req["filename"],
            storage_key=storage_key,
            size_bytes=len(assembled_bytes),
            content_type=req["content_type"],
            category="audio",
            tags=tags,
            status="ready",
            metadata=metadata,
        )

    @staticmethod
    def process_register_photo(
        filename: str,
        content_type: str,
        size_bytes: int,
        register_type: str,
        village_lgd_code: str,
        worker_id: str,
        patient_id: Optional[str] = None,
        subcentre_id: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> RegisterPhotoUploadResponse:
        file_id = f"file-reg-{uuid.uuid4().hex[:12]}"
        ocr_job_id = f"ocr-job-{uuid.uuid4().hex[:16]}"
        storage_key = f"{settings.asha_media_bucket_name}/registers/{village_lgd_code}/{file_id}_{filename}"

        tags = [
            register_type,  # e.g. "register:mcp_card" or "register:immunization"
            OcrStatus.PENDING,
            "doc_type:register_snapshot",
            f"village:{village_lgd_code}",
            f"worker:{worker_id}",
        ]
        if subcentre_id:
            tags.append(f"subcentre:{subcentre_id}")
        if patient_id:
            tags.append(f"patient:{patient_id}")

        return RegisterPhotoUploadResponse(
            file_id=file_id,
            filename=filename,
            storage_key=storage_key,
            size_bytes=size_bytes,
            tags=tags,
            ocr_status=OcrStatus.PENDING,
            ocr_job_id=ocr_job_id,
            village_lgd_code=village_lgd_code,
        )

    @staticmethod
    def get_health_education_catalog(
        language_code: Optional[str] = None,
        condition_code: Optional[str] = None,
        target: Optional[str] = None,
    ) -> HealthEducationCatalogResponse:
        clips = LOCALIZED_HEALTH_EDUCATION_CLIPS

        if language_code:
            clips = [c for c in clips if c.language_code.lower() == language_code.lower()]
        if condition_code:
            clips = [c for c in clips if c.condition_code == condition_code]
        if target:
            clips = [c for c in clips if c.recommended_target.lower() == target.lower()]

        supported_languages = sorted(list(set(c.language_code for c in LOCALIZED_HEALTH_EDUCATION_CLIPS)))

        return HealthEducationCatalogResponse(
            total=len(clips),
            supported_languages=supported_languages,
            clips=clips,
            sync_timestamp=datetime.now(timezone.utc).isoformat(),
        )
