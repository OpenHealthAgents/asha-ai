"""
API Route for Frontline Rural Point-of-Care (PoC) Device Ingestion & FHIR Transformer.
"""

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, status

from app.schemas.providers.point_of_care import (
    NormalizedPointOfCarePayload,
    PointOfCareIngestRequest,
)
from app.services.fhir_observation_transformer import FhirObservationTransformer
from app.services.point_of_care_adapter import PointOfCareAdapter

router = APIRouter(prefix="/point-of-care", tags=["External: Point-of-Care Devices"])


@router.post("/ingest", response_model=NormalizedPointOfCarePayload, status_code=status.HTTP_200_OK)
async def ingest_device_reading(payload: PointOfCareIngestRequest) -> NormalizedPointOfCarePayload:
    """
    Ingests and normalizes raw telemetry from low-cost Bluetooth point-of-care kits:
    - Digital BP cuffs
    - Pulse oximeters
    - Glucometers
    - Digital hemoglobinometers
    - Smart thermometers
    - Handheld fetal Dopplers
    """
    try:
        return PointOfCareAdapter.normalize_ingest_request(payload)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/transform-and-push", status_code=status.HTTP_200_OK)
async def transform_and_push_to_fhir(payload: PointOfCareIngestRequest) -> Dict[str, Any]:
    """
    Normalizes point-of-care kit readings, transforms them into standard HL7 FHIR R4
    Observation resources with standard LOINC codes (BP 85354-9, SpO2 59408-5, Glucose 2339-0,
    Hemoglobin 718-7, Temp 8310-5), and pushes them to `bezs-emr-gql`.
    """
    normalized = PointOfCareAdapter.normalize_ingest_request(payload)
    fhir_observations = FhirObservationTransformer.transform_to_fhir_observations(normalized)

    # Push to bezs-emr-gql
    push_result = await FhirObservationTransformer.push_to_bezs_emr_gql(normalized)

    return {
        "status": "PROCESSED",
        "ingest_id": normalized.ingest_id,
        "overall_clinical_risk": normalized.overall_clinical_risk,
        "requires_emergency_referral": normalized.requires_emergency_referral,
        "referral_recommendation": normalized.referral_recommendation,
        "fhir_observations_generated": len(fhir_observations),
        "fhir_observations": fhir_observations,
        "bezs_emr_gql_sync_result": push_result,
    }


@router.get("/supported-kits", status_code=status.HTTP_200_OK)
async def get_supported_kits() -> Dict[str, Any]:
    """
    Returns the supported field screening kits, BLE GATT specifications,
    and LOINC clinical code mappings for rural frontline health workflows.
    """
    return {
        "kits": [
            {
                "category": "Blood Pressure Monitor",
                "device_type": "bluetooth_bp_cuff",
                "ble_gatt_service": "0x1810",
                "ble_gatt_characteristic": "0x2A35",
                "loinc_codes": ["8480-6 (Systolic)", "8462-4 (Diastolic)", "85354-9 (BP Panel)", "8867-4 (Pulse)"],
                "unit": "mmHg",
            },
            {
                "category": "Pulse Oximeter",
                "device_type": "pulse_oximeter",
                "ble_gatt_service": "0x1822",
                "ble_gatt_characteristic": "0x2A5F",
                "loinc_codes": ["59408-5 (SpO2)", "8867-4 (Pulse Rate)"],
                "unit": "%",
            },
            {
                "category": "Glucometer",
                "device_type": "glucometer",
                "ble_gatt_service": "0x1808",
                "ble_gatt_characteristic": "0x2A18",
                "loinc_codes": ["2339-0 (Blood Glucose)"],
                "unit": "mg/dL",
            },
            {
                "category": "Digital Hemoglobinometer",
                "device_type": "digital_hemoglobinometer",
                "loinc_codes": ["718-7 (Hemoglobin)"],
                "unit": "g/dL",
            },
            {
                "category": "Smart Thermometer",
                "device_type": "smart_thermometer",
                "ble_gatt_service": "0x1809",
                "ble_gatt_characteristic": "0x2A1C",
                "loinc_codes": ["8310-5 (Body Temperature)"],
                "unit": "Cel",
            },
            {
                "category": "Fetal Doppler",
                "device_type": "fetal_doppler",
                "loinc_codes": ["55283-6 (Fetal Heart Rate)"],
                "unit": "/min",
            },
        ]
    }
