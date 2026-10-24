"""
Strawberry GraphQL types for Offline Field Sync and Rural Village Care Gaps.
"""

from typing import List, Optional
import strawberry


@strawberry.input
class OfflineObservationInput:
    code: str
    display: str
    value_quantity: Optional[float] = None
    unit: Optional[str] = None
    value_string: Optional[str] = None
    value_boolean: Optional[bool] = None
    loinc_code: Optional[str] = None


@strawberry.input
class QuestionnaireItemAnswerInput:
    link_id: str
    text: Optional[str] = None
    value_string: Optional[str] = None
    value_boolean: Optional[bool] = None
    value_integer: Optional[int] = None
    value_decimal: Optional[float] = None
    value_date: Optional[str] = None


@strawberry.input
class OfflineQuestionnaireResponseInput:
    questionnaire_url: str
    status: str = "completed"
    items: List[QuestionnaireItemAnswerInput]


@strawberry.input
class OfflineVisitInput:
    visit_uuid: str  # Client-generated UUID serving as Idempotency Key
    client_timestamp: str  # ISO 8601 offline capture timestamp on mobile
    worker_id: str  # ASHA or ANM user id
    patient_id: str  # FHIR Patient id
    village_lgd_code: str
    visit_type: str  # "ANC" | "PNC" | "IMMUNIZATION" | "CBAC_NCD" | "IMNCI_PEDIATRIC" | "ROUTINE"
    household_id: Optional[str] = None
    observations: Optional[List[OfflineObservationInput]] = None
    questionnaire_response: Optional[OfflineQuestionnaireResponseInput] = None
    immunizations_given: Optional[List[str]] = None  # Vaccine codes (e.g. "BCG", "PENTA-1")
    referral_needed: bool = False
    referral_reason: Optional[str] = None
    referral_urgency: Optional[str] = "ROUTINE"  # "ROUTINE" | "URGENT" | "EMERGENCY"
    notes: Optional[str] = None


@strawberry.type
class SyncVisitResult:
    visit_uuid: str
    status: str  # "SUCCESS" | "CONFLICT_RESOLVED" | "SKIPPED_DUPLICATE" | "FAILED"
    encounter_id: Optional[str] = None
    created_resources: List[str] = strawberry.field(default_factory=list)
    conflict_details: Optional[str] = None
    error_message: Optional[str] = None
    processed_at: str = ""


@strawberry.type
class SyncBatchPayload:
    synced_count: int
    conflicted_count: int
    failed_count: int
    results: List[SyncVisitResult]


@strawberry.type
class OverdueImmunizationGap:
    patient_id: str
    patient_name: str
    vaccine_code: str
    vaccine_name: str
    due_date: str
    days_overdue: int
    contact_phone: Optional[str] = None
    household_address: Optional[str] = None


@strawberry.type
class MissedAncGap:
    patient_id: str
    patient_name: str
    gestational_age_weeks: int
    expected_visit_trimester: str
    due_date: str
    is_high_risk: bool
    high_risk_reasons: List[str]
    contact_phone: Optional[str] = None
    anc_visit_number: Optional[int] = 1
    expected_gestational_week: Optional[int] = 12
    weeks_overdue: Optional[int] = 4


@strawberry.type
class PendingNcdScreeningGap:
    patient_id: str
    patient_name: str
    age: int
    last_cbac_date: Optional[str] = None
    last_cbac_score: Optional[int] = None
    screening_status: str  # "NEVER_SCREENED" | "ANNUAL_RESUMPTION_DUE" | "HIGH_RISK_FOLLOWUP_OVERDUE"
    household_address: Optional[str] = None
    age_years: Optional[int] = 45
    screening_type: Optional[str] = "CBAC_HYPERTENSION_DIABETES"


@strawberry.type
class CareGapSummary:
    village_lgd_code: str
    village_name: str
    total_care_gaps: int
    overdue_immunizations: List[OverdueImmunizationGap]
    missed_anc_visits: List[MissedAncGap]
    pending_ncd_screenings: List[PendingNcdScreeningGap]
    total_overdue_count: Optional[int] = 0
