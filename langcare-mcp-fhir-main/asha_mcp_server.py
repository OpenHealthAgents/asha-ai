"""
ASHA AI Copilot Model Context Protocol (MCP) Server.
Core clinical intelligence engine exposing strongly-typed tools,
NHM/IMNCI clinical guidelines as MCP resources, and structured clinical prompts.
"""

import json
import os
import sys
from typing import Any, Dict, List, Optional

# Add workspace path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server.mcpserver import MCPServer
from asha_clinical_engine import (
    ClinicalRuleEngine,
    HouseholdCareGapDetector,
    LocalizedCounselingGenerator,
    TranscriptExtractor,
    NHM_ASHA_MATERNAL_CHILD_HANDBOOK,
    IMNCI_PEDIATRIC_TRIAGE_PROTOCOL,
    ANC_HIGH_RISK_PREGNANCY_PROTOCOL,
    CBAC_NCD_SCREENING_GUIDELINE,
)

# Initialize MCP Server with clinical copilot metadata
app = MCPServer(
    name="asha-clinical-copilot-mcp",
)

care_gap_detector = HouseholdCareGapDetector()
counseling_generator = LocalizedCounselingGenerator()


# ==============================================================================
# 1. MCP TOOLS IMPLEMENTATION
# ==============================================================================

@app.tool(
    name="extract_structured_visit_from_transcript",
    description=(
        "Extracts clinical entities, vital signs (BP, SpO2, Heart rate, Temp, Hemoglobin), "
        "symptoms, and care observations from regional language ASR transcripts (Sarvam API) "
        "and maps them into valid FHIR R4 Encounter, Observation[], and QuestionnaireResponse resources."
    ),
)
def extract_structured_visit_from_transcript(
    transcript: str,
    patient_id: str,
    worker_id: str,
    village_lgd_code: str,
    language_code: str = "hi-IN",
    visit_uuid: Optional[str] = None,
    is_maternal: bool = False,
    is_pediatric: bool = False,
    encounter_type: str = "household_visit",
) -> Dict[str, Any]:
    """
    Extracts structured FHIR visit bundle from regional ASR transcript.
    """
    encounter, observations, questionnaire_response = TranscriptExtractor.build_fhir_resources(
        transcript=transcript,
        patient_id=patient_id,
        worker_id=worker_id,
        village_lgd_code=village_lgd_code,
        visit_uuid=visit_uuid,
        encounter_type=encounter_type,
        is_maternal=is_maternal,
        is_pediatric=is_pediatric,
    )

    extracted_vitals = TranscriptExtractor.extract_vitals(transcript)
    extracted_symptoms = TranscriptExtractor.extract_symptoms(transcript)

    return {
        "status": "SUCCESS",
        "patient_id": patient_id,
        "worker_id": worker_id,
        "village_lgd_code": village_lgd_code,
        "language_code": language_code,
        "extracted_entities": {
            "vitals": extracted_vitals,
            "symptoms": extracted_symptoms,
        },
        "fhir_resources": {
            "encounter": encounter,
            "observations": observations,
            "questionnaire_response": questionnaire_response,
        },
    }


@app.tool(
    name="evaluate_maternal_pediatric_red_flags",
    description=(
        "Deterministic + LLM hybrid clinical rule engine based on NHM/IMNCI guidelines. "
        "Evaluates maternal high-risk flags (BP >= 140/90, Hb < 7 g/dL, bleeding, reduced fetal movement, "
        "pedal edema) and pediatric danger signs (fast breathing/chest indrawing, lethargy, inability to "
        "breastfeed, convulsions, fever with rash). Outputs a structured FHIR R4 RiskAssessment resource "
        "(HIGH, MODERATE, LOW) with explicit referral instructions."
    ),
)
def evaluate_maternal_pediatric_red_flags(
    patient_id: str,
    is_maternal: bool = False,
    gestational_age_weeks: Optional[int] = None,
    is_pediatric: bool = False,
    age_months: Optional[int] = None,
    systolic_bp: Optional[float] = None,
    diastolic_bp: Optional[float] = None,
    hemoglobin: Optional[float] = None,
    spo2: Optional[float] = None,
    temperature_c: Optional[float] = None,
    temperature_f: Optional[float] = None,
    fetal_heart_rate: Optional[float] = None,
    respiratory_rate: Optional[float] = None,
    symptoms: Optional[List[str]] = None,
    encounter_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Evaluates clinical parameters against NHM and IMNCI danger sign rules.
    """
    vitals: Dict[str, float] = {}
    if systolic_bp is not None:
        vitals["systolic_bp"] = systolic_bp
    if diastolic_bp is not None:
        vitals["diastolic_bp"] = diastolic_bp
    if hemoglobin is not None:
        vitals["hemoglobin"] = hemoglobin
    if spo2 is not None:
        vitals["spo2"] = spo2
    if temperature_c is not None:
        vitals["temperature_c"] = temperature_c
    elif temperature_f is not None:
        vitals["temperature_f"] = temperature_f
    if fetal_heart_rate is not None:
        vitals["fetal_heart_rate"] = fetal_heart_rate
    if respiratory_rate is not None:
        vitals["respiratory_rate"] = respiratory_rate

    result = ClinicalRuleEngine.evaluate(
        patient_id=patient_id,
        is_maternal=is_maternal,
        gestational_age_weeks=gestational_age_weeks,
        is_pediatric=is_pediatric,
        age_months=age_months,
        vitals=vitals,
        symptoms=symptoms or [],
        encounter_id=encounter_id,
    )

    flags_data = [
        {
            "code": f.code,
            "category": f.category,
            "description": f.description,
            "severity": f.severity.value,
            "snomed_code": f.snomed_code,
            "urgency": f.referral_urgency,
            "action": f.action,
        }
        for f in result.flags
    ]

    return {
        "status": "EVALUATED",
        "risk_level": result.risk_level.value,
        "clinical_summary": result.clinical_summary,
        "referral_facility": result.referral_facility,
        "transport_mode": result.transport_mode,
        "explicit_referral_instructions": result.explicit_referral_instructions,
        "triggered_flags": flags_data,
        "fhir_risk_assessment": result.fhir_risk_assessment,
    }


@app.tool(
    name="detect_household_care_gaps",
    description=(
        "Queries medplum via bezs-emr-gql for all members of a rural household Group. "
        "Returns overdue infant/child immunizations (Pentavalent, MR, BCG, Rotavirus), "
        "missed Antenatal Care (ANC) visits, and overdue 30+ adult NCD/CBAC screenings."
    ),
)
def detect_household_care_gaps(
    household_group_id: str,
    village_lgd_code: str,
    household_members: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Evaluates care gaps for all members of a rural household Group.
    """
    report = care_gap_detector.detect_household_gaps(
        household_group_id=household_group_id,
        village_lgd_code=village_lgd_code,
        household_members=household_members,
    )

    gaps_list = [
        {
            "member_id": g.member_id,
            "member_name": g.member_name,
            "gap_type": g.gap_type,
            "title": g.title,
            "description": g.description,
            "due_date": g.due_date,
            "days_overdue": g.days_overdue,
            "urgency": g.urgency,
            "action": g.action,
        }
        for g in report.gaps
    ]

    return {
        "status": "SUCCESS",
        "household_group_id": report.household_group_id,
        "village_lgd_code": report.village_lgd_code,
        "evaluated_at": report.evaluated_at,
        "total_gaps": report.total_gaps,
        "counts": {
            "overdue_immunizations": report.overdue_immunizations_count,
            "missed_anc": report.missed_anc_count,
            "pending_ncd": report.pending_ncd_count,
        },
        "care_gaps": gaps_list,
        "action_plan_for_asha": report.action_plan_for_asha,
    }


@app.tool(
    name="generate_localized_counseling_script",
    description=(
        "Generates a culturally sensitive, dialect-appropriate 60-second counseling script "
        "for the ASHA worker to play or read to the family. Pulls verified audio education references "
        "from bezs-filenest indexed by clinical condition code (SNOMED-CT / ICD-10)."
    ),
)
def generate_localized_counseling_script(
    snomed_code: str,
    language_code: str = "hi",
    patient_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generates culturally grounded counseling script with verified audio clips.
    """
    resp = counseling_generator.generate(
        snomed_code=snomed_code,
        language_code=language_code,
        patient_name=patient_name,
    )

    clips_data = [
        {
            "clip_id": c.clip_id,
            "condition_name": c.condition_name,
            "snomed_code": c.snomed_code,
            "language_code": c.language_code,
            "duration_seconds": c.duration_seconds,
            "title": c.title,
            "audio_stream_url": c.audio_stream_url,
            "thumbnail_url": c.thumbnail_url,
        }
        for c in resp.verified_audio_clips
    ]

    return {
        "status": "GENERATED",
        "target_condition": resp.target_condition,
        "snomed_code": resp.condition_snomed_code,
        "language_code": resp.language_code,
        "estimated_read_time_seconds": resp.estimated_read_time_seconds,
        "spoken_counseling_script": resp.spoken_counseling_script,
        "cultural_context_notes": resp.cultural_context_notes,
        "key_takeaways_for_family": resp.key_takeaways_for_family,
        "suggested_action_for_asha": resp.suggested_action_for_asha,
        "verified_audio_clips": clips_data,
    }


# ==============================================================================
# 2. MCP RESOURCES IMPLEMENTATION (NHM Guidelines & Protocol Documents)
# ==============================================================================

@app.resource("resource://nhm/handbooks/asha-maternal-child-v1")
def resource_asha_maternal_child_handbook() -> str:
    """National Health Mission ASHA Clinical Handbook: Maternal and Newborn Care (Module 6 & 7)."""
    return NHM_ASHA_MATERNAL_CHILD_HANDBOOK


@app.resource("resource://nhm/workflows/imnci-triage-v1")
def resource_imnci_triage_protocol() -> str:
    """Integrated Management of Neonatal and Childhood Illnesses (IMNCI) Protocol (MoHFW)."""
    return IMNCI_PEDIATRIC_TRIAGE_PROTOCOL


@app.resource("resource://nhm/workflows/anc-highrisk-protocol-v1")
def resource_anc_high_risk_protocol() -> str:
    """Comprehensive RMNCH+A High-Risk Pregnancy (HRP) Identification and Referral Guidelines."""
    return ANC_HIGH_RISK_PREGNANCY_PROTOCOL


@app.resource("resource://nhm/guidelines/cbac-ncd-screening-v1")
def resource_cbac_ncd_screening() -> str:
    """Community Based Assessment Checklist (CBAC) for NCD Screening (Ayushman Bharat AB-HWC)."""
    return CBAC_NCD_SCREENING_GUIDELINE


# ==============================================================================
# 3. MCP PROMPTS IMPLEMENTATION (Clinical Grounding Workflows)
# ==============================================================================

@app.prompt(name="maternal_anc_triage")
def prompt_maternal_anc_triage(
    patient_name: str,
    gestational_age_weeks: int,
    systolic_bp: int,
    diastolic_bp: int,
    symptoms: str,
) -> str:
    """Prompt for evaluating an Antenatal Care (ANC) home visit against NHM protocols."""
    return f"""You are the clinical copilot for an ASHA worker visiting pregnant mother {patient_name}.
Current Gestational Age: {gestational_age_weeks} weeks.
Recorded Blood Pressure: {systolic_bp}/{diastolic_bp} mmHg.
Reported Symptoms / Complaints: {symptoms}.

Instructions:
1. Refer to resource://nhm/workflows/anc-highrisk-protocol-v1.
2. Check for Pre-eclampsia (BP >= 140/90 mmHg, visual disturbances, epigastric pain, pedal edema).
3. Do NOT recommend or hallucinate any prescription antihypertensive or anticonvulsant dosage (e.g. labetalol, nifedipine) - ASHA workers cannot prescribe medications.
4. If danger signs exist, formulate an urgent referral recommendation to the PHC Medical Officer via 108 Ambulance.
5. Provide a simple, empathetic 3-sentence Hindi or regional explanation for the ASHA to communicate calmly to the family.
"""


@app.prompt(name="imnci_pediatric_assessment")
def prompt_imnci_pediatric_assessment(
    child_name: str,
    age_months: int,
    respiratory_rate: int,
    danger_signs: str,
) -> str:
    """Prompt for pediatric assessment strictly following IMNCI algorithms."""
    return f"""You are assisting an ASHA worker evaluating child {child_name}, age {age_months} months.
Respiratory Rate: {respiratory_rate} breaths/min.
Observed Signs: {danger_signs}.

Instructions:
1. Ground your clinical logic strictly in resource://nhm/workflows/imnci-triage-v1.
2. Check for IMNCI General Danger Signs: Inability to drink/breastfeed, vomiting everything, convulsions, lethargy/unconsciousness.
3. Classify respiratory status: Fast breathing threshold is >= 50 breaths/min for 2-11 months, and >= 40 breaths/min for 12-59 months. Check for chest indrawing.
4. Output the exact IMNCI pink/yellow/green classification (Severe Pneumonia vs Pneumonia vs No Pneumonia).
5. Specify home care (breastfeeding, warmth, fluids) or emergency PHC referral steps.
"""


@app.prompt(name="cbac_ncd_workflow")
def prompt_cbac_ncd_workflow(
    patient_name: str,
    age_years: int,
    tobacco_user: bool,
    systolic_bp: int,
    diastolic_bp: int,
) -> str:
    """Prompt for adult NCD risk screening using Ayushman Bharat CBAC checklist."""
    return f"""You are guiding an ASHA worker conducting an annual NCD screening for {patient_name}, age {age_years}.
Tobacco / Bidi user: {tobacco_user}.
Blood Pressure: {systolic_bp}/{diastolic_bp} mmHg.

Instructions:
1. Ground recommendations in resource://nhm/guidelines/cbac-ncd-screening-v1.
2. Calculate estimated CBAC score risk category.
3. Advise on lifestyle modifications (cessation of tobacco, low salt diet, 150 minutes weekly physical activity).
4. Direct to nearest Ayushman Bharat Health and Wellness Centre (AB-HWC) for confirmation if BP >= 140/90 mmHg.
"""


def main():
    """Run MCP server in stdio mode for MCP clients and agents."""
    app.run()


if __name__ == "__main__":
    main()
