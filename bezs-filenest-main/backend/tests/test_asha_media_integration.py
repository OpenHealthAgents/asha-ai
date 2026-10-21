"""
Integration tests for ASHA Media: Resumable chunked audio uploads,
paper register OCR archival tagging, and localized health education catalog.
"""

import hashlib
import io
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ.setdefault("DATABASE_PRIMARY_URL", "postgresql+asyncpg://filenest:filenest@localhost:5432/filenest")

from app.schemas.asha_media import (
    AudioCodec,
    ChunkedUploadInitRequest,
    RegisterType,
    OcrStatus,
)
from app.services.asha_media_service import AshaMediaService


def test_chunked_audio_upload_lifecycle():
    print("\n--- 1. Testing Chunked Audio Upload Lifecycle ---")

    # Simulate 512KB .opus audio stream split into two 256KB chunks
    sample_opus_data = b"OggS\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00OpusHead" + (b"\xaa" * 524200)
    total_size = len(sample_opus_data)
    chunk_size = 262144
    chunk0 = sample_opus_data[:chunk_size]
    chunk1 = sample_opus_data[chunk_size:]
    expected_sha256 = hashlib.sha256(sample_opus_data).hexdigest()

    init_req = ChunkedUploadInitRequest(
        filename="anc_visit_audio_01.opus",
        content_type="audio/opus",
        total_size_bytes=total_size,
        chunk_size_bytes=chunk_size,
        total_chunks=2,
        audio_codec=AudioCodec.OPUS,
        duration_seconds=124.5,
        visit_uuid="visit-uuid-asha-881",
        patient_id="patient-asha-anita-patra",
        worker_id="usr-asha-sunita",
        village_lgd_code="215432",
        language_code="or",  # Odia dialect
    )

    # 1. Initialize chunked session
    init_res = AshaMediaService.init_chunked_upload(init_req)
    assert init_res.session_id.startswith("chunk-sess-")
    assert init_res.total_chunks == 2
    print(f"[OK] Chunked session initialized: {init_res.session_id} (Bucket: asha-field-media)")

    # 2. Upload Chunk 0
    c0_res = AshaMediaService.upload_chunk(init_res.session_id, 0, chunk0)
    assert c0_res.bytes_received == len(chunk0)
    assert not c0_res.is_complete
    print(f"[OK] Chunk 0 uploaded ({c0_res.bytes_received} bytes). Complete: {c0_res.is_complete}")

    # 3. Upload Chunk 1
    c1_res = AshaMediaService.upload_chunk(init_res.session_id, 1, chunk1)
    assert c1_res.bytes_received == len(chunk1)
    assert c1_res.is_complete
    print(f"[OK] Chunk 1 uploaded ({c1_res.bytes_received} bytes). Complete: {c1_res.is_complete}")

    # 4. Finalize & Verify Assembly
    complete_res = AshaMediaService.complete_chunked_upload(
        session_id=init_res.session_id,
        checksum_sha256=expected_sha256,
    )
    assert complete_res.size_bytes == total_size
    assert complete_res.status == "ready"
    assert "asha:field_voice" in complete_res.tags
    assert "codec:opus" in complete_res.tags
    assert "lang:or" in complete_res.tags
    assert complete_res.metadata["checksum_sha256"] == expected_sha256
    print(f"[OK] Assembled file: {complete_res.storage_key} ({complete_res.size_bytes} bytes)")
    print(f"     Tags: {', '.join(complete_res.tags)}")


def test_paper_register_photo_archival():
    print("\n--- 2. Testing Paper Register Snapshot Tagging ---")
    photo_res = AshaMediaService.process_register_photo(
        filename="mcp_card_page2_anc_schedule.jpg",
        content_type="image/jpeg",
        size_bytes=2450000,
        register_type=RegisterType.MCP_CARD.value,
        village_lgd_code="215432",
        worker_id="usr-asha-sunita",
        patient_id="patient-asha-anita-patra",
        subcentre_id="sc-rampur-01",
        notes="High-risk pregnancy Mamta card with handwritten Hb 6.8 g/dL alert.",
    )

    assert photo_res.ocr_status == OcrStatus.PENDING
    assert RegisterType.MCP_CARD.value in photo_res.tags
    assert "ocr:pending" in photo_res.tags
    assert "village:215432" in photo_res.tags
    assert "subcentre:sc-rampur-01" in photo_res.tags
    print(f"[OK] Register Snapshot Stored: {photo_res.storage_key}")
    print(f"     OCR Job ID: {photo_res.ocr_job_id}")
    print(f"     Archival Tags: {', '.join(photo_res.tags)}")


def test_localized_health_education_catalog():
    print("\n--- 3. Testing Localized Health Education Catalog ---")

    # Query all
    all_catalog = AshaMediaService.get_health_education_catalog()
    assert all_catalog.total >= 8
    print(f"[OK] Total Health Education Clips: {all_catalog.total}")
    print(f"     Supported Languages: {', '.join(all_catalog.supported_languages)}")

    # Query filtered by Language (Odia)
    odia_catalog = AshaMediaService.get_health_education_catalog(language_code="or")
    assert odia_catalog.total >= 2
    for clip in odia_catalog.clips:
        print(f"  - [{clip.language_code.upper()}] Condition: {clip.condition_name}, Code: {clip.condition_code}")

    # Query filtered by SNOMED-CT code (Pre-eclampsia 398254007)
    preeclampsia_clips = AshaMediaService.get_health_education_catalog(condition_code="398254007")
    assert len(preeclampsia_clips.clips) >= 3  # Hindi, Odia, Tamil, Telugu
    print(f"[OK] Pre-eclampsia (SNOMED 398254007) Clips across dialects: {len(preeclampsia_clips.clips)}")


if __name__ == "__main__":
    print("==================================================================")
    print("  Testing bezs-filenest ASHA Media Ingestion & Education Catalog  ")
    print("==================================================================")
    test_chunked_audio_upload_lifecycle()
    test_paper_register_photo_archival()
    test_localized_health_education_catalog()
    print("\n==================================================================")
    print("  [OK] ALL BEZS-FILENEST INTEGRATION TESTS PASSED CLEANLY!         ")
    print("==================================================================")
