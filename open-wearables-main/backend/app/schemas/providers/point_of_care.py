"""
Point-of-Care (PoC) Ingestion Schemas for Frontline ASHA Rural Screening Kits.
Supports Bluetooth BP Cuffs, Pulse Oximeters, Glucometers, Hemoglobinometers,
Smart Thermometers, and Handheld Fetal Dopplers.
"""

from enum import StrEnum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FieldDeviceType(StrEnum):
    BLUETOOTH_BP = "bluetooth_bp_cuff"
    PULSE_OXIMETER = "pulse_oximeter"
    GLUCOMETER = "glucometer"
    DIGITAL_HEMOGLOBINOMETER = "digital_hemoglobinometer"
    SMART_THERMOMETER = "smart_thermometer"
    FETAL_DOPPLER = "fetal_doppler"


class ClinicalRiskSeverity(StrEnum):
    NORMAL = "NORMAL"
    WARNING = "WARNING"
    CRITICAL_ALERT = "CRITICAL_ALERT"


class ReadingContext(BaseModel):
    worker_id: str = Field(..., description="ASHA / ANM worker identifier")
    patient_id: str = Field(..., description="Target patient FHIR identifier")
    visit_uuid: str = Field(..., description="Idempotent field visit UUID")
    village_lgd_code: str = Field(..., description="Village LGD code")
    recorded_at: str = Field(..., description="ISO 8601 timestamp of measurement")
    is_maternal: bool = Field(default=False, description="Whether patient is currently pregnant")
    gestational_age_weeks: Optional[int] = Field(default=None, description="Gestational weeks if pregnant")


class BloodPressureReading(BaseModel):
    systolic_mmhg: float = Field(..., ge=40, le=300)
    diastolic_mmhg: float = Field(..., ge=20, le=200)
    pulse_bpm: Optional[float] = Field(default=None, ge=30, le=250)
    mean_arterial_pressure_mmhg: Optional[float] = None
    arrhythmia_detected: bool = False


class PulseOximeterReading(BaseModel):
    spo2_percent: float = Field(..., ge=40, le=100)
    pulse_bpm: float = Field(..., ge=30, le=250)
    perfusion_index: Optional[float] = None


class GlucometerReading(BaseModel):
    glucose_mg_dl: float = Field(..., ge=20, le=800)
    meal_context: str = Field(default="random", description="fasting | postprandial | random")


class HemoglobinometerReading(BaseModel):
    hemoglobin_g_dl: float = Field(..., ge=2.0, le=25.0)
    strip_lot_number: Optional[str] = None


class ThermometerReading(BaseModel):
    temperature_celsius: float = Field(..., ge=30.0, le=45.0)
    measurement_site: str = Field(default="axillary", description="axillary | forehead_temporal | oral")


class FetalDopplerReading(BaseModel):
    fetal_heart_rate_bpm: float = Field(..., ge=60, le=240)


class PointOfCareIngestRequest(BaseModel):
    device_type: FieldDeviceType
    device_manufacturer: str = Field(default="Generic BLE Screening Kit")
    device_model: str = Field(default="Standard PoC Kit")
    device_serial_number: Optional[str] = None
    battery_level_percent: Optional[int] = Field(default=None, ge=0, le=100)
    context: ReadingContext
    raw_ble_payload_hex: Optional[str] = Field(default=None, description="Raw hex string from BLE GATT characteristic if available")
    blood_pressure: Optional[BloodPressureReading] = None
    pulse_oximeter: Optional[PulseOximeterReading] = None
    glucometer: Optional[GlucometerReading] = None
    hemoglobinometer: Optional[HemoglobinometerReading] = None
    thermometer: Optional[ThermometerReading] = None
    fetal_doppler: Optional[FetalDopplerReading] = None


class NormalizedVitalMetric(BaseModel):
    metric_name: str
    loinc_code: str
    value: float
    unit: str
    clinical_status: ClinicalRiskSeverity
    alert_message: Optional[str] = None


class NormalizedPointOfCarePayload(BaseModel):
    ingest_id: str
    device_type: FieldDeviceType
    device_info: Dict[str, Any]
    context: ReadingContext
    metrics: List[NormalizedVitalMetric]
    overall_clinical_risk: ClinicalRiskSeverity
    requires_emergency_referral: bool
    referral_recommendation: Optional[str] = None
