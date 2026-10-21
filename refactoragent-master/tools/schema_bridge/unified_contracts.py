"""
Unified Shared Contracts and Clinical Data Transfer Objects (DTOs)
Bridging: bezs-iam, bezs-emr-gql, langcare-mcp-fhir, bezs-filenest, bezs-hms, and bezs-observability.
Compliant with National Health Mission (NHM), ABDM, HL7 FHIR R4, LOINC, and SNOMED-CT standards.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Dict, Any, Optional
import datetime
import hashlib
import json


class UserRole(str, Enum):
    ROLE_ASHA = "ROLE_ASHA"
    ROLE_ANM = "ROLE_ANM"
    ROLE_PHC_MO = "ROLE_PHC_MO"
    ROLE_ADMIN = "ROLE_ADMIN"


class TriageRiskLevel(str, Enum):
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"


class CareGapUrgency(str, Enum):
    CRITICAL = "CRITICAL"
    URGENT = "URGENT"
    ROUTINE = "ROUTINE"


class StandardLOINC:
    SYSTOLIC_BP = "8480-6"
    DIASTOLIC_BP = "8462-4"
    SPO2 = "59408-5"
    BLOOD_GLUCOSE = "2339-0"
    HEMOGLOBIN = "718-7"
    BODY_TEMP = "8310-5"
    FETAL_HEART_RATE = "55283-6"


class StandardSNOMED:
    PRE_ECLAMPSIA = "398254007"
    SEVERE_ANEMIA = "199004008"
    PEDIATRIC_PNEUMONIA = "195893006"
    DEHYDRATION = "409940001"
    NORMAL_PREGNANCY = "77386006"
    MALNUTRITION = "713454000"


@dataclass
class FrontlineWorkerProfile:
    worker_id: str
    username: str
    role: UserRole
    state_code: str
    district_code: str
    block_code: str
    phc_id: str
    subcentre_id: str
    village_lgd_code: str
    hpr_id: Optional[str] = None


@dataclass
class ObservationDTO:
    code: str
    display: str
    value: float
    unit: str
    interpretation: str  # "NORMAL", "HIGH", "CRITICAL_HIGH", "LOW"
    recorded_at: str
    device_id: Optional[str] = None

    def to_fhir_observation(self, patient_id: str) -> Dict[str, Any]:
        return {
            "resourceType": "Observation",
            "status": "final",
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": self.code,
                    "display": self.display
                }]
            },
            "subject": {"reference": f"Patient/{patient_id}"},
            "effectiveDateTime": self.recorded_at,
            "valueQuantity": {
                "value": self.value,
                "unit": self.unit,
                "system": "http://unitsofmeasure.org"
            },
            "interpretation": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                    "code": self.interpretation
                }]
            }]
        }


@dataclass
class CareGapDTO:
    beneficiary_id: str
    beneficiary_name: str
    gap_type: str  # "IMMUNIZATION", "ANC_CHECKUP", "NCD_SCREENING"
    description: str
    overdue_days: int
    urgency: CareGapUrgency


@dataclass
class RiskAssessmentDTO:
    risk_level: TriageRiskLevel
    red_flags: List[str]
    referral_urgency: str
    referral_facility: str
    counseling_script: str
    recommended_actions: List[str] = field(default_factory=list)


@dataclass
class RuralVisitPayloadDTO:
    visit_id: str
    household_group_id: str
    beneficiary_id: str
    beneficiary_name: str
    worker_id: str
    village_lgd_code: str
    audio_storage_url: str
    audio_sha256: str
    transcript: str
    language: str
    vitals: List[ObservationDTO]
    risk_assessment: RiskAssessmentDTO
    care_gaps: List[CareGapDTO]
    asha_override_status: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())


@dataclass
class PHCReferralTicketDTO:
    ticket_id: str
    patient_id: str
    patient_name: str
    abha_id: Optional[str]
    asha_worker_id: str
    phc_id: str
    village_lgd_code: str
    priority: str
    clinical_summary: str
    audio_clip_url: str
    vitals_summary: Dict[str, Any]
    status: str = "PENDING_DOCTOR_REVIEW"
    created_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())


@dataclass
class ClinicalAuditDTO:
    audit_id: str
    timestamp: str
    patient_id: str
    worker_id: str
    input_audio_hash: str
    transcript: str
    mcp_rule_triggered: str
    asha_override_status: str
    cryptographic_signature: str

    @classmethod
    def create(
        cls,
        audit_id: str,
        patient_id: str,
        worker_id: str,
        input_audio_hash: str,
        transcript: str,
        mcp_rule_triggered: str,
        asha_override_status: str = "NONE",
    ) -> "ClinicalAuditDTO":
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
        raw_to_sign = f"{audit_id}|{ts}|{patient_id}|{worker_id}|{input_audio_hash}|{mcp_rule_triggered}|{asha_override_status}"
        sig = hashlib.sha256(raw_to_sign.encode("utf-8")).hexdigest()
        return cls(
            audit_id=audit_id,
            timestamp=ts,
            patient_id=patient_id,
            worker_id=worker_id,
            input_audio_hash=input_audio_hash,
            transcript=transcript,
            mcp_rule_triggered=mcp_rule_triggered,
            asha_override_status=asha_override_status,
            cryptographic_signature=sig,
        )
