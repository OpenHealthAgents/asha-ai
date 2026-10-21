"""
ASHA AI Copilot Clinical Intelligence Engine.
Core clinical decision support, ASR transcript entity extraction,
household care gap computation, and localized counseling generators.
"""

from .clinical_rules import ClinicalRuleEngine, RiskLevel, TriageEvaluationResult
from .transcript_extractor import TranscriptExtractor
from .care_gaps import HouseholdCareGapDetector, HouseholdCareGapReport
from .counseling_generator import LocalizedCounselingGenerator, LocalizedCounselingResponse
from .nhm_knowledge_base import (
    NHM_ASHA_MATERNAL_CHILD_HANDBOOK,
    IMNCI_PEDIATRIC_TRIAGE_PROTOCOL,
    ANC_HIGH_RISK_PREGNANCY_PROTOCOL,
    CBAC_NCD_SCREENING_GUIDELINE,
    NATIONAL_IMMUNIZATION_SCHEDULE,
)

__all__ = [
    "ClinicalRuleEngine",
    "RiskLevel",
    "TriageEvaluationResult",
    "TranscriptExtractor",
    "HouseholdCareGapDetector",
    "HouseholdCareGapReport",
    "LocalizedCounselingGenerator",
    "LocalizedCounselingResponse",
    "NHM_ASHA_MATERNAL_CHILD_HANDBOOK",
    "IMNCI_PEDIATRIC_TRIAGE_PROTOCOL",
    "ANC_HIGH_RISK_PREGNANCY_PROTOCOL",
    "CBAC_NCD_SCREENING_GUIDELINE",
    "NATIONAL_IMMUNIZATION_SCHEDULE",
]
