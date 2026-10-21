"""
Transformer service: Converts Normalized Point-of-Care Wearable/Kit payloads
into standardized HL7 FHIR R4 Observation resources (with standard LOINC codes)
and pushes them to the bezs-emr-gql service gateway.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import httpx
import uuid

from app.schemas.providers.point_of_care import (
    ClinicalRiskSeverity,
    NormalizedPointOfCarePayload,
    NormalizedVitalMetric,
)

BEZS_EMR_GQL_URL = "http://localhost:8000/graphql"


class FhirObservationTransformer:
    """
    Transforms point-of-care screening kit metrics into standard FHIR R4 Observations:
    - Systolic BP: LOINC 8480-6
    - Diastolic BP: LOINC 8462-4
    - BP Panel: LOINC 85354-9
    - Pulse: LOINC 8867-4
    - SpO2: LOINC 59408-5
    - Blood Glucose: LOINC 2339-0
    - Hemoglobin: LOINC 718-7
    - Body Temperature: LOINC 8310-5
    - Fetal Heart Rate: LOINC 55283-6
    """

    @classmethod
    def transform_to_fhir_observations(cls, payload: NormalizedPointOfCarePayload) -> List[Dict[str, Any]]:
        observations: List[Dict[str, Any]] = []
        ctx = payload.context

        interpretation_map = {
            ClinicalRiskSeverity.NORMAL: {"code": "N", "display": "Normal"},
            ClinicalRiskSeverity.WARNING: {"code": "A", "display": "Abnormal"},
            ClinicalRiskSeverity.CRITICAL_ALERT: {"code": "HH", "display": "Critical High / Alert"},
        }

        # Check for Blood Pressure to create standard BP Panel Observation (LOINC 85354-9)
        sys_metric = next((m for m in payload.metrics if m.loinc_code == "8480-6"), None)
        dia_metric = next((m for m in payload.metrics if m.loinc_code == "8462-4"), None)

        if sys_metric and dia_metric:
            bp_obs_id = f"obs-bp-{uuid.uuid4().hex[:12]}"
            bp_status = sys_metric.clinical_status if sys_metric.clinical_status != ClinicalRiskSeverity.NORMAL else dia_metric.clinical_status
            interp = interpretation_map[bp_status]

            bp_panel = {
                "resourceType": "Observation",
                "id": bp_obs_id,
                "status": "final",
                "category": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                "code": "vital-signs",
                                "display": "Vital Signs",
                            }
                        ]
                    }
                ],
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "85354-9",
                            "display": "Blood pressure panel with all children optional",
                        }
                    ]
                },
                "subject": {"reference": f"Patient/{ctx.patient_id}"},
                "performer": [{"reference": f"Practitioner/{ctx.worker_id}"}],
                "effectiveDateTime": ctx.recorded_at,
                "interpretation": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                                "code": interp["code"],
                                "display": interp["display"],
                            }
                        ]
                    }
                ],
                "component": [
                    {
                        "code": {
                            "coding": [
                                {
                                    "system": "http://loinc.org",
                                    "code": "8480-6",
                                    "display": "Systolic blood pressure",
                                }
                            ]
                        },
                        "valueQuantity": {
                            "value": sys_metric.value,
                            "unit": "mmHg",
                            "system": "http://unitsofmeasure.org",
                            "code": "mm[Hg]",
                        },
                    },
                    {
                        "code": {
                            "coding": [
                                {
                                    "system": "http://loinc.org",
                                    "code": "8462-4",
                                    "display": "Diastolic blood pressure",
                                }
                            ]
                        },
                        "valueQuantity": {
                            "value": dia_metric.value,
                            "unit": "mmHg",
                            "system": "http://unitsofmeasure.org",
                            "code": "mm[Hg]",
                        },
                    },
                ],
                "extension": [
                    {
                        "url": "https://nrces.in/ndhm/fhir/r4/StructureDefinition/LgdHierarchy",
                        "extension": [
                            {"url": "village_lgd_code", "valueString": ctx.village_lgd_code},
                            {"url": "visit_uuid", "valueString": ctx.visit_uuid},
                        ],
                    }
                ],
            }
            if sys_metric.alert_message:
                bp_panel["note"] = [{"text": sys_metric.alert_message}]
            observations.append(bp_panel)

        # Transform all other individual metrics (SpO2, Glucose, Hemoglobin, Temp, Fetal Heart Rate)
        for metric in payload.metrics:
            if metric.loinc_code in ("8480-6", "8462-4"):
                continue  # Already represented in BP panel

            obs_id = f"obs-{uuid.uuid4().hex[:12]}"
            interp = interpretation_map[metric.clinical_status]

            # Resolve UCUM code
            ucum_map = {
                "%": "%",
                "mg/dL": "mg/dL",
                "g/dL": "g/dL",
                "Cel": "Cel",
                "/min": "/min",
            }
            ucum_code = ucum_map.get(metric.unit, metric.unit)

            obs = {
                "resourceType": "Observation",
                "id": obs_id,
                "status": "final",
                "category": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                "code": "vital-signs" if metric.loinc_code != "718-7" else "laboratory",
                                "display": "Vital Signs" if metric.loinc_code != "718-7" else "Laboratory",
                            }
                        ]
                    }
                ],
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": metric.loinc_code,
                            "display": metric.metric_name,
                        }
                    ]
                },
                "subject": {"reference": f"Patient/{ctx.patient_id}"},
                "performer": [{"reference": f"Practitioner/{ctx.worker_id}"}],
                "effectiveDateTime": ctx.recorded_at,
                "valueQuantity": {
                    "value": metric.value,
                    "unit": metric.unit,
                    "system": "http://unitsofmeasure.org",
                    "code": ucum_code,
                },
                "interpretation": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                                "code": interp["code"],
                                "display": interp["display"],
                            }
                        ]
                    }
                ],
                "extension": [
                    {
                        "url": "https://nrces.in/ndhm/fhir/r4/StructureDefinition/LgdHierarchy",
                        "extension": [
                            {"url": "village_lgd_code", "valueString": ctx.village_lgd_code},
                            {"url": "visit_uuid", "valueString": ctx.visit_uuid},
                        ],
                    }
                ],
            }
            if metric.alert_message:
                obs["note"] = [{"text": metric.alert_message}]

            observations.append(obs)

        return observations

    @classmethod
    async def push_to_bezs_emr_gql(
        cls,
        payload: NormalizedPointOfCarePayload,
        graphql_endpoint: str = BEZS_EMR_GQL_URL,
    ) -> Dict[str, Any]:
        """
        Pushes normalized screening kit observations to bezs-emr-gql
        using the syncOfflineFieldVisits GraphQL mutation.
        """
        ctx = payload.context

        obs_inputs = [
            {
                "code": m.metric_name.lower().replace(" ", "-"),
                "display": m.metric_name,
                "valueQuantity": m.value,
                "unit": m.unit,
                "loincCode": m.loinc_code,
            }
            for m in payload.metrics
        ]

        mutation = """
        mutation SyncPointOfCareReadings($visits: [OfflineVisitInput!]!) {
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
                }
            }
        }
        """

        visit_input = {
            "visitUuid": ctx.visit_uuid,
            "clientTimestamp": ctx.recorded_at,
            "workerId": ctx.worker_id,
            "patientId": ctx.patient_id,
            "villageLgdCode": ctx.village_lgd_code,
            "visitType": "ANC" if ctx.is_maternal else "ROUTINE",
            "observations": obs_inputs,
            "referralNeeded": payload.requires_emergency_referral,
            "referralReason": payload.referral_recommendation,
            "referralUrgency": "EMERGENCY" if payload.overall_clinical_risk == ClinicalRiskSeverity.CRITICAL_ALERT else "ROUTINE",
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(
                    graphql_endpoint,
                    json={
                        "query": mutation,
                        "variables": {"visits": [visit_input]},
                    },
                )
                if response.status_code == 200:
                    return response.json()
                return {
                    "error": f"HTTP {response.status_code}",
                    "details": response.text,
                    "offline_buffered": True,
                }
            except Exception as exc:
                # In offline field mode, client buffers locally
                return {
                    "status": "OFFLINE_BUFFERED",
                    "message": f"EMR GraphQL endpoint unreachable ({str(exc)}). Buffered for next online sync.",
                    "offline_buffered": True,
                }
