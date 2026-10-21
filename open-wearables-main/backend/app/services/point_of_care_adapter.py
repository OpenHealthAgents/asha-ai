"""
Point-of-Care Ingestion Adapter for Rural Field Screening Kits.
Normalizes BLE GATT characteristics and mobile input payloads into unified clinical metrics.
"""

import struct
from typing import List, Optional
import uuid

from app.schemas.providers.point_of_care import (
    BloodPressureReading,
    ClinicalRiskSeverity,
    FieldDeviceType,
    GlucometerReading,
    HemoglobinometerReading,
    NormalizedPointOfCarePayload,
    NormalizedVitalMetric,
    PointOfCareIngestRequest,
    PulseOximeterReading,
    ThermometerReading,
    FetalDopplerReading,
)


class PointOfCareAdapter:
    """
    Normalizes readings from frontline point-of-care screening devices:
    - Bluetooth BP monitors (GATT 0x2A35)
    - Pulse oximeters (GATT 0x2A5F)
    - Blood glucometers (GATT 0x2A18)
    - Digital hemoglobinometers
    - Smart thermometers (GATT 0x2A1C)
    - Handheld fetal Doppler monitors
    """

    @classmethod
    def normalize_ingest_request(cls, req: PointOfCareIngestRequest) -> NormalizedPointOfCarePayload:
        ingest_id = f"poc-ingest-{uuid.uuid4().hex[:12]}"
        metrics: List[NormalizedVitalMetric] = []
        overall_risk = ClinicalRiskSeverity.NORMAL
        requires_referral = False
        referral_reasons: List[str] = []

        # 1. Parse Raw BLE GATT payload if provided
        if req.raw_ble_payload_hex:
            cls._parse_raw_ble(req)

        # 2. Blood Pressure Normalization (LOINC 8480-6 Systolic, 8462-4 Diastolic)
        if req.blood_pressure:
            bp = req.blood_pressure
            systolic = bp.systolic_mmhg
            diastolic = bp.diastolic_mmhg

            # Maternal pre-eclampsia screening (>= 140/90 mmHg)
            if req.context.is_maternal:
                if systolic >= 160 or diastolic >= 110:
                    status = ClinicalRiskSeverity.CRITICAL_ALERT
                    msg = "Critical Pre-eclampsia Alert (BP >= 160/110 mmHg). Immediate PHC emergency escalation required."
                    requires_referral = True
                    referral_reasons.append(msg)
                elif systolic >= 140 or diastolic >= 90:
                    status = ClinicalRiskSeverity.WARNING
                    msg = "High Blood Pressure in Pregnancy (Pre-eclampsia danger sign >= 140/90 mmHg)."
                    requires_referral = True
                    referral_reasons.append(msg)
                else:
                    status = ClinicalRiskSeverity.NORMAL
                    msg = "Normal Maternal Blood Pressure."
            else:
                # General adult hypertension (Grade 1 / 2)
                if systolic >= 180 or diastolic >= 120:
                    status = ClinicalRiskSeverity.CRITICAL_ALERT
                    msg = "Hypertensive Crisis (BP >= 180/120 mmHg)."
                    requires_referral = True
                    referral_reasons.append(msg)
                elif systolic >= 140 or diastolic >= 90:
                    status = ClinicalRiskSeverity.WARNING
                    msg = "Stage 2 Hypertension (BP >= 140/90 mmHg)."
                    requires_referral = True
                    referral_reasons.append(msg)
                else:
                    status = ClinicalRiskSeverity.NORMAL
                    msg = "Normal Blood Pressure."

            overall_risk = cls._escalate_risk(overall_risk, status)

            metrics.append(
                NormalizedVitalMetric(
                    metric_name="Systolic Blood Pressure",
                    loinc_code="8480-6",
                    value=systolic,
                    unit="mmHg",
                    clinical_status=status,
                    alert_message=msg,
                )
            )
            metrics.append(
                NormalizedVitalMetric(
                    metric_name="Diastolic Blood Pressure",
                    loinc_code="8462-4",
                    value=diastolic,
                    unit="mmHg",
                    clinical_status=status,
                    alert_message=msg,
                )
            )

            if bp.pulse_bpm:
                metrics.append(
                    NormalizedVitalMetric(
                        metric_name="Heart Rate / Pulse",
                        loinc_code="8867-4",
                        value=bp.pulse_bpm,
                        unit="/min",
                        clinical_status=ClinicalRiskSeverity.NORMAL,
                    )
                )

        # 3. Pulse Oximeter Normalization (LOINC 59408-5 SpO2)
        if req.pulse_oximeter:
            pox = req.pulse_oximeter
            spo2 = pox.spo2_percent
            if spo2 < 90.0:
                status = ClinicalRiskSeverity.CRITICAL_ALERT
                msg = f"Severe Hypoxemia (SpO2 {spo2}% < 90%). Emergency oxygen and PHC referral needed."
                requires_referral = True
                referral_reasons.append(msg)
            elif spo2 < 94.0:
                status = ClinicalRiskSeverity.WARNING
                msg = f"Mild Hypoxemia (SpO2 {spo2}% < 94%). Urgent clinical assessment."
                requires_referral = True
                referral_reasons.append(msg)
            else:
                status = ClinicalRiskSeverity.NORMAL
                msg = f"Normal Oxygen Saturation ({spo2}%)."

            overall_risk = cls._escalate_risk(overall_risk, status)

            metrics.append(
                NormalizedVitalMetric(
                    metric_name="Oxygen Saturation SpO2",
                    loinc_code="59408-5",
                    value=spo2,
                    unit="%",
                    clinical_status=status,
                    alert_message=msg,
                )
            )
            metrics.append(
                NormalizedVitalMetric(
                    metric_name="Pulse Rate",
                    loinc_code="8867-4",
                    value=pox.pulse_bpm,
                    unit="/min",
                    clinical_status=ClinicalRiskSeverity.NORMAL,
                )
            )

        # 4. Glucometer Normalization (LOINC 2339-0 Blood Glucose)
        if req.glucometer:
            gluc = req.glucometer
            val = gluc.glucose_mg_dl
            if val < 54.0:
                status = ClinicalRiskSeverity.CRITICAL_ALERT
                msg = f"Severe Hypoglycemia ({val} mg/dL). Immediate oral glucose / PHC referral."
                requires_referral = True
                referral_reasons.append(msg)
            elif (req.context.is_maternal and val >= 140.0) or val >= 200.0:
                status = ClinicalRiskSeverity.WARNING
                msg = f"Hyperglycemia / Gestational Diabetes Alert ({val} mg/dL)."
                requires_referral = True
                referral_reasons.append(msg)
            else:
                status = ClinicalRiskSeverity.NORMAL
                msg = f"Blood Glucose normal ({val} mg/dL)."

            overall_risk = cls._escalate_risk(overall_risk, status)

            metrics.append(
                NormalizedVitalMetric(
                    metric_name="Blood Glucose",
                    loinc_code="2339-0",
                    value=val,
                    unit="mg/dL",
                    clinical_status=status,
                    alert_message=msg,
                )
            )

        # 5. Digital Hemoglobinometer Normalization (LOINC 718-7 Hemoglobin)
        if req.hemoglobinometer:
            hb = req.hemoglobinometer.hemoglobin_g_dl
            # NHM Maternal Anemia Classification: Severe < 7.0, Moderate 7.0-9.9, Mild 10.0-10.9
            if hb < 7.0:
                status = ClinicalRiskSeverity.CRITICAL_ALERT
                msg = f"Severe Maternal Anemia (Hb {hb} g/dL < 7.0 g/dL). High-risk pregnancy danger sign requiring blood transfusion / IV iron sucrose."
                requires_referral = True
                referral_reasons.append(msg)
            elif hb < 10.0:
                status = ClinicalRiskSeverity.WARNING
                msg = f"Moderate Anemia (Hb {hb} g/dL). Double dose IFA tablets and dietary counselling."
                referral_reasons.append(msg)
            else:
                status = ClinicalRiskSeverity.NORMAL
                msg = f"Normal Hemoglobin ({hb} g/dL)."

            overall_risk = cls._escalate_risk(overall_risk, status)

            metrics.append(
                NormalizedVitalMetric(
                    metric_name="Hemoglobin",
                    loinc_code="718-7",
                    value=hb,
                    unit="g/dL",
                    clinical_status=status,
                    alert_message=msg,
                )
            )

        # 6. Smart Thermometer Normalization (LOINC 8310-5 Body Temperature)
        if req.thermometer:
            temp = req.thermometer.temperature_celsius
            if temp >= 39.0:
                status = ClinicalRiskSeverity.CRITICAL_ALERT
                msg = f"High Grade Fever ({temp} °C). Sepsis/Malaria evaluation required."
                requires_referral = True
                referral_reasons.append(msg)
            elif temp < 36.0:
                status = ClinicalRiskSeverity.WARNING
                msg = f"Hypothermia alert ({temp} °C). Immediate thermal care / Kangaroo Mother Care."
                requires_referral = True
                referral_reasons.append(msg)
            else:
                status = ClinicalRiskSeverity.NORMAL
                msg = f"Normal body temperature ({temp} °C)."

            overall_risk = cls._escalate_risk(overall_risk, status)

            metrics.append(
                NormalizedVitalMetric(
                    metric_name="Body Temperature",
                    loinc_code="8310-5",
                    value=temp,
                    unit="Cel",
                    clinical_status=status,
                    alert_message=msg,
                )
            )

        # 7. Handheld Fetal Doppler (LOINC 55283-6 Fetal Heart Rate)
        if req.fetal_doppler:
            fhr = req.fetal_doppler.fetal_heart_rate_bpm
            if fhr < 110.0 or fhr > 160.0:
                status = ClinicalRiskSeverity.CRITICAL_ALERT
                msg = f"Fetal Distress Alert: Fetal heart rate {fhr} bpm (Normal range: 110 - 160 bpm)."
                requires_referral = True
                referral_reasons.append(msg)
            else:
                status = ClinicalRiskSeverity.NORMAL
                msg = f"Normal Fetal Heart Rate ({fhr} bpm)."

            overall_risk = cls._escalate_risk(overall_risk, status)

            metrics.append(
                NormalizedVitalMetric(
                    metric_name="Fetal Heart Rate",
                    loinc_code="55283-6",
                    value=fhr,
                    unit="/min",
                    clinical_status=status,
                    alert_message=msg,
                )
            )

        referral_rec = "; ".join(referral_reasons) if referral_reasons else None

        return NormalizedPointOfCarePayload(
            ingest_id=ingest_id,
            device_type=req.device_type,
            device_info={
                "manufacturer": req.device_manufacturer,
                "model": req.device_model,
                "serial_number": req.device_serial_number,
                "battery_level": req.battery_level_percent,
            },
            context=req.context,
            metrics=metrics,
            overall_clinical_risk=overall_risk,
            requires_emergency_referral=requires_referral,
            referral_recommendation=referral_rec,
        )

    @staticmethod
    def _parse_raw_ble(req: PointOfCareIngestRequest) -> None:
        """Parses standard Bluetooth SIG GATT characteristic bytes."""
        try:
            raw_bytes = bytes.fromhex(req.raw_ble_payload_hex or "")
            if req.device_type == FieldDeviceType.BLUETOOTH_BP and len(raw_bytes) >= 7:
                # IEEE 11073-10407 Blood Pressure Measurement (0x2A35)
                # flags: byte 0, systolic: SFLOAT (2 bytes), diastolic: SFLOAT (2 bytes), MAP: SFLOAT (2 bytes)
                flags = raw_bytes[0]
                systolic = struct.unpack("<H", raw_bytes[1:3])[0]
                diastolic = struct.unpack("<H", raw_bytes[3:5])[0]
                pulse = struct.unpack("<H", raw_bytes[7:9])[0] if len(raw_bytes) >= 9 else None
                req.blood_pressure = BloodPressureReading(
                    systolic_mmhg=float(systolic),
                    diastolic_mmhg=float(diastolic),
                    pulse_bpm=float(pulse) if pulse else None,
                )
            elif req.device_type == FieldDeviceType.PULSE_OXIMETER and len(raw_bytes) >= 4:
                # IEEE 11073-10404 PLX Spot-Check
                spo2 = raw_bytes[1]
                pulse = raw_bytes[2]
                req.pulse_oximeter = PulseOximeterReading(
                    spo2_percent=float(spo2),
                    pulse_bpm=float(pulse),
                )
        except Exception:
            pass  # Fall back to structured reading

    @staticmethod
    def _escalate_risk(current: ClinicalRiskSeverity, new_risk: ClinicalRiskSeverity) -> ClinicalRiskSeverity:
        hierarchy = {
            ClinicalRiskSeverity.NORMAL: 0,
            ClinicalRiskSeverity.WARNING: 1,
            ClinicalRiskSeverity.CRITICAL_ALERT: 2,
        }
        return new_risk if hierarchy[new_risk] > hierarchy[current] else current
