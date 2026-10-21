"""
Deterministic + LLM Hybrid Clinical Rule Engine for ASHA AI Copilot.
Implements NHM / IMNCI red flag rules for maternal and pediatric triage,
outputting strongly-typed FHIR R4 RiskAssessment resources.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import uuid
from typing import Any, Dict, List, Optional


class RiskLevel(str, Enum):
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"


@dataclass
class ClinicalFlag:
    code: str
    category: str  # "MATERNAL" | "PEDIATRIC" | "GENERAL"
    description: str
    severity: RiskLevel
    snomed_code: Optional[str] = None
    referral_urgency: str = "ROUTINE"  # "IMMEDIATE_EMERGENCY" | "SAME_DAY" | "ROUTINE"
    action: str = ""


@dataclass
class TriageEvaluationResult:
    risk_level: RiskLevel
    flags: List[ClinicalFlag] = field(default_factory=list)
    referral_facility: str = "Primary Health Centre (PHC)"
    transport_mode: str = "Routine"
    explicit_referral_instructions: List[str] = field(default_factory=list)
    clinical_summary: str = ""
    fhir_risk_assessment: Dict[str, Any] = field(default_factory=dict)


class ClinicalRuleEngine:
    """
    Evaluates clinical parameters against NHM ASHA Module 6/7,
    IMNCI guidelines, and RMNCH+A High-Risk Pregnancy protocols.
    """

    @classmethod
    def evaluate(
        cls,
        patient_id: str,
        is_maternal: bool = False,
        gestational_age_weeks: Optional[int] = None,
        is_pediatric: bool = False,
        age_months: Optional[int] = None,
        vitals: Optional[Dict[str, float]] = None,
        symptoms: Optional[List[str]] = None,
        encounter_id: Optional[str] = None,
    ) -> TriageEvaluationResult:
        vitals = vitals or {}
        symptoms = [s.lower().strip() for s in (symptoms or [])]
        detected_flags: List[ClinicalFlag] = []

        systolic = vitals.get("systolic_bp")
        diastolic = vitals.get("diastolic_bp")
        hb = vitals.get("hemoglobin")
        spo2 = vitals.get("spo2")
        temp = vitals.get("temperature_c") or (
            ((vitals.get("temperature_f", 98.6) - 32) * 5 / 9) if vitals.get("temperature_f") else None
        )
        fhr = vitals.get("fetal_heart_rate")
        rr = vitals.get("respiratory_rate")
        glucose = vitals.get("blood_glucose")

        # ---------------------------------------------------------
        # 1. MATERNAL RED FLAGS EVALUATION (NHM / RMNCH+A Protocol)
        # ---------------------------------------------------------
        if is_maternal or (gestational_age_weeks is not None and gestational_age_weeks > 0):
            # Pre-eclampsia / Hypertensive Disorder
            if (systolic is not None and systolic >= 140) or (diastolic is not None and diastolic >= 90):
                severity = RiskLevel.HIGH if (systolic and systolic >= 160) or (diastolic and diastolic >= 110) else RiskLevel.HIGH
                detected_flags.append(
                    ClinicalFlag(
                        code="MAT_PREECLAMPSIA_BP",
                        category="MATERNAL",
                        description=f"Hypertension in Pregnancy ({systolic}/{diastolic} mmHg >= 140/90). Severe risk of pre-eclampsia/eclampsia.",
                        severity=severity,
                        snomed_code="398254007",
                        referral_urgency="IMMEDIATE_EMERGENCY",
                        action="Refer immediately to PHC/FRU. Keep patient in left lateral position. Prepare for Magnesium Sulfate loading dose if instructed by MO.",
                    )
                )

            # Severe Maternal Anemia
            if hb is not None and hb < 7.0:
                detected_flags.append(
                    ClinicalFlag(
                        code="MAT_SEVERE_ANEMIA",
                        category="MATERNAL",
                        description=f"Severe Maternal Anemia (Hb {hb} g/dL < 7.0 g/dL). Critical risk of maternal heart failure and postpartum hemorrhage.",
                        severity=RiskLevel.HIGH,
                        snomed_code="271737000",
                        referral_urgency="IMMEDIATE_EMERGENCY",
                        action="Immediate referral to FRU/District Hospital with blood storage facility for IV Iron Sucrose or blood transfusion.",
                    )
                )
            elif hb is not None and 7.0 <= hb < 10.0:
                detected_flags.append(
                    ClinicalFlag(
                        code="MAT_MODERATE_ANEMIA",
                        category="MATERNAL",
                        description=f"Moderate Maternal Anemia (Hb {hb} g/dL).",
                        severity=RiskLevel.MODERATE,
                        snomed_code="718-7",
                        referral_urgency="SAME_DAY",
                        action="Double dose of IFA tablets (2 tablets daily) after treating worms, dietary counseling, and follow-up in 14 days.",
                    )
                )

            # Vaginal Bleeding
            if any(term in symptoms for term in ["bleeding", "vaginal bleeding", "spotting", "blood discharge", "haemorrhage"]):
                detected_flags.append(
                    ClinicalFlag(
                        code="MAT_VAGINAL_BLEEDING",
                        category="MATERNAL",
                        description="Antepartum/Postpartum Vaginal Bleeding reported.",
                        severity=RiskLevel.HIGH,
                        snomed_code="289530006",
                        referral_urgency="IMMEDIATE_EMERGENCY",
                        action="EMERGENCY 108 AMBULANCE REFERRAL. Do NOT perform digital vaginal exam. Elevate legs, keep mother warm.",
                    )
                )

            # Reduced or Absent Fetal Movement
            if any(term in symptoms for term in ["reduced fetal movement", "no fetal movement", "decreased movement", "baccha nahi hil raha"]):
                detected_flags.append(
                    ClinicalFlag(
                        code="MAT_REDUCED_FETAL_MOVEMENT",
                        category="MATERNAL",
                        description="Reduced or absent fetal movement in third trimester.",
                        severity=RiskLevel.HIGH,
                        snomed_code="276369006",
                        referral_urgency="IMMEDIATE_EMERGENCY",
                        action="Urgent referral to PHC/FRU for non-stress test (NST) and ultrasound.",
                    )
                )

            # Pedal Edema / Facial Puffiness
            if any(term in symptoms for term in ["pedal edema", "swelling in feet", "swollen feet", "face swelling", "pair me sujan"]):
                detected_flags.append(
                    ClinicalFlag(
                        code="MAT_PEDAL_EDEMA",
                        category="MATERNAL",
                        description="Bilateral pedal edema or facial puffiness.",
                        severity=RiskLevel.MODERATE if (systolic and systolic < 140) else RiskLevel.HIGH,
                        snomed_code="267038008",
                        referral_urgency="SAME_DAY" if (systolic and systolic < 140) else "IMMEDIATE_EMERGENCY",
                        action="Urgent urine albumin check. If BP high or urine protein positive, refer immediately.",
                    )
                )

            # Fetal Heart Rate Distress
            if fhr is not None and (fhr < 110 or fhr > 160):
                detected_flags.append(
                    ClinicalFlag(
                        code="MAT_FETAL_DISTRESS_FHR",
                        category="MATERNAL",
                        description=f"Abnormal Fetal Heart Rate: {fhr} bpm (Normal: 110-160 bpm). Suggests fetal distress.",
                        severity=RiskLevel.HIGH,
                        snomed_code="55283-6",
                        referral_urgency="IMMEDIATE_EMERGENCY",
                        action="Administer maternal oxygen, position mother in left lateral tilt, emergency transport to FRU.",
                    )
                )

        # ---------------------------------------------------------
        # 2. PEDIATRIC RED FLAGS EVALUATION (IMNCI Protocol)
        # ---------------------------------------------------------
        if is_pediatric or (age_months is not None and age_months <= 60):
            # General Danger Signs
            if any(term in symptoms for term in ["inability to breastfeed", "cannot drink", "unable to suck", "doodh nahi pi raha"]):
                detected_flags.append(
                    ClinicalFlag(
                        code="PED_INABILITY_TO_FEED",
                        category="PEDIATRIC",
                        description="Inability to drink or breastfeed. Key IMNCI General Danger Sign.",
                        severity=RiskLevel.HIGH,
                        snomed_code="289169006",
                        referral_urgency="IMMEDIATE_EMERGENCY",
                        action="Immediate PHC referral. If young infant, express breast milk and cup feed on way. Keep warm.",
                    )
                )

            if any(term in symptoms for term in ["vomiting everything", "vomits all", "har cheez ulti"]):
                detected_flags.append(
                    ClinicalFlag(
                        code="PED_VOMITING_EVERYTHING",
                        category="PEDIATRIC",
                        description="Vomiting everything consumed. IMNCI General Danger Sign.",
                        severity=RiskLevel.HIGH,
                        snomed_code="422400008",
                        referral_urgency="IMMEDIATE_EMERGENCY",
                        action="Emergency referral to PHC/FRU. Provide frequent small sips of ORS during transit.",
                    )
                )

            if any(term in symptoms for term in ["convulsions", "fits", "seizures", "daura"]):
                detected_flags.append(
                    ClinicalFlag(
                        code="PED_CONVULSIONS",
                        category="PEDIATRIC",
                        description="Convulsions / fits during present illness.",
                        severity=RiskLevel.HIGH,
                        snomed_code="91175000",
                        referral_urgency="IMMEDIATE_EMERGENCY",
                        action="Immediate emergency referral. Clear airway, place on side, do not insert anything into mouth.",
                    )
                )

            if any(term in symptoms for term in ["lethargy", "unconscious", "floppy", "abnormally sleepy", "behosh"]):
                detected_flags.append(
                    ClinicalFlag(
                        code="PED_LETHARGY",
                        category="PEDIATRIC",
                        description="Lethargy or unconsciousness. Critical neurological / sepsis danger sign.",
                        severity=RiskLevel.HIGH,
                        snomed_code="214264003",
                        referral_urgency="IMMEDIATE_EMERGENCY",
                        action="Immediate emergency transport to PHC/Hospital with pediatric emergency care.",
                    )
                )

            # Respiratory Danger Signs
            fast_breathing = False
            if rr is not None:
                if (age_months or 0) < 2 and rr >= 60:
                    fast_breathing = True
                elif 2 <= (age_months or 0) < 12 and rr >= 50:
                    fast_breathing = True
                elif (age_months or 0) >= 12 and rr >= 40:
                    fast_breathing = True

            chest_indrawing = any(term in symptoms for term in ["chest indrawing", "lower chest wall goes in", "saans lene me pasli chalna"])
            if chest_indrawing or (fast_breathing and spo2 is not None and spo2 < 92):
                detected_flags.append(
                    ClinicalFlag(
                        code="PED_SEVERE_PNEUMONIA",
                        category="PEDIATRIC",
                        description="Severe Pneumonia / Very Severe Disease (Chest indrawing or respiratory failure).",
                        severity=RiskLevel.HIGH,
                        snomed_code="233604007",
                        referral_urgency="IMMEDIATE_EMERGENCY",
                        action="URGENT REFERRAL to PHC. Give 1st dose of Oral Amoxicillin if referral will take > 2 hours. Keep child warm.",
                    )
                )
            elif fast_breathing:
                detected_flags.append(
                    ClinicalFlag(
                        code="PED_PNEUMONIA_FAST_BREATHING",
                        category="PEDIATRIC",
                        description=f"Fast breathing (RR {rr} breaths/min). Classified as Pneumonia without chest indrawing.",
                        severity=RiskLevel.MODERATE,
                        snomed_code="2014009",
                        referral_urgency="SAME_DAY",
                        action="Treat at Sub-centre/home with Oral Amoxicillin for 5 days. Re-assess in 2 days or immediately if danger signs develop.",
                    )
                )

            # High fever with rash
            if any(term in symptoms for term in ["rash", "red spots", "measles rash"]) and (
                (temp and temp >= 38.5) or any(term in symptoms for term in ["high fever", "tez bukhar"])
            ):
                detected_flags.append(
                    ClinicalFlag(
                        code="PED_FEVER_WITH_RASH",
                        category="PEDIATRIC",
                        description="High fever accompanied by generalized rash (Suspected Measles/viral exanthem).",
                        severity=RiskLevel.HIGH,
                        snomed_code="52254009",
                        referral_urgency="SAME_DAY",
                        action="Urgent PHC referral. Give Vitamin A dose immediately. Isolate child from other non-vaccinated infants.",
                    )
                )

        # ---------------------------------------------------------
        # 3. OVERALL RISK LEVEL DETERMINATION
        # ---------------------------------------------------------
        has_high = any(f.severity == RiskLevel.HIGH for f in detected_flags)
        has_mod = any(f.severity == RiskLevel.MODERATE for f in detected_flags)

        if has_high:
            overall_risk = RiskLevel.HIGH
            referral_facility = "First Referral Unit (FRU) / District Hospital"
            transport_mode = "108 Emergency Ambulance"
        elif has_mod:
            overall_risk = RiskLevel.MODERATE
            referral_facility = "Primary Health Centre (PHC) / Sub-Centre"
            transport_mode = "ASHA-accompanied or local transit"
        else:
            overall_risk = RiskLevel.LOW
            referral_facility = "Village Health Nutrition Day (VHND) / Sub-Centre"
            transport_mode = "Routine"

        instructions: List[str] = []
        for flag in detected_flags:
            instructions.append(f"[{flag.category} - {flag.severity.value}] {flag.description} -> {flag.action}")

        if not instructions:
            instructions.append("No immediate red flags detected. Continue routine preventive care and age-appropriate nutrition.")

        # Build FHIR R4 RiskAssessment resource
        now_iso = datetime.now(timezone.utc).isoformat()
        risk_id = f"risk-assessment-{uuid.uuid4().hex[:12]}"

        fhir_risk_assessment = {
            "resourceType": "RiskAssessment",
            "id": risk_id,
            "status": "final",
            "subject": {"reference": f"Patient/{patient_id}"},
            "occurrenceDateTime": now_iso,
            "condition": {
                "text": "Maternal / Pediatric Frontline Triage (NHM & IMNCI Protocol)"
            },
            "prediction": [
                {
                    "outcome": {
                        "text": f"Triage Risk Level: {overall_risk.value}",
                        "coding": [
                            {
                                "system": "https://nhm.gov.in/clinical-risk-level",
                                "code": overall_risk.value,
                                "display": f"{overall_risk.value} Clinical Risk",
                            }
                        ],
                    },
                    "qualitativeRisk": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/risk-probability",
                                "code": "high" if overall_risk == RiskLevel.HIGH else ("moderate" if overall_risk == RiskLevel.MODERATE else "low"),
                                "display": overall_risk.value.capitalize(),
                            }
                        ]
                    },
                    "rationale": "Evaluated against NHM ASHA Module 6/7, IMNCI algorithms, and maternal/neonatal danger sign checklists.",
                }
            ],
            "mitigation": (
                f"Referral Facility: {referral_facility}. Transport: {transport_mode}. "
                f"Key Action: {detected_flags[0].action if detected_flags else 'Continue routine village visits.'}"
            ),
            "note": [
                {"text": instr} for instr in instructions
            ],
        }

        if encounter_id:
            fhir_risk_assessment["encounter"] = {"reference": f"Encounter/{encounter_id}"}

        return TriageEvaluationResult(
            risk_level=overall_risk,
            flags=detected_flags,
            referral_facility=referral_facility,
            transport_mode=transport_mode,
            explicit_referral_instructions=instructions,
            clinical_summary=(
                f"Evaluated patient {patient_id}. Overall Risk: {overall_risk.value}. "
                f"{len(detected_flags)} danger sign(s) triggered."
            ),
            fhir_risk_assessment=fhir_risk_assessment,
        )
