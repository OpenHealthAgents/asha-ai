"""
Integration tests for Open-Wearables Point-of-Care (PoC) Ingestion
and FHIR R4 Observation Transformer Service for Frontline Rural Screening Kits.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ.setdefault("SECRET_KEY", "open-wearables-poc-secret-key-32b!")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/openwearables")

from app.schemas.providers.point_of_care import (
    BloodPressureReading,
    ClinicalRiskSeverity,
    FieldDeviceType,
    FetalDopplerReading,
    GlucometerReading,
    HemoglobinometerReading,
    PointOfCareIngestRequest,
    PulseOximeterReading,
    ReadingContext,
    ThermometerReading,
)
from app.services.fhir_observation_transformer import FhirObservationTransformer
from app.services.point_of_care_adapter import PointOfCareAdapter


async def run_poc_tests():
    print("==================================================================")
    print("  Testing Open-Wearables PoC Kit Ingestion & FHIR Transformer     ")
    print("==================================================================")

    context = ReadingContext(
        worker_id="usr-asha-sunita",
        patient_id="patient-asha-anita-patra",
        visit_uuid="visit-uuid-poc-901",
        village_lgd_code="215432",
        recorded_at="2026-10-22T08:15:00Z",
        is_maternal=True,
        gestational_age_weeks=32,
    )

    # 1. Test Bluetooth BP Cuff Ingestion (Severe Pre-eclampsia Alert)
    print("\n--- 1. Testing Bluetooth BP Cuff (Pre-eclampsia Threshold) ---")
    bp_req = PointOfCareIngestRequest(
        device_type=FieldDeviceType.BLUETOOTH_BP,
        device_manufacturer="Omron Healthcare",
        device_model="HEM-7156T BLE",
        device_serial_number="OMR-BLE-99812",
        battery_level_percent=88,
        context=context,
        blood_pressure=BloodPressureReading(
            systolic_mmhg=152.0,
            diastolic_mmhg=96.0,
            pulse_bpm=84.0,
        ),
    )
    bp_norm = PointOfCareAdapter.normalize_ingest_request(bp_req)
    assert bp_norm.overall_clinical_risk in (ClinicalRiskSeverity.WARNING, ClinicalRiskSeverity.CRITICAL_ALERT)
    assert bp_norm.requires_emergency_referral is True
    print(f"[OK] BP Normalization: {bp_norm.metrics[0].value}/{bp_norm.metrics[1].value} mmHg")
    print(f"     Risk Status: {bp_norm.overall_clinical_risk}")
    print(f"     Alert: {bp_norm.metrics[0].alert_message}")

    # 2. Test Digital Hemoglobinometer (Severe Maternal Anemia LOINC 718-7)
    print("\n--- 2. Testing Digital Hemoglobinometer (Hb < 7.0 g/dL Alert) ---")
    hb_req = PointOfCareIngestRequest(
        device_type=FieldDeviceType.DIGITAL_HEMOGLOBINOMETER,
        device_manufacturer="TrueHb Point-of-Care",
        device_model="TrueHb Pro BLE",
        context=context,
        hemoglobinometer=HemoglobinometerReading(
            hemoglobin_g_dl=6.8,
            strip_lot_number="LOT-2026-OCT-44",
        ),
    )
    hb_norm = PointOfCareAdapter.normalize_ingest_request(hb_req)
    assert hb_norm.overall_clinical_risk == ClinicalRiskSeverity.CRITICAL_ALERT
    assert hb_norm.metrics[0].loinc_code == "718-7"
    assert hb_norm.requires_emergency_referral is True
    print(f"[OK] Hemoglobin: {hb_norm.metrics[0].value} g/dL (LOINC: {hb_norm.metrics[0].loinc_code})")
    print(f"     Clinical Status: {hb_norm.metrics[0].clinical_status}")
    print(f"     Alert: {hb_norm.metrics[0].alert_message}")

    # 3. Test Pulse Oximeter (Severe Hypoxemia Alert SpO2 < 90%)
    print("\n--- 3. Testing Pulse Oximeter (SpO2 LOINC 59408-5) ---")
    pox_req = PointOfCareIngestRequest(
        device_type=FieldDeviceType.PULSE_OXIMETER,
        device_manufacturer="Choicemmed",
        device_model="MD300C228 BLE",
        context=context,
        pulse_oximeter=PulseOximeterReading(
            spo2_percent=88.0,
            pulse_bpm=110.0,
        ),
    )
    pox_norm = PointOfCareAdapter.normalize_ingest_request(pox_req)
    assert pox_norm.overall_clinical_risk == ClinicalRiskSeverity.CRITICAL_ALERT
    assert pox_norm.metrics[0].loinc_code == "59408-5"
    print(f"[OK] SpO2: {pox_norm.metrics[0].value}% (LOINC: {pox_norm.metrics[0].loinc_code})")
    print(f"     Pulse: {pox_norm.metrics[1].value} bpm (LOINC: {pox_norm.metrics[1].loinc_code})")
    print(f"     Alert: {pox_norm.metrics[0].alert_message}")

    # 4. Test Smart Thermometer (Body Temp LOINC 8310-5)
    print("\n--- 4. Testing Smart Thermometer (High Grade Fever LOINC 8310-5) ---")
    temp_req = PointOfCareIngestRequest(
        device_type=FieldDeviceType.SMART_THERMOMETER,
        device_manufacturer="Beurer",
        device_model="FT95 Non-Contact BLE",
        context=context,
        thermometer=ThermometerReading(
            temperature_celsius=39.4,
            measurement_site="forehead_temporal",
        ),
    )
    temp_norm = PointOfCareAdapter.normalize_ingest_request(temp_req)
    assert temp_norm.metrics[0].loinc_code == "8310-5"
    assert temp_norm.overall_clinical_risk == ClinicalRiskSeverity.CRITICAL_ALERT
    print(f"[OK] Body Temp: {temp_norm.metrics[0].value} Cel (LOINC: {temp_norm.metrics[0].loinc_code})")

    # 5. Test Handheld Fetal Doppler (Fetal Heart Rate LOINC 55283-6)
    print("\n--- 5. Testing Handheld Fetal Doppler (Fetal Distress LOINC 55283-6) ---")
    fhr_req = PointOfCareIngestRequest(
        device_type=FieldDeviceType.FETAL_DOPPLER,
        device_manufacturer="Contec Medical",
        device_model="Baby Sound C BLE",
        context=context,
        fetal_doppler=FetalDopplerReading(
            fetal_heart_rate_bpm=102.0,  # Below normal 110-160 bpm
        ),
    )
    fhr_norm = PointOfCareAdapter.normalize_ingest_request(fhr_req)
    assert fhr_norm.metrics[0].loinc_code == "55283-6"
    assert fhr_norm.overall_clinical_risk == ClinicalRiskSeverity.CRITICAL_ALERT
    print(f"[OK] Fetal Heart Rate: {fhr_norm.metrics[0].value} bpm (LOINC: {fhr_norm.metrics[0].loinc_code})")
    print(f"     Alert: {fhr_norm.metrics[0].alert_message}")

    # 6. Test Multi-Device FHIR R4 Observation Transformation
    print("\n--- 6. Testing FHIR R4 Observation Transformer ---")
    multi_req = PointOfCareIngestRequest(
        device_type=FieldDeviceType.BLUETOOTH_BP,
        device_manufacturer="Integrated Frontline Screening Kit",
        context=context,
        blood_pressure=BloodPressureReading(systolic_mmhg=148.0, diastolic_mmhg=94.0, pulse_bpm=86.0),
        pulse_oximeter=PulseOximeterReading(spo2_percent=97.0, pulse_bpm=86.0),
        hemoglobinometer=HemoglobinometerReading(hemoglobin_g_dl=6.8),
        thermometer=ThermometerReading(temperature_celsius=37.1),
    )
    multi_norm = PointOfCareAdapter.normalize_ingest_request(multi_req)
    fhir_obs_list = FhirObservationTransformer.transform_to_fhir_observations(multi_norm)

    assert len(fhir_obs_list) >= 4
    loinc_codes_generated = []
    for obs in fhir_obs_list:
        code = obs["code"]["coding"][0]["code"]
        loinc_codes_generated.append(code)
        print(f"  - [FHIR Observation] ID: {obs['id']} -> LOINC: {code} ({obs['code']['coding'][0]['display']})")
        assert obs["subject"]["reference"] == "Patient/patient-asha-anita-patra"
        assert obs["performer"][0]["reference"] == "Practitioner/usr-asha-sunita"
        assert any(ext["url"].endswith("LgdHierarchy") for ext in obs.get("extension", []))

    # Verify essential LOINC codes are all present
    assert "85354-9" in loinc_codes_generated  # BP panel
    assert "718-7" in loinc_codes_generated    # Hemoglobin
    assert "59408-5" in loinc_codes_generated  # SpO2
    assert "8310-5" in loinc_codes_generated   # Temperature
    print(f"[OK] All essential LOINC codes verified: {loinc_codes_generated}")

    # 7. Test EMR GraphQL Push Payload Generation
    print("\n--- 7. Testing EMR GraphQL Push Handling ---")
    push_res = await FhirObservationTransformer.push_to_bezs_emr_gql(multi_norm)
    assert push_res is not None
    print(f"[OK] EMR GraphQL Push Invocation Result: {push_res}")

    print("\n==================================================================")
    print("  [OK] ALL OPEN-WEARABLES POINT-OF-CARE TESTS PASSED CLEANLY!     ")
    print("==================================================================")


if __name__ == "__main__":
    asyncio.run(run_poc_tests())
