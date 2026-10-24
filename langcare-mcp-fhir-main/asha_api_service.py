"""
HTTP/REST & MCP Clinical Service for Frontline ASHA Copilot.
Exposes real-time endpoints on port 8090 for mobile and backend clients:
- GET  /health
- POST /api/v1/clinical/evaluate-red-flags
- POST /api/v1/clinical/extract-transcript
- POST /api/v1/clinical/detect-care-gaps
- POST /api/v1/clinical/counseling-script
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uvicorn
import asha_mcp_server

app = FastAPI(
    title="SevaFirst Frontline Clinical Intelligence API",
    description="IMNCI/NHM Clinical Decision Support & Regional Voice Triage Engine",
    version="1.0.0",
)


class EvaluateRedFlagsRequest(BaseModel):
    patient_id: str
    is_maternal: bool = False
    gestational_age_weeks: Optional[int] = None
    is_pediatric: bool = False
    age_months: Optional[int] = None
    systolic_bp: Optional[float] = None
    diastolic_bp: Optional[float] = None
    hemoglobin: Optional[float] = None
    spo2: Optional[float] = None
    temperature_c: Optional[float] = None
    temperature_f: Optional[float] = None
    fetal_heart_rate: Optional[float] = None
    respiratory_rate: Optional[float] = None
    symptoms: Optional[List[str]] = None
    encounter_id: Optional[str] = None


class ExtractTranscriptRequest(BaseModel):
    transcript: str
    patient_id: str
    worker_id: str
    village_lgd_code: str
    language_code: str = "hi-IN"
    visit_uuid: Optional[str] = None
    is_maternal: bool = False
    is_pediatric: bool = False
    encounter_type: str = "household_visit"


class DetectCareGapsRequest(BaseModel):
    household_group_id: str
    village_lgd_code: str
    household_members: Optional[List[Dict[str, Any]]] = None


class CounselingScriptRequest(BaseModel):
    snomed_code: str
    language_code: str = "hi"
    patient_name: Optional[str] = None


@app.get("/health")
def healthcheck():
    return {
        "status": "healthy",
        "service": "sevafirst-clinical-mcp",
        "mcp_version": "2.3.0",
        "nhm_guidelines": "NHM ASHA Modules 6 & 7 / IMNCI Protocol 2026",
    }


@app.post("/api/v1/clinical/evaluate-red-flags")
def evaluate_red_flags(req: EvaluateRedFlagsRequest):
    return asha_mcp_server.evaluate_maternal_pediatric_red_flags(
        patient_id=req.patient_id,
        is_maternal=req.is_maternal,
        gestational_age_weeks=req.gestational_age_weeks,
        is_pediatric=req.is_pediatric,
        age_months=req.age_months,
        systolic_bp=req.systolic_bp,
        diastolic_bp=req.diastolic_bp,
        hemoglobin=req.hemoglobin,
        spo2=req.spo2,
        temperature_c=req.temperature_c,
        temperature_f=req.temperature_f,
        fetal_heart_rate=req.fetal_heart_rate,
        respiratory_rate=req.respiratory_rate,
        symptoms=req.symptoms,
        encounter_id=req.encounter_id,
    )


@app.post("/api/v1/clinical/extract-transcript")
def extract_transcript(req: ExtractTranscriptRequest):
    return asha_mcp_server.extract_structured_visit_from_transcript(
        transcript=req.transcript,
        patient_id=req.patient_id,
        worker_id=req.worker_id,
        village_lgd_code=req.village_lgd_code,
        language_code=req.language_code,
        visit_uuid=req.visit_uuid,
        is_maternal=req.is_maternal,
        is_pediatric=req.is_pediatric,
        encounter_type=req.encounter_type,
    )


@app.post("/api/v1/clinical/detect-care-gaps")
def detect_care_gaps(req: DetectCareGapsRequest):
    return asha_mcp_server.detect_household_care_gaps(
        household_group_id=req.household_group_id,
        village_lgd_code=req.village_lgd_code,
        household_members=req.household_members,
    )


@app.post("/api/v1/clinical/counseling-script")
def counseling_script(req: CounselingScriptRequest):
    return asha_mcp_server.generate_localized_counseling_script(
        snomed_code=req.snomed_code,
        language_code=req.language_code,
        patient_name=req.patient_name,
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8090)
