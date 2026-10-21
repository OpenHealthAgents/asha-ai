"""
Comprehensive test verification for GraphQL Offline Field Sync Mutation
and Village Care Gaps Query in bezs-emr-gql.
"""

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.graphql.schema import schema


async def run_tests():
    print("==================================================================")
    print("  Testing bezs-emr-gql Strawberry GraphQL Schema & Resolvers      ")
    print("==================================================================")

    # 1. Test Query: getVillageCareGaps
    print("\n--- 1. Testing Query: getVillageCareGaps ---")
    query_care_gaps = """
    query GetCareGaps($lgdCode: String!) {
        getVillageCareGaps(villageLgdCode: $lgdCode) {
            villageLgdCode
            villageName
            totalCareGaps
            overdueImmunizations {
                patientId
                patientName
                vaccineCode
                vaccineName
                dueDate
                daysOverdue
                contactPhone
            }
            missedAncVisits {
                patientId
                patientName
                gestationalAgeWeeks
                expectedVisitTrimester
                dueDate
                isHighRisk
                highRiskReasons
            }
            pendingNcdScreenings {
                patientId
                patientName
                age
                lastCbacDate
                lastCbacScore
                screeningStatus
            }
        }
    }
    """
    result = await schema.execute(query_care_gaps, variable_values={"lgdCode": "215432"})
    assert result.errors is None, f"Query errors: {result.errors}"
    assert result.data is not None
    summary = result.data["getVillageCareGaps"]
    print(f"[OK] Village: {summary['villageName']} (LGD: {summary['villageLgdCode']})")
    print(f"[OK] Total Care Gaps: {summary['totalCareGaps']}")
    print(f"[OK] Overdue Immunizations count: {len(summary['overdueImmunizations'])}")
    print(f"[OK] Missed ANC Visits count: {len(summary['missedAncVisits'])}")
    print(f"[OK] Pending NCD Screenings count: {len(summary['pendingNcdScreenings'])}")

    # 2. Test Batch Mutation: syncOfflineFieldVisits
    print("\n--- 2. Testing Mutation: syncOfflineFieldVisits ---")
    mutation_sync = """
    mutation SyncFieldVisits($visits: [OfflineVisitInput!]!) {
        syncOfflineFieldVisits(visits: $visits) {
            syncedCount
            conflictedCount
            failedCount
            results {
                visitUuid
                status
                encounterId
                createdResources
                conflictDetails
                errorMessage
                processedAt
            }
        }
    }
    """

    test_visits = [
        {
            "visitUuid": "v-uuid-asha-001",
            "clientTimestamp": "2026-10-21T08:30:00Z",
            "workerId": "usr-asha-sunita",
            "patientId": "patient-asha-baby-aarav",
            "villageLgdCode": "215432",
            "visitType": "IMMUNIZATION",
            "immunizationsGiven": ["PENTA-1", "ROTA-1"],
            "observations": [
                {
                    "code": "weight",
                    "display": "Body Weight",
                    "valueQuantity": 5.4,
                    "unit": "kg",
                    "loincCode": "29463-7",
                }
            ],
            "referralNeeded": False,
        },
        {
            "visitUuid": "v-uuid-asha-002",
            "clientTimestamp": "2026-10-20T14:15:00Z",
            "workerId": "usr-asha-sunita",
            "patientId": "patient-asha-anita-patra",
            "villageLgdCode": "215432",
            "visitType": "ANC",
            "observations": [
                {
                    "code": "bp-systolic",
                    "display": "Systolic Blood Pressure",
                    "valueQuantity": 150.0,
                    "unit": "mmHg",
                    "loincCode": "8480-6",
                },
                {
                    "code": "bp-diastolic",
                    "display": "Diastolic Blood Pressure",
                    "valueQuantity": 98.0,
                    "unit": "mmHg",
                    "loincCode": "8462-4",
                },
            ],
            "questionnaireResponse": {
                "questionnaireUrl": "https://nhm.gov.in/fhir/r4/Questionnaire/ANC-HighRisk-v1",
                "status": "completed",
                "items": [
                    {"linkId": "anc-gestational-weeks", "valueInteger": 32},
                    {"linkId": "anc-pre-eclampsia", "valueBoolean": True},
                    {"linkId": "anc-severe-anemia", "valueBoolean": True},
                ],
            },
            "referralNeeded": True,
            "referralReason": "Severe pre-eclampsia and severe maternal anemia (Hb 6.8 g/dL)",
            "referralUrgency": "EMERGENCY",
            "notes": "Emergency escort arranged via 108 ambulance to Bhadrak PHC.",
        },
    ]

    sync_result = await schema.execute(mutation_sync, variable_values={"visits": test_visits})
    assert sync_result.errors is None, f"Mutation errors: {sync_result.errors}"
    assert sync_result.data is not None
    payload = sync_result.data["syncOfflineFieldVisits"]
    print(f"[OK] Synced Count: {payload['syncedCount']}")
    print(f"[OK] Conflicted Count: {payload['conflictedCount']}")
    print(f"[OK] Failed Count: {payload['failedCount']}")
    for res in payload["results"]:
        print(f"  - Visit [{res['visitUuid']}] -> Status: {res['status']}, Encounter: {res['encounterId']}")
        print(f"    Created FHIR Resources: {', '.join(res['createdResources'])}")

    # 3. Test Idempotency (Re-sync same batch)
    print("\n--- 3. Testing Idempotency on duplicate sync ---")
    resync_result = await schema.execute(mutation_sync, variable_values={"visits": [test_visits[0]]})
    assert resync_result.errors is None
    resync_payload = resync_result.data["syncOfflineFieldVisits"]
    first_res = resync_payload["results"][0]
    print(f"[OK] Duplicate Resync Status: {first_res['status']} ({first_res['conflictDetails']})")
    assert first_res["status"] == "SKIPPED_DUPLICATE"

    # 4. Test Retrospective Conflict Resolution (Earlier timestamp on already updated patient)
    print("\n--- 4. Testing Retrospective Timestamp Conflict Resolution ---")
    retrospective_visit = {
        "visitUuid": "v-uuid-asha-003",
        "clientTimestamp": "2026-10-18T10:00:00Z",  # 2 days earlier than latest recorded visit on Anita Patra
        "workerId": "usr-asha-sunita",
        "patientId": "patient-asha-anita-patra",
        "villageLgdCode": "215432",
        "visitType": "ROUTINE",
        "referralNeeded": False,
    }
    retro_result = await schema.execute(mutation_sync, variable_values={"visits": [retrospective_visit]})
    assert retro_result.errors is None
    retro_payload = retro_result.data["syncOfflineFieldVisits"]
    retro_res = retro_payload["results"][0]
    print(f"[OK] Retrospective Conflict Status: {retro_res['status']}")
    print(f"  Conflict Details: {retro_res['conflictDetails']}")
    assert retro_res["status"] == "CONFLICT_RESOLVED"

    print("\n==================================================================")
    print("  [OK] ALL GRAPHQL SCHEMAS, MUTATIONS & RESOLVERS VERIFIED CLEANLY! ")
    print("==================================================================")


if __name__ == "__main__":
    asyncio.run(run_tests())
