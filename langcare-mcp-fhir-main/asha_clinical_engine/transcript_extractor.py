"""
Regional Language ASR Transcript Extractor for ASHA AI Copilot.
Processes transcripts from Sarvam API / regional speech engines
(Hindi, Odia, Telugu, Tamil, Marathi, Bengali, and Indian English)
and converts natural language visit dialogues into valid FHIR R4:
- Encounter
- Observation[]
- QuestionnaireResponse
"""

from datetime import datetime, timezone
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple


class TranscriptExtractor:
    """
    Extracts clinical entities, vitals, symptoms, and care observations
    from regional conversation transcripts and maps to FHIR R4 resources.
    """

    # Multi-lingual regex keywords for vital signs (English transliterated + Devanagari / regional scripts)
    BP_PATTERNS = [
        r"(?:bp|raktachaap|raktchap|blood pressure|pressure|बीपी|रक्तचाप|रक्तदाब)\s*(?:is|tha|hai|hoga|:)?\s*(\d{2,3})\s*(?:by|over|/|-|\s+)\s*(\d{2,3})",
        r"(\d{2,3})\s*(?:by|/|-)\s*(\d{2,3})\s*(?:bp|mmhg|blood pressure|बीपी)?",
    ]

    PULSE_PATTERNS = [
        r"(?:pulse|heart rate|dhadkan|pulse rate|hr|पल्स|धड़कन|नाड़ी)\s*(?:is|tha|hai|:)?\s*(\d{2,3})",
        r"(\d{2,3})\s*(?:bpm|dhadkan per minute|beats per minute|प्रति मिनट)",
    ]

    SPO2_PATTERNS = [
        r"(?:spo2|oxygen|o2|oxygen level|o2 level|ऑक्सीजन)\s*(?:is|tha|hai|:)?\s*(\d{2,3})",
        r"(\d{2,3})\s*%\s*(?:spo2|oxygen|ऑक्सीजन)?",
    ]

    TEMP_PATTERNS = [
        r"(?:temperature|bukhar|taapman|fever|temp|बुखार|तापमान)\s*(?:is|tha|hai|:)?\s*(\d{2,3}(?:\.\d)?)",
        r"(\d{2,3}(?:\.\d)?)\s*(?:degree|deg|f|fahrenheit|celsius|c|डिग्री)",
    ]

    HB_PATTERNS = [
        r"(?:hemoglobin|hb|khoon ki matra|khoon|heamoglobin|हीमोग्लोबिन|हिमोग्लोबिन|खून|रक्त)\s*(?:is|tha|hai|में|:)?\s*(?:हीमोग्लोबिन|हिमोग्लोबिन)?\s*(\d{1,2}(?:\.\d)?)",
        r"(\d{1,2}(?:\.\d)?)\s*(?:gm|g/dl|gram|g|ग्राम)",
    ]

    WEIGHT_PATTERNS = [
        r"(?:weight|vajan|vazan|bhaar|वजन|भार)\s*(?:is|tha|hai|:)?\s*(\d{1,3}(?:\.\d)?)\s*(?:kg|kilo|kilogram|किलो|किग्रा)?",
        r"(\d{1,3}(?:\.\d)?)\s*(?:kg|kilo|kilogram|किलो|किग्रा)",
    ]

    # Clinical symptom lexicon (Multilingual: English, Hindi/Devanagari, Odia, Marathi, Telugu, Tamil, Bengali)
    SYMPTOM_LEXICON = {
        "fever": ["fever", "bukhar", "taap", "jwar", "jor", "kaachal", "juram", "बुखार", "ताप", "ଜ୍ୱର"],
        "cough": ["cough", "khansi", "khansha", "kashta", "irumal", "daggu", "kashi", "खांसी", "ଖାସ"],
        "fast_breathing": ["fast breathing", "tez saans", "saans tez", "dhumpu", "moochu thinaral", "तेज़ सांस", "ଦ୍ରୁତ ଶ୍ୱାସ"],
        "chest_indrawing": ["chest indrawing", "pasli chalna", "chhati bhitar", "nenju koodu", "पसली चलना", "ଛାତି ଦବିବା"],
        "convulsions": ["convulsions", "fits", "daura", "mirgi", "valippu", "moorchha", "दौरा", "ବାତ"],
        "lethargy": ["lethargy", "unconscious", "behosh", "kamjori", "tandra", "mayakkam", "बेहोश", "ଅଚେତ"],
        "inability_to_breastfeed": ["doodh nahi pi raha", "not breastfeeding", "unable to drink", "cannot drink", "paal kudikkala", "दूध नहीं पी रहा", "ସ୍ତନ୍ୟପାନ କରୁନାହିଁ"],
        "pedal_edema": ["pair me sujan", "swollen feet", "pedal edema", "pao phoolna", "kaal veekam", "सूजन", "पैरों में सूजन", "ଗୋଡ଼ ଫୁଲିବା"],
        "vaginal_bleeding": ["bleeding", "khoon aana", "vaginal bleeding", "spotting", "raktha sraavam", "खून आना", "রক্তপাত"],
        "severe_headache": ["severe headache", "sar dard", "sar ghoomna", "tala vali", "सिर दर्द", "ମୁଣ୍ଡ ବିନ୍ଧା"],
        "vomiting": ["vomiting", "ulti", "banti", "vamana", "उल्टी", "ବାନ୍ତି"],
        "diarrhea": ["diarrhea", "dast", "jhada", "virochana", "दस्त", "ଝାଡ଼ା"],
    }

    @classmethod
    def extract_vitals(cls, text: str) -> Dict[str, float]:
        text_lower = text.lower()
        extracted: Dict[str, float] = {}

        # 1. Blood Pressure
        for pattern in cls.BP_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                s = float(match.group(1))
                d = float(match.group(2))
                if 70 <= s <= 260 and 40 <= d <= 160:
                    extracted["systolic_bp"] = s
                    extracted["diastolic_bp"] = d
                    break

        # 2. Pulse / Heart Rate
        for pattern in cls.PULSE_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                val = float(match.group(1))
                if 40 <= val <= 220:
                    extracted["pulse"] = val
                    break

        # 3. SpO2
        for pattern in cls.SPO2_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                val = float(match.group(1))
                if 50 <= val <= 100:
                    extracted["spo2"] = val
                    break

        # 4. Temperature
        for pattern in cls.TEMP_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                val = float(match.group(1))
                if val > 80:  # Fahrenheit
                    extracted["temperature_f"] = val
                    extracted["temperature_c"] = round((val - 32) * 5 / 9, 1)
                    break
                elif 34 <= val <= 43:  # Celsius
                    extracted["temperature_c"] = val
                    extracted["temperature_f"] = round((val * 9 / 5) + 32, 1)
                    break

        # 5. Hemoglobin
        for pattern in cls.HB_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                val = float(match.group(1))
                if 2.0 <= val <= 20.0:
                    extracted["hemoglobin"] = val
                    break

        # 6. Weight
        for pattern in cls.WEIGHT_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                val = float(match.group(1))
                if 1.5 <= val <= 180.0:
                    extracted["weight_kg"] = val
                    break

        return extracted

    @classmethod
    def extract_symptoms(cls, text: str) -> List[str]:
        text_lower = text.lower()
        detected: List[str] = []
        for canonical, aliases in cls.SYMPTOM_LEXICON.items():
            if any(alias in text_lower for alias in aliases):
                detected.append(canonical)
        return detected

    @classmethod
    def build_fhir_resources(
        cls,
        transcript: str,
        patient_id: str,
        worker_id: str,
        village_lgd_code: str,
        visit_uuid: Optional[str] = None,
        encounter_date: Optional[str] = None,
        encounter_type: str = "household_visit",  # "anc_visit" | "child_imnci" | "cbac_survey" | "household_visit"
        is_maternal: bool = False,
        is_pediatric: bool = False,
    ) -> Tuple[Dict[str, Any], List[Dict[str, Any]], Dict[str, Any]]:
        """
        Parses transcript and generates:
        1. FHIR Encounter
        2. FHIR Observation[]
        3. FHIR QuestionnaireResponse
        """
        now_iso = encounter_date or datetime.now(timezone.utc).isoformat()
        visit_id = visit_uuid or f"visit-{uuid.uuid4().hex[:12]}"
        encounter_id = f"enc-{visit_id}"

        vitals = cls.extract_vitals(transcript)
        symptoms = cls.extract_symptoms(transcript)

        # 1. FHIR R4 Encounter
        encounter: Dict[str, Any] = {
            "resourceType": "Encounter",
            "id": encounter_id,
            "status": "finished",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "HH",
                "display": "Home Health Visit",
            },
            "type": [
                {
                    "coding": [
                        {
                            "system": "https://nhm.gov.in/encounter-type",
                            "code": encounter_type,
                            "display": encounter_type.replace("_", " ").title(),
                        }
                    ]
                }
            ],
            "subject": {"reference": f"Patient/{patient_id}"},
            "participant": [
                {
                    "type": [
                        {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                                    "code": "PPRF",
                                    "display": "Primary Performer",
                                }
                            ]
                        }
                    ],
                    "individual": {"reference": f"Practitioner/{worker_id}"},
                }
            ],
            "period": {"start": now_iso, "end": now_iso},
            "location": [
                {
                    "location": {
                        "identifier": {
                            "system": "https://lgd.gov.in/village",
                            "value": village_lgd_code,
                        },
                        "display": f"Village LGD {village_lgd_code}",
                    }
                }
            ],
            "serviceProvider": {"identifier": {"system": "https://abdm.gov.in/hpr", "value": worker_id}},
        }

        # 2. FHIR R4 Observations
        observations: List[Dict[str, Any]] = []

        # BP Observation
        if "systolic_bp" in vitals and "diastolic_bp" in vitals:
            obs_bp = {
                "resourceType": "Observation",
                "id": f"obs-bp-{uuid.uuid4().hex[:8]}",
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
                        {"system": "http://loinc.org", "code": "85354-9", "display": "Blood pressure panel"}
                    ]
                },
                "subject": {"reference": f"Patient/{patient_id}"},
                "encounter": {"reference": f"Encounter/{encounter_id}"},
                "effectiveDateTime": now_iso,
                "component": [
                    {
                        "code": {"coding": [{"system": "http://loinc.org", "code": "8480-6", "display": "Systolic BP"}]},
                        "valueQuantity": {"value": vitals["systolic_bp"], "unit": "mmHg", "system": "http://unitsofmeasure.org", "code": "mm[Hg]"},
                    },
                    {
                        "code": {"coding": [{"system": "http://loinc.org", "code": "8462-4", "display": "Diastolic BP"}]},
                        "valueQuantity": {"value": vitals["diastolic_bp"], "unit": "mmHg", "system": "http://unitsofmeasure.org", "code": "mm[Hg]"},
                    },
                ],
            }
            observations.append(obs_bp)

        # Pulse Observation
        if "pulse" in vitals:
            obs_pulse = {
                "resourceType": "Observation",
                "id": f"obs-hr-{uuid.uuid4().hex[:8]}",
                "status": "final",
                "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs"}]}],
                "code": {"coding": [{"system": "http://loinc.org", "code": "8867-4", "display": "Heart rate"}]},
                "subject": {"reference": f"Patient/{patient_id}"},
                "encounter": {"reference": f"Encounter/{encounter_id}"},
                "effectiveDateTime": now_iso,
                "valueQuantity": {"value": vitals["pulse"], "unit": "beats/minute", "system": "http://unitsofmeasure.org", "code": "/min"},
            }
            observations.append(obs_pulse)

        # SpO2 Observation
        if "spo2" in vitals:
            obs_spo2 = {
                "resourceType": "Observation",
                "id": f"obs-spo2-{uuid.uuid4().hex[:8]}",
                "status": "final",
                "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs"}]}],
                "code": {"coding": [{"system": "http://loinc.org", "code": "59408-5", "display": "Oxygen saturation in Arterial blood"}]},
                "subject": {"reference": f"Patient/{patient_id}"},
                "encounter": {"reference": f"Encounter/{encounter_id}"},
                "effectiveDateTime": now_iso,
                "valueQuantity": {"value": vitals["spo2"], "unit": "%", "system": "http://unitsofmeasure.org", "code": "%"},
            }
            observations.append(obs_spo2)

        # Hemoglobin Observation
        if "hemoglobin" in vitals:
            obs_hb = {
                "resourceType": "Observation",
                "id": f"obs-hb-{uuid.uuid4().hex[:8]}",
                "status": "final",
                "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "laboratory"}]}],
                "code": {"coding": [{"system": "http://loinc.org", "code": "718-7", "display": "Hemoglobin [Mass/volume] in Blood"}]},
                "subject": {"reference": f"Patient/{patient_id}"},
                "encounter": {"reference": f"Encounter/{encounter_id}"},
                "effectiveDateTime": now_iso,
                "valueQuantity": {"value": vitals["hemoglobin"], "unit": "g/dL", "system": "http://unitsofmeasure.org", "code": "g/dL"},
            }
            observations.append(obs_hb)

        # Body Temperature
        if "temperature_c" in vitals:
            obs_temp = {
                "resourceType": "Observation",
                "id": f"obs-temp-{uuid.uuid4().hex[:8]}",
                "status": "final",
                "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "vital-signs"}]}],
                "code": {"coding": [{"system": "http://loinc.org", "code": "8310-5", "display": "Body temperature"}]},
                "subject": {"reference": f"Patient/{patient_id}"},
                "encounter": {"reference": f"Encounter/{encounter_id}"},
                "effectiveDateTime": now_iso,
                "valueQuantity": {"value": vitals["temperature_c"], "unit": "Cel", "system": "http://unitsofmeasure.org", "code": "Cel"},
            }
            observations.append(obs_temp)

        # 3. FHIR R4 QuestionnaireResponse
        questionnaire_id = "anc-highrisk-v1" if is_maternal else ("imnci-pediatric-triage-v1" if is_pediatric else "cbac-ncd-v1")
        items: List[Dict[str, Any]] = []

        if is_maternal:
            items.extend([
                {"linkId": "anc_bp_status", "text": "High BP (>= 140/90 mmHg)", "answer": [{"valueBoolean": vitals.get("systolic_bp", 0) >= 140 or vitals.get("diastolic_bp", 0) >= 90}]},
                {"linkId": "anc_severe_anemia", "text": "Severe Anemia (Hb < 7.0 g/dL)", "answer": [{"valueBoolean": vitals.get("hemoglobin", 12.0) < 7.0}]},
                {"linkId": "anc_vaginal_bleeding", "text": "Vaginal Bleeding", "answer": [{"valueBoolean": "vaginal_bleeding" in symptoms}]},
                {"linkId": "anc_pedal_edema", "text": "Pedal Edema", "answer": [{"valueBoolean": "pedal_edema" in symptoms}]},
            ])
        elif is_pediatric:
            items.extend([
                {"linkId": "imnci_inability_breastfeed", "text": "Unable to breastfeed or drink", "answer": [{"valueBoolean": "inability_to_breastfeed" in symptoms}]},
                {"linkId": "imnci_convulsions", "text": "Convulsions during illness", "answer": [{"valueBoolean": "convulsions" in symptoms}]},
                {"linkId": "imnci_chest_indrawing", "text": "Chest indrawing observed", "answer": [{"valueBoolean": "chest_indrawing" in symptoms}]},
                {"linkId": "imnci_fast_breathing", "text": "Fast breathing", "answer": [{"valueBoolean": "fast_breathing" in symptoms}]},
            ])
        else:
            items.extend([
                {"linkId": "cbac_tobacco", "text": "Uses tobacco or bidi", "answer": [{"valueBoolean": "tobacco" in transcript.lower() or "bidi" in transcript.lower()}]},
                {"linkId": "cbac_hypertension_history", "text": "Known hypertension / High BP", "answer": [{"valueBoolean": vitals.get("systolic_bp", 0) >= 140}]},
            ])

        questionnaire_response: Dict[str, Any] = {
            "resourceType": "QuestionnaireResponse",
            "id": f"qr-{visit_id}",
            "questionnaire": f"Questionnaire/{questionnaire_id}",
            "status": "completed",
            "subject": {"reference": f"Patient/{patient_id}"},
            "encounter": {"reference": f"Encounter/{encounter_id}"},
            "authored": now_iso,
            "author": {"reference": f"Practitioner/{worker_id}"},
            "item": items,
        }

        return encounter, observations, questionnaire_response
