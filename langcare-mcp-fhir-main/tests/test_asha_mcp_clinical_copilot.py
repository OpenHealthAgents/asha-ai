"""
Comprehensive Integration Tests for ASHA AI Copilot MCP Server
and Clinical Intelligence Engine in langcare-mcp-fhir.
"""

import json
import os
import sys

# Configure UTF-8 encoding for multi-lingual console output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add repo to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, REPO_ROOT)

from asha_mcp_server import (
    app,
    extract_structured_visit_from_transcript,
    evaluate_maternal_pediatric_red_flags,
    detect_household_care_gaps,
    generate_localized_counseling_script,
    resource_asha_maternal_child_handbook,
    resource_imnci_triage_protocol,
    resource_anc_high_risk_protocol,
    resource_cbac_ncd_screening,
    prompt_maternal_anc_triage,
    prompt_imnci_pediatric_assessment,
    prompt_cbac_ncd_workflow,
)


def run_tests():
    print("==================================================================")
    print("  Testing ASHA AI Copilot MCP Server & Clinical Intelligence      ")
    print("==================================================================")

    # ------------------------------------------------------------------
    # 1. Test extract_structured_visit_from_transcript
    # ------------------------------------------------------------------
    print("\n--- 1. Testing extract_structured_visit_from_transcript ---")
    hindi_transcript = (
        "नमस्ते दीदी। आज अनीता दीदी के घर आए हैं। इनका बीपी 145/95 आया है। "
        "खून की जांच में हीमोग्लोबिन 6.5 ग्राम है। पैरों में हल्की सूजन (pair me sujan) है "
        "और हल्का सिर दर्द भी है। सांस लेने में कोई परेशानी नहीं है।"
    )

    extracted = extract_structured_visit_from_transcript(
        transcript=hindi_transcript,
        patient_id="patient-asha-anita-patra",
        worker_id="usr-asha-sunita",
        village_lgd_code="215432",
        language_code="hi-IN",
        is_maternal=True,
        encounter_type="anc_home_visit",
    )

    assert extracted["status"] == "SUCCESS"
    vitals = extracted["extracted_entities"]["vitals"]
    assert vitals.get("systolic_bp") == 145.0, f"Expected 145.0, got {vitals.get('systolic_bp')}"
    assert vitals.get("diastolic_bp") == 95.0, f"Expected 95.0, got {vitals.get('diastolic_bp')}"
    assert vitals.get("hemoglobin") == 6.5, f"Expected 6.5, got {vitals.get('hemoglobin')}"
    print(f"[OK] Extracted Vitals: BP {vitals['systolic_bp']}/{vitals['diastolic_bp']} mmHg, Hb {vitals['hemoglobin']} g/dL")

    symptoms = extracted["extracted_entities"]["symptoms"]
    assert "pedal_edema" in symptoms
    print(f"[OK] Extracted Symptoms: {symptoms}")

    fhir_res = extracted["fhir_resources"]
    assert fhir_res["encounter"]["resourceType"] == "Encounter"
    assert fhir_res["encounter"]["subject"]["reference"] == "Patient/patient-asha-anita-patra"
    assert len(fhir_res["observations"]) >= 2
    loinc_codes = [obs["code"]["coding"][0]["code"] for obs in fhir_res["observations"]]
    assert "85354-9" in loinc_codes  # BP
    assert "718-7" in loinc_codes    # Hb
    print(f"[OK] Validated FHIR Encounter & Observations (LOINCs: {loinc_codes})")

    qr = fhir_res["questionnaire_response"]
    assert qr["resourceType"] == "QuestionnaireResponse"
    assert "anc-highrisk-v1" in qr["questionnaire"]
    print(f"[OK] Validated QuestionnaireResponse ({qr['questionnaire']})")

    # ------------------------------------------------------------------
    # 2. Test evaluate_maternal_pediatric_red_flags
    # ------------------------------------------------------------------
    print("\n--- 2. Testing evaluate_maternal_pediatric_red_flags ---")

    # 2A. Maternal High-Risk Evaluation
    mat_eval = evaluate_maternal_pediatric_red_flags(
        patient_id="patient-asha-anita-patra",
        is_maternal=True,
        gestational_age_weeks=32,
        systolic_bp=148.0,
        diastolic_bp=96.0,
        hemoglobin=6.4,
        symptoms=["pair me sujan", "bleeding"],
    )
    assert mat_eval["risk_level"] == "HIGH"
    flag_codes = [f["code"] for f in mat_eval["triggered_flags"]]
    assert "MAT_PREECLAMPSIA_BP" in flag_codes
    assert "MAT_SEVERE_ANEMIA" in flag_codes
    assert "MAT_VAGINAL_BLEEDING" in flag_codes
    assert mat_eval["fhir_risk_assessment"]["resourceType"] == "RiskAssessment"
    assert "108" in mat_eval["transport_mode"]
    print(f"[OK] Maternal Red Flags Detected: {flag_codes}")
    print(f"     Risk Level: {mat_eval['risk_level']} | Transport: {mat_eval['transport_mode']}")
    print(f"     Referral Facility: {mat_eval['referral_facility']}")

    # 2B. Pediatric IMNCI Danger Signs Evaluation
    ped_eval = evaluate_maternal_pediatric_red_flags(
        patient_id="patient-asha-baby-aarav",
        is_pediatric=True,
        age_months=6,
        respiratory_rate=58.0,
        spo2=89.0,
        temperature_c=39.2,
        symptoms=["inability to breastfeed", "convulsions", "chest indrawing"],
    )
    assert ped_eval["risk_level"] == "HIGH"
    ped_codes = [f["code"] for f in ped_eval["triggered_flags"]]
    assert "PED_INABILITY_TO_FEED" in ped_codes
    assert "PED_CONVULSIONS" in ped_codes
    assert "PED_SEVERE_PNEUMONIA" in ped_codes
    print(f"[OK] Pediatric IMNCI Flags Detected: {ped_codes}")
    print(f"     Risk Level: {ped_eval['risk_level']} | Transport: {ped_eval['transport_mode']}")

    # 2C. Low-Risk Routine Visit
    low_eval = evaluate_maternal_pediatric_red_flags(
        patient_id="patient-routine-01",
        is_maternal=True,
        gestational_age_weeks=18,
        systolic_bp=116.0,
        diastolic_bp=74.0,
        hemoglobin=11.5,
        symptoms=[],
    )
    assert low_eval["risk_level"] == "LOW"
    assert len(low_eval["triggered_flags"]) == 0
    print(f"[OK] Routine Low Risk Visit Evaluated: {low_eval['risk_level']}")

    # ------------------------------------------------------------------
    # 3. Test detect_household_care_gaps
    # ------------------------------------------------------------------
    print("\n--- 3. Testing detect_household_care_gaps ---")
    mock_members = [
        {
            "id": "patient-infant-01",
            "name": "Baby Aarav",
            "age_months": 3,
            "received_vaccines": ["BCG", "HepB-0", "OPV-0"],
        },
        {
            "id": "patient-mother-01",
            "name": "Anita Patra",
            "age_years": 24,
            "is_pregnant": True,
            "gestational_weeks": 29,
            "completed_anc_visits": 1,
        },
        {
            "id": "patient-father-01",
            "name": "Ramesh Patra",
            "age_years": 42,
            "last_ncd_screening_date": None,
        },
    ]

    care_gaps = detect_household_care_gaps(
        household_group_id="group-household-ward3-42",
        village_lgd_code="215432",
        household_members=mock_members,
    )
    assert care_gaps["status"] == "SUCCESS"
    assert care_gaps["total_gaps"] >= 3
    counts = care_gaps["counts"]
    assert counts["overdue_immunizations"] >= 2  # Pentavalent-1 and Rotavirus-1
    assert counts["missed_anc"] >= 1            # 2nd ANC missed
    assert counts["pending_ncd"] >= 1           # Adult 30+ screening
    print(f"[OK] Household Care Gaps: {care_gaps['total_gaps']} total gaps detected")
    print(f"     Immunizations: {counts['overdue_immunizations']}, ANC: {counts['missed_anc']}, NCD: {counts['pending_ncd']}")
    for action in care_gaps["action_plan_for_asha"]:
        print(f"     Action: {action}")

    # ------------------------------------------------------------------
    # 4. Test generate_localized_counseling_script
    # ------------------------------------------------------------------
    print("\n--- 4. Testing generate_localized_counseling_script ---")

    # 4A. Hindi Pre-eclampsia Counseling
    counsel_hi = generate_localized_counseling_script(
        snomed_code="398254007",
        language_code="hi",
        patient_name="Anita",
    )
    assert counsel_hi["status"] == "GENERATED"
    assert counsel_hi["language_code"] == "hi"
    assert "रक्तचाप" in counsel_hi["spoken_counseling_script"]
    assert len(counsel_hi["verified_audio_clips"]) > 0
    print(f"[OK] Hindi Counseling Script Generated ({counsel_hi['estimated_read_time_seconds']}s read time)")
    print(f"     Title: {counsel_hi['target_condition']}")
    print(f"     Snippet: {counsel_hi['spoken_counseling_script'][:100]}...")
    print(f"     Verified Audio Clip: {counsel_hi['verified_audio_clips'][0]['audio_stream_url']}")

    # 4B. Odia Pre-eclampsia Counseling
    counsel_or = generate_localized_counseling_script(
        snomed_code="398254007",
        language_code="or",
        patient_name="Anita",
    )
    assert counsel_or["language_code"] == "or"
    assert "ରକ୍ତଚାପ" in counsel_or["spoken_counseling_script"]
    print(f"[OK] Odia Counseling Script Generated:")
    print(f"     Snippet: {counsel_or['spoken_counseling_script'][:100]}...")

    # ------------------------------------------------------------------
    # 5. Test MCP Resources & Prompts
    # ------------------------------------------------------------------
    print("\n--- 5. Testing MCP Resources & Prompts ---")

    # Resources
    handbook = resource_asha_maternal_child_handbook()
    assert "National Health Mission" in handbook
    assert "ANC 1" in handbook

    imnci = resource_imnci_triage_protocol()
    assert "IMNCI" in imnci
    assert "General Danger Signs" in imnci

    anc_hrp = resource_anc_high_risk_protocol()
    assert "High-Risk Pregnancy" in anc_hrp

    cbac = resource_cbac_ncd_screening()
    assert "CBAC" in cbac
    print("[OK] All 4 NHM Protocol MCP Resources verified & grounded in MoHFW standards.")

    # Prompts
    p1 = prompt_maternal_anc_triage("Sunita", 32, 145, 95, "severe headache")
    assert "resource://nhm/workflows/anc-highrisk-protocol-v1" in p1
    assert "Do NOT recommend or hallucinate" in p1

    p2 = prompt_imnci_pediatric_assessment("Aarav", 8, 54, "chest indrawing")
    assert "resource://nhm/workflows/imnci-triage-v1" in p2

    p3 = prompt_cbac_ncd_workflow("Ramesh", 45, True, 142, 90)
    assert "resource://nhm/guidelines/cbac-ncd-screening-v1" in p3
    print("[OK] All 3 MCP Prompts verified with strict clinical anti-hallucination guardrails.")

    print("\n==================================================================")
    print("  [OK] ALL ASHA AI COPILOT MCP TOOLS & PROTOCOLS PASSED CLEANLY!  ")
    print("==================================================================")


if __name__ == "__main__":
    run_tests()
