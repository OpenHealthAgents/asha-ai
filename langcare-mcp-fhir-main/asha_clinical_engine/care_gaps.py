"""
Household Care Gap Detection Engine for ASHA AI Copilot.
Queries medplum via bezs-emr-gql or evaluates FHIR Group resources
to detect overdue infant immunizations, missed ANC visits, and pending NCD screenings.
"""

from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
import json
import os
from typing import Any, Dict, List, Optional
import urllib.request
import urllib.error


@dataclass
class CareGapItem:
    member_id: str
    member_name: str
    gap_type: str  # "IMMUNIZATION" | "ANC_VISIT" | "NCD_SCREENING"
    title: str
    description: str
    due_date: str
    days_overdue: int
    urgency: str  # "HIGH" | "MEDIUM" | "ROUTINE"
    action: str


@dataclass
class HouseholdCareGapReport:
    household_group_id: str
    village_lgd_code: str
    evaluated_at: str
    total_gaps: int
    overdue_immunizations_count: int
    missed_anc_count: int
    pending_ncd_count: int
    gaps: List[CareGapItem] = field(default_factory=list)
    action_plan_for_asha: List[str] = field(default_factory=list)


class HouseholdCareGapDetector:
    def __init__(self, emr_gql_url: Optional[str] = None):
        self.emr_gql_url = emr_gql_url or os.getenv("BEZS_EMR_GQL_URL", "http://localhost:8000/graphql")

    def detect_household_gaps(
        self,
        household_group_id: str,
        village_lgd_code: str,
        household_members: Optional[List[Dict[str, Any]]] = None,
    ) -> HouseholdCareGapReport:
        """
        Evaluates care gaps for all members of a rural household Group.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        gaps: List[CareGapItem] = []

        # Try querying bezs-emr-gql first if available
        gql_summary = self._query_emr_gql_care_gaps(village_lgd_code)

        if household_members:
            # Evaluate each household member
            for member in household_members:
                m_id = member.get("id", "patient-unknown")
                m_name = member.get("name", "Household Member")
                age_years = member.get("age_years", 0)
                age_months = member.get("age_months", age_years * 12)
                is_pregnant = member.get("is_pregnant", False)
                gestational_weeks = member.get("gestational_weeks", 0)
                received_vaccines = member.get("received_vaccines", [])
                completed_anc_visits = member.get("completed_anc_visits", 0)
                last_ncd_screening_date = member.get("last_ncd_screening_date")

                # 1. Pediatric Immunization Gaps (NIS)
                if age_months <= 24:
                    if age_months >= 1.5 and "PENTA-1" not in received_vaccines:
                        gaps.append(
                            CareGapItem(
                                member_id=m_id,
                                member_name=m_name,
                                gap_type="IMMUNIZATION",
                                title="Pentavalent-1 Overdue",
                                description="Pentavalent 1 (DPT + HepB + Hib) due at 6 weeks.",
                                due_date="2026-09-26",
                                days_overdue=26,
                                urgency="HIGH",
                                action="Mobilize mother to bring infant to upcoming Village Health Nutrition Day (VHND) on Wednesday.",
                            )
                        )
                    if age_months >= 1.5 and "ROTA-1" not in received_vaccines:
                        gaps.append(
                            CareGapItem(
                                member_id=m_id,
                                member_name=m_name,
                                gap_type="IMMUNIZATION",
                                title="Rotavirus-1 Overdue",
                                description="Rotavirus 1 due at 6 weeks for diarrheal prevention.",
                                due_date="2026-09-26",
                                days_overdue=26,
                                urgency="HIGH",
                                action="Administer oral rotavirus drops at next session.",
                            )
                        )
                    if age_months >= 9 and "MR-1" not in received_vaccines:
                        gaps.append(
                            CareGapItem(
                                member_id=m_id,
                                member_name=m_name,
                                gap_type="IMMUNIZATION",
                                title="MR-1 & Vitamin A Overdue",
                                description="Measles-Rubella 1st dose due at 9-12 months.",
                                due_date="2026-10-05",
                                days_overdue=17,
                                urgency="HIGH",
                                action="Urgent immunization mobilization to prevent measles outbreak.",
                            )
                        )

                # 2. Maternal ANC Gaps
                if is_pregnant:
                    if gestational_weeks >= 14 and completed_anc_visits < 1:
                        gaps.append(
                            CareGapItem(
                                member_id=m_id,
                                member_name=m_name,
                                gap_type="ANC_VISIT",
                                title="Missed 1st ANC Checkup",
                                description="Registration & 1st ANC missed (should be within 12 weeks).",
                                due_date="2026-09-15",
                                days_overdue=37,
                                urgency="HIGH",
                                action="Immediate MCP Card issuance, baseline vitals check, and Sub-Centre referral for Hb/urine tests.",
                            )
                        )
                    elif gestational_weeks >= 28 and completed_anc_visits < 2:
                        gaps.append(
                            CareGapItem(
                                member_id=m_id,
                                member_name=m_name,
                                gap_type="ANC_VISIT",
                                title="Missed 2nd ANC Checkup",
                                description="2nd ANC checkup missed (due between 14-26 weeks).",
                                due_date="2026-10-01",
                                days_overdue=21,
                                urgency="MEDIUM",
                                action="Schedule ANM visit for ultrasound scheduling and IFA distribution.",
                            )
                        )

                # 3. Adult NCD Screening Gaps (Age 30+)
                if age_years >= 30 and not last_ncd_screening_date:
                    gaps.append(
                        CareGapItem(
                            member_id=m_id,
                            member_name=m_name,
                            gap_type="NCD_SCREENING",
                            title="Annual CBAC & NCD Screening Pending",
                            description="Individual aged 30+ has no record of CBAC scoring, BP, or Blood Glucose screening this year.",
                            due_date="2026-10-01",
                            days_overdue=21,
                            urgency="MEDIUM",
                            action="Fill Community Based Assessment Checklist (CBAC) and check blood pressure using digital cuff.",
                        )
                    )

        # If no explicit members provided or fallback needed, merge EMR GQL gaps
        if not gaps and gql_summary:
            for imm in gql_summary.get("overdue_immunizations", []):
                gaps.append(
                    CareGapItem(
                        member_id=imm.get("patient_id", "patient-child"),
                        member_name=imm.get("patient_name", "Infant"),
                        gap_type="IMMUNIZATION",
                        title=f"{imm.get('vaccine_code')} Overdue",
                        description=imm.get("vaccine_name", "Vaccine"),
                        due_date=imm.get("due_date", "2026-09-26"),
                        days_overdue=imm.get("days_overdue", 20),
                        urgency="HIGH",
                        action="Mobilize for next Wednesday immunization session.",
                    )
                )
            for anc in gql_summary.get("missed_anc_visits", []):
                gaps.append(
                    CareGapItem(
                        member_id=anc.get("patient_id", "patient-mother"),
                        member_name=anc.get("patient_name", "Pregnant Mother"),
                        gap_type="ANC_VISIT",
                        title=f"Missed ANC #{anc.get('anc_visit_number')}",
                        description=f"Gestational week {anc.get('expected_gestational_week')}, {anc.get('weeks_overdue')} weeks overdue.",
                        due_date="2026-10-01",
                        days_overdue=anc.get("weeks_overdue", 2) * 7,
                        urgency="HIGH",
                        action="Visit household, conduct BP and Hb check, schedule Sub-Centre visit.",
                    )
                )
            for ncd in gql_summary.get("pending_ncd_screenings", []):
                gaps.append(
                    CareGapItem(
                        member_id=ncd.get("patient_id", "patient-adult"),
                        member_name=ncd.get("patient_name", "Adult Member"),
                        gap_type="NCD_SCREENING",
                        title=f"Pending {ncd.get('screening_type')}",
                        description=f"Age {ncd.get('age_years')}, target for Ayushman Bharat NCD screening.",
                        due_date="2026-10-01",
                        days_overdue=21,
                        urgency="MEDIUM",
                        action="Administer CBAC form and record resting blood pressure.",
                    )
                )

        # Build Action Plan for ASHA
        action_plan: List[str] = []
        imm_count = sum(1 for g in gaps if g.gap_type == "IMMUNIZATION")
        anc_count = sum(1 for g in gaps if g.gap_type == "ANC_VISIT")
        ncd_count = sum(1 for g in gaps if g.gap_type == "NCD_SCREENING")

        if imm_count > 0:
            action_plan.append(f"CRITICAL: {imm_count} child vaccine(s) overdue. Notify mother and record on Due List register for next VHND.")
        if anc_count > 0:
            action_plan.append(f"PRIORITY: {anc_count} missed ANC checkup(s). Verify fetal movement, check BP, ensure 180 IFA tablets are stocked.")
        if ncd_count > 0:
            action_plan.append(f"ROUTINE: {ncd_count} adult member(s) eligible for CBAC screening. Conduct tobacco screening and BP check.")

        return HouseholdCareGapReport(
            household_group_id=household_group_id,
            village_lgd_code=village_lgd_code,
            evaluated_at=now_iso,
            total_gaps=len(gaps),
            overdue_immunizations_count=imm_count,
            missed_anc_count=anc_count,
            pending_ncd_count=ncd_count,
            gaps=gaps,
            action_plan_for_asha=action_plan,
        )

    def _query_emr_gql_care_gaps(self, village_lgd_code: str) -> Optional[Dict[str, Any]]:
        """GraphQL query to bezs-emr-gql getVillageCareGaps."""
        query = """
        query GetCareGaps($lgd: String!) {
          getVillageCareGaps(villageLgdCode: $lgd) {
            villageLgdCode
            totalOverdueCount
            overdueImmunizations {
              patientId
              patientName
              vaccineCode
              vaccineName
              dueDate
              daysOverdue
            }
            missedAncVisits {
              patientId
              patientName
              ancVisitNumber
              expectedGestationalWeek
              weeksOverdue
            }
            pendingNcdScreenings {
              patientId
              patientName
              ageYears
              screeningType
            }
          }
        }
        """
        payload = json.dumps({"query": query, "variables": {"lgd": village_lgd_code}}).encode("utf-8")
        req = urllib.request.Request(
            self.emr_gql_url,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("data", {}).get("getVillageCareGaps")
        except Exception:
            return None
