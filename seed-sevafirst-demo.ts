/**
 * SevaFirst Frontline ASHA AI Copilot - Master Demo Seed Script
 * ==============================================================================
 * Populates realistic Indian rural healthcare data for National Health Mission (NHM):
 * 1. Primary Health Centre: "PHC Thazhambur" (Chengalpattu, Tamil Nadu) + Medical Officer.
 * 2. Frontline RBAC: 2 ASHA workers mapped to 15 rural households with 14-day offline JWTs.
 * 3. 15 Rural Households (`Group` FHIR R4) with ABHA IDs, RCH IDs, and family members.
 * 4. Three production-grade clinical scenarios:
 *    - Scenario A: High-Risk Maternal Triage (Pre-eclampsia, BP 152/98 mmHg, 108 escalation)
 *    - Scenario B: Pediatric Care Gap (14mo infant, overdue Pentavalent-3 & MR-1, Tamil audio counseling)
 *    - Scenario C: Offline Sync Resilience (3 voice encounters queued offline, bulk sync, telemetry)
 * ==============================================================================
 */

import * as fs from "fs";
import * as path from "path";
import * as crypto from "crypto";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// ── Configuration & Geographic Constants (LGD / Census) ─────────────────────
const GEOGRAPHY = {
  STATE: "Tamil Nadu",
  STATE_CODE: "TN",
  DISTRICT: "Chengalpattu",
  DISTRICT_CODE: "dist-chengalpattu",
  BLOCK: "Thiruporur",
  BLOCK_CODE: "blk-thiruporur",
  VILLAGE_NAME: "Thazhambur",
  VILLAGE_LGD_CODE: "629375",
  PHC_ID: "phc-thazhambur",
  PHC_NAME: "Primary Health Centre Thazhambur",
  SUBCENTRE_ID: "sc-thazhambur-north",
  SUBCENTRE_NAME: "Thazhambur North Health & Wellness Sub-Centre",
};

// ── 1. PHC Thazhambur & Medical Officer ──────────────────────────────────────
export interface PHCRecord {
  id: string;
  name: string;
  state_code: string;
  district_code: string;
  block_code: string;
  village_lgd_code: string;
  subcentre_id: string;
  medical_officer: {
    id: string;
    name: string;
    username: string;
    email: string;
    phone: string;
    role: string;
    hpr_id: string;
  };
  supplies_stock: Array<{
    item_code: string;
    item_name: string;
    current_quantity: number;
    minimum_threshold: number;
    unit: string;
    is_bottleneck: boolean;
  }>;
}

export const PHC_THAZHAMBUR_SEED: PHCRecord = {
  id: GEOGRAPHY.PHC_ID,
  name: GEOGRAPHY.PHC_NAME,
  state_code: GEOGRAPHY.STATE_CODE,
  district_code: GEOGRAPHY.DISTRICT_CODE,
  block_code: GEOGRAPHY.BLOCK_CODE,
  village_lgd_code: GEOGRAPHY.VILLAGE_LGD_CODE,
  subcentre_id: GEOGRAPHY.SUBCENTRE_ID,
  medical_officer: {
    id: "usr-mo-radhakrishnan-01",
    name: "Dr. K. Radhakrishnan, MBBS, MD (Community Medicine)",
    username: "mo_thazhambur",
    email: "dr.radhakrishnan@nhm.tn.gov.in",
    phone: "+919444123456",
    role: "ROLE_PHC_MO",
    hpr_id: "HPR-TN-982341",
  },
  supplies_stock: [
    {
      item_code: "MED-IFA-RED",
      item_name: "Iron Folic Acid (IFA) Tablets (Maternal Red)",
      current_quantity: 45,
      minimum_threshold: 250,
      unit: "strips",
      is_bottleneck: true, // Urgent Stockout
    },
    {
      item_code: "MED-CALCIUM-500",
      item_name: "Calcium & Vitamin D3 Tablets (500mg)",
      current_quantity: 80,
      minimum_threshold: 300,
      unit: "tablets",
      is_bottleneck: true,
    },
    {
      item_code: "MED-OXYTOCIN",
      item_name: "Oxytocin Injection (10 IU/mL Ampoules)",
      current_quantity: 14,
      minimum_threshold: 50,
      unit: "ampoules",
      is_bottleneck: true,
    },
    {
      item_code: "MED-ORS-ZINC",
      item_name: "ORS Sachets + Zinc Sulfate (Pediatric)",
      current_quantity: 420,
      minimum_threshold: 200,
      unit: "packets",
      is_bottleneck: false,
    },
    {
      item_code: "MED-PCM-500",
      item_name: "Paracetamol 500mg",
      current_quantity: 850,
      minimum_threshold: 300,
      unit: "tablets",
      is_bottleneck: false,
    },
  ],
};

// ── 2. ASHA Workers & Cryptographic 14-Day Offline Tokens ───────────────────
export interface AshaWorkerSeed {
  id: string;
  name: string;
  username: string;
  phone: string;
  role: string;
  hpr_id: string;
  state_code: string;
  district_code: string;
  block_code: string;
  phc_id: string;
  subcentre_id: string;
  village_lgd_code: string;
  assigned_households: string[];
  offline_token: {
    token_id: string;
    issued_at: string;
    expires_at: string;
    ttl_days: number;
    signature: string;
  };
}

function generateOfflineToken(workerId: string, role: string, villageLgd: string) {
  const now = new Date();
  const expires = new Date(now.getTime() + 14 * 24 * 60 * 60 * 1000); // 14 days
  const tokenId = `tok-off-${crypto.randomBytes(8).toString("hex")}`;
  const rawPayload = `${tokenId}|${workerId}|${role}|${villageLgd}|${now.toISOString()}|${expires.toISOString()}`;
  const signature = crypto.createHmac("sha256", "sevafirst_national_health_mission_secret_key_32chars")
    .update(rawPayload)
    .digest("hex");

  return {
    token_id: tokenId,
    issued_at: now.toISOString(),
    expires_at: expires.toISOString(),
    ttl_days: 14,
    signature,
  };
}

export const ASHA_WORKERS_SEED: AshaWorkerSeed[] = [
  {
    id: "usr-asha-kavitha-629375",
    name: "Kavitha Sundaram",
    username: "asha_kavitha",
    phone: "+919840112233",
    role: "ROLE_ASHA",
    hpr_id: "HPR-ASHA-TN-629375-01",
    state_code: GEOGRAPHY.STATE_CODE,
    district_code: GEOGRAPHY.DISTRICT_CODE,
    block_code: GEOGRAPHY.BLOCK_CODE,
    phc_id: GEOGRAPHY.PHC_ID,
    subcentre_id: GEOGRAPHY.SUBCENTRE_ID,
    village_lgd_code: GEOGRAPHY.VILLAGE_LGD_CODE,
    assigned_households: [
      "hh-thazhambur-001",
      "hh-thazhambur-002",
      "hh-thazhambur-003",
      "hh-thazhambur-004",
      "hh-thazhambur-005",
      "hh-thazhambur-006",
      "hh-thazhambur-007",
      "hh-thazhambur-008",
    ],
    offline_token: generateOfflineToken("usr-asha-kavitha-629375", "ROLE_ASHA", GEOGRAPHY.VILLAGE_LGD_CODE),
  },
  {
    id: "usr-asha-selvi-629375",
    name: "Selvi Murugan",
    username: "asha_selvi",
    phone: "+919840445566",
    role: "ROLE_ASHA",
    hpr_id: "HPR-ASHA-TN-629375-02",
    state_code: GEOGRAPHY.STATE_CODE,
    district_code: GEOGRAPHY.DISTRICT_CODE,
    block_code: GEOGRAPHY.BLOCK_CODE,
    phc_id: GEOGRAPHY.PHC_ID,
    subcentre_id: GEOGRAPHY.SUBCENTRE_ID,
    village_lgd_code: GEOGRAPHY.VILLAGE_LGD_CODE,
    assigned_households: [
      "hh-thazhambur-009",
      "hh-thazhambur-010",
      "hh-thazhambur-011",
      "hh-thazhambur-012",
      "hh-thazhambur-013",
      "hh-thazhambur-014",
      "hh-thazhambur-015",
    ],
    offline_token: generateOfflineToken("usr-asha-selvi-629375", "ROLE_ASHA", GEOGRAPHY.VILLAGE_LGD_CODE),
  },
];

// ── 3. 15 Rural Households & FHIR R4 Beneficiaries ──────────────────────────
export interface HouseholdMember {
  id: string;
  name: string;
  relationship: string;
  gender: "male" | "female" | "other";
  birth_date: string;
  age_years: number;
  abha_id: string;
  rch_id?: string;
  is_pregnant?: boolean;
  gestational_weeks?: number;
  gravida_para?: string;
  immunizations_done: string[];
  cbac_screened: boolean;
}

export interface RuralHousehold {
  id: string;
  household_number: string;
  head_of_household: string;
  address_line: string;
  village_name: string;
  village_lgd_code: string;
  assigned_asha_id: string;
  members: HouseholdMember[];
}

export function generate15Households(): RuralHousehold[] {
  const households: RuralHousehold[] = [
    {
      id: "hh-thazhambur-001",
      household_number: "THZ-WARD1-042",
      head_of_household: "Anbarasan Muthu",
      address_line: "No. 14, Pillayar Kovil Street",
      village_name: GEOGRAPHY.VILLAGE_NAME,
      village_lgd_code: GEOGRAPHY.VILLAGE_LGD_CODE,
      assigned_asha_id: "usr-asha-kavitha-629375",
      members: [
        {
          id: "pat-anbarasan-muthu",
          name: "Anbarasan Muthu",
          relationship: "Head of Household",
          gender: "male",
          birth_date: "1994-06-15",
          age_years: 32,
          abha_id: "91-4432-8761-9011",
          immunizations_done: [],
          cbac_screened: true,
        },
        {
          id: "pat-priya-anbarasan",
          name: "Priya Anbarasan",
          relationship: "Spouse (Pregnant Mother)",
          gender: "female",
          birth_date: "2000-03-22",
          age_years: 26,
          abha_id: "91-4432-8761-9012",
          rch_id: "RCH-TN-2026-004521",
          is_pregnant: true,
          gestational_weeks: 32,
          gravida_para: "G2P1",
          immunizations_done: ["TT-1"],
          cbac_screened: true,
        },
        {
          id: "pat-baby-kavin",
          name: "Baby Kavin Anbarasan",
          relationship: "Child (Infant)",
          gender: "male",
          birth_date: "2025-08-10",
          age_years: 1,
          abha_id: "91-4432-8761-9013",
          rch_id: "RCH-CHILD-TN-2025-089123",
          immunizations_done: ["BCG", "OPV-0", "HepB-0", "OPV-1", "Pentavalent-1", "Rota-1", "OPV-2", "Pentavalent-2", "Rota-2"],
          cbac_screened: false,
        },
        {
          id: "pat-meenakshi-ammal",
          name: "Meenakshi Ammal",
          relationship: "Mother-in-law (Elder)",
          gender: "female",
          birth_date: "1960-11-05",
          age_years: 65,
          abha_id: "91-4432-8761-9014",
          immunizations_done: [],
          cbac_screened: true,
        },
      ],
    },
    {
      id: "hh-thazhambur-002",
      household_number: "THZ-WARD1-043",
      head_of_household: "Murugan Selvam",
      address_line: "No. 18, Pillayar Kovil Street",
      village_name: GEOGRAPHY.VILLAGE_NAME,
      village_lgd_code: GEOGRAPHY.VILLAGE_LGD_CODE,
      assigned_asha_id: "usr-asha-kavitha-629375",
      members: [
        {
          id: "pat-murugan-selvam",
          name: "Murugan Selvam",
          relationship: "Head of Household",
          gender: "male",
          birth_date: "1992-04-10",
          age_years: 34,
          abha_id: "91-4432-8761-9021",
          immunizations_done: [],
          cbac_screened: true,
        },
        {
          id: "pat-deepa-murugan",
          name: "Deepa Murugan",
          relationship: "Spouse (Pregnant Mother)",
          gender: "female",
          birth_date: "1997-08-14",
          age_years: 29,
          abha_id: "91-4432-8761-9022",
          rch_id: "RCH-TN-2026-004522",
          is_pregnant: true,
          gestational_weeks: 20,
          gravida_para: "G1P0",
          immunizations_done: ["TT-1", "TT-2"],
          cbac_screened: true,
        },
      ],
    },
    {
      id: "hh-thazhambur-003",
      household_number: "THZ-WARD1-044",
      head_of_household: "Venkatesan Ramasamy",
      address_line: "No. 22, Mariamman Kovil Street",
      village_name: GEOGRAPHY.VILLAGE_NAME,
      village_lgd_code: GEOGRAPHY.VILLAGE_LGD_CODE,
      assigned_asha_id: "usr-asha-kavitha-629375",
      members: [
        {
          id: "pat-venkatesan-ramasamy",
          name: "Venkatesan Ramasamy",
          relationship: "Head of Household (Senior)",
          gender: "male",
          birth_date: "1964-02-18",
          age_years: 62,
          abha_id: "91-4432-8761-9031",
          immunizations_done: [],
          cbac_screened: true,
        },
        {
          id: "pat-kamala-venkatesan",
          name: "Kamala Venkatesan",
          relationship: "Spouse",
          gender: "female",
          birth_date: "1968-07-25",
          age_years: 58,
          abha_id: "91-4432-8761-9032",
          immunizations_done: [],
          cbac_screened: true,
        },
      ],
    },
    {
      id: "hh-thazhambur-004",
      household_number: "THZ-WARD1-045",
      head_of_household: "Ravi Chandran",
      address_line: "No. 29, North Mada Street",
      village_name: GEOGRAPHY.VILLAGE_NAME,
      village_lgd_code: GEOGRAPHY.VILLAGE_LGD_CODE,
      assigned_asha_id: "usr-asha-kavitha-629375",
      members: [
        {
          id: "pat-ravi-chandran",
          name: "Ravi Chandran",
          relationship: "Head of Household",
          gender: "male",
          birth_date: "1993-01-12",
          age_years: 33,
          abha_id: "91-4432-8761-9041",
          immunizations_done: [],
          cbac_screened: true,
        },
        {
          id: "pat-lakshmi-ravi",
          name: "Lakshmi Ravi",
          relationship: "Spouse (Postnatal Mother)",
          gender: "female",
          birth_date: "1998-05-30",
          age_years: 28,
          abha_id: "91-4432-8761-9042",
          rch_id: "RCH-TN-2025-003891",
          is_pregnant: false,
          immunizations_done: ["TT-1", "TT-2", "TT-Booster"],
          cbac_screened: true,
        },
        {
          id: "pat-baby-dharani",
          name: "Baby Dharani Ravi",
          relationship: "Infant (42 days)",
          gender: "female",
          birth_date: "2026-09-10",
          age_years: 0,
          abha_id: "91-4432-8761-9043",
          rch_id: "RCH-CHILD-TN-2026-091102",
          immunizations_done: ["BCG", "OPV-0", "HepB-0", "OPV-1", "Pentavalent-1", "Rota-1"],
          cbac_screened: false,
        },
      ],
    },
  ];

  // Generate Households 5 through 15 procedurally for realistic rural saturation
  const familySurnames = [
    "Karthik", "Subramanian", "Balaji", "Govindasamy", "Arumugam",
    "Senthil", "Velu", "Ganesan", "Saravanan", "Rajendran", "Dhanapal"
  ];

  for (let i = 5; i <= 15; i++) {
    const surname = familySurnames[i - 5];
    const ashaId = i <= 8 ? "usr-asha-kavitha-629375" : "usr-asha-selvi-629375";
    const pad = String(i).padStart(3, "0");

    households.push({
      id: `hh-thazhambur-${pad}`,
      household_number: `THZ-WARD${i % 3 + 1}-${100 + i}`,
      head_of_household: `${surname} Natarajan`,
      address_line: `No. ${i * 4}, Village High Road`,
      village_name: GEOGRAPHY.VILLAGE_NAME,
      village_lgd_code: GEOGRAPHY.VILLAGE_LGD_CODE,
      assigned_asha_id: ashaId,
      members: [
        {
          id: `pat-${surname.toLowerCase()}-head`,
          name: `${surname} Natarajan`,
          relationship: "Head of Household",
          gender: "male",
          birth_date: `198${i % 9}-0${(i % 9) + 1}-10`,
          age_years: 40 + (i % 10),
          abha_id: `91-4432-8761-${9050 + i}`,
          immunizations_done: [],
          cbac_screened: i % 2 === 0,
        },
        {
          id: `pat-${surname.toLowerCase()}-spouse`,
          name: `Vasanthi ${surname}`,
          relationship: "Spouse",
          gender: "female",
          birth_date: `199${i % 8}-0${(i % 8) + 1}-20`,
          age_years: 32 + (i % 8),
          abha_id: `91-4432-8761-${9070 + i}`,
          is_pregnant: i === 6 || i === 11,
          gestational_weeks: i === 6 ? 16 : i === 11 ? 28 : undefined,
          rch_id: (i === 6 || i === 11) ? `RCH-TN-2026-0045${i}` : undefined,
          immunizations_done: ["TT-1"],
          cbac_screened: true,
        },
      ],
    });
  }

  return households;
}

// ── 4. The 3 Production-Grade Clinical Scenarios ────────────────────────────
export interface ClinicalScenarioA {
  scenario_name: string;
  category: "HIGH_RISK_MATERNAL_TRIAGE";
  beneficiary: {
    patient_id: string;
    name: string;
    age: number;
    parity: string;
    gestational_age: string;
    abha_id: string;
    rch_id: string;
    household_id: string;
  };
  field_voice_transcripts: {
    regional_tamil: string;
    regional_hindi: string;
    sarvam_audio_file: string;
    sarvam_confidence: number;
  };
  bluetooth_device_vitals: {
    device_model: string;
    systolic_bp_mmhg: number;
    diastolic_bp_mmhg: number;
    hemoglobin_g_dl: number;
    fetal_heart_rate_bpm: number;
    temperature_f: number;
    spo2_percent: number;
  };
  mcp_clinical_triage: {
    risk_level: "HIGH";
    clinical_condition: string;
    snomed_code: string;
    danger_flags: string[];
    immediate_action: string;
  };
  escalation_triggers: {
    kestra_flow: string;
    phc_ticket_priority: string;
    dispatch_108_ambulance: boolean;
    sms_whatsapp_recipient: string;
    assigned_doctor: string;
  };
}

export interface ClinicalScenarioB {
  scenario_name: string;
  category: "PEDIATRIC_CARE_GAP_PROACTIVE_INTERCEPTION";
  beneficiary: {
    patient_id: string;
    name: string;
    age_months: number;
    gender: string;
    abha_id: string;
    rch_id: string;
    household_id: string;
  };
  overdue_immunizations: Array<{
    vaccine_code: string;
    vaccine_name: string;
    due_age: string;
    days_overdue: number;
    urgency: "HIGH" | "CRITICAL";
  }>;
  asha_copilot_behavior: {
    prompt_trigger: string;
    ui_card_color: "AMBER";
    localized_hesitancy_audio: {
      tamil_asset_url: string;
      tamil_script: string;
      hindi_asset_url: string;
      hindi_script: string;
    };
  };
}

export interface ClinicalScenarioC {
  scenario_name: string;
  category: "OFFLINE_SYNC_RESILIENCE_TELEMETRY";
  device_state: {
    connectivity: "OFFLINE";
    cache_backend: "SQLite / MMKV";
    offline_token_valid: boolean;
  };
  queued_offline_visits: Array<{
    visit_uuid: string;
    household_id: string;
    patient_id: string;
    beneficiary_name: string;
    encounter_type: string;
    audio_note_size_bytes: number;
    recorded_at: string;
  }>;
  reconnection_sync_flow: {
    batch_mutation: string;
    media_upload_bucket: string;
    telemetry_updates: {
      average_voice_doc_time_seconds: number;
      manual_baseline_seconds: number;
      doc_time_saved_percent: number;
      sync_success_rate: number;
      asr_confidence_score: number;
    };
  };
}

export const SCENARIO_A: ClinicalScenarioA = {
  scenario_name: "Scenario A: High-Risk Maternal Pre-Eclampsia Emergency Escalation",
  category: "HIGH_RISK_MATERNAL_TRIAGE",
  beneficiary: {
    patient_id: "pat-priya-anbarasan",
    name: "Priya Anbarasan",
    age: 26,
    parity: "G2P1",
    gestational_age: "32 weeks",
    abha_id: "91-4432-8761-9012",
    rch_id: "RCH-TN-2026-004521",
    household_id: "hh-thazhambur-001",
  },
  field_voice_transcripts: {
    regional_tamil:
      "அக்கா, எனக்கு மூணு நாளா கடுமையான தலைவலி இருக்கு, கண்ணு மங்கலா தெரியுது, ரெண்டு கால்லயும் ரொம்ப வீக்கம் வந்திருக்கு... இன்னைக்கு குழந்தை அசைவு கூட ரொம்ப குறைவா இருக்கு அக்கா.",
    regional_hindi:
      "दीदी, मुझे पिछले तीन दिनों से बहुत तेज सिरदर्द हो रहा है, आंखों के आगे धुंधलापन दिख रहा है और दोनों पैरों में बहुत सूजन आ गई है। बच्चा भी कम हिल रहा है।",
    sarvam_audio_file: "s3://asha-field-media/2026/10/22/audio_priya_preeclampsia_32w.opus",
    sarvam_confidence: 0.968,
  },
  bluetooth_device_vitals: {
    device_model: "Omron HEM-7120 Smart BLE BP Monitor",
    systolic_bp_mmhg: 152.0,
    diastolic_bp_mmhg: 98.0,
    hemoglobin_g_dl: 7.6,
    fetal_heart_rate_bpm: 118.0,
    temperature_f: 98.4,
    spo2_percent: 98.0,
  },
  mcp_clinical_triage: {
    risk_level: "HIGH",
    clinical_condition: "Severe Pre-eclampsia in 3rd Trimester with Moderate Anemia",
    snomed_code: "398254007",
    danger_flags: [
      "Systolic BP >= 140 mmHg (152 mmHg)",
      "Diastolic BP >= 90 mmHg (98 mmHg)",
      "Severe persistent headache & visual disturbance (scotoma)",
      "Bilateral pedal edema",
      "Reduced fetal movement (FHR 118 bpm)",
      "Hemoglobin < 8 g/dL (7.6 g/dL)",
    ],
    immediate_action: "Immediate Emergency Referral to PHC Thazhambur / 108 Ambulance Dispatch",
  },
  escalation_triggers: {
    kestra_flow: "sevafirst_frontline/high_risk_referral_flow.yml",
    phc_ticket_priority: "EMERGENCY_RED",
    dispatch_108_ambulance: true,
    sms_whatsapp_recipient: "+919444123456",
    assigned_doctor: "Dr. K. Radhakrishnan (MO, PHC Thazhambur)",
  },
};

export const SCENARIO_B: ClinicalScenarioB = {
  scenario_name: "Scenario B: Proactive Pediatric Immunization Gap Interception",
  category: "PEDIATRIC_CARE_GAP_PROACTIVE_INTERCEPTION",
  beneficiary: {
    patient_id: "pat-baby-kavin",
    name: "Baby Kavin Anbarasan",
    age_months: 14,
    gender: "male",
    abha_id: "91-4432-8761-9013",
    rch_id: "RCH-CHILD-TN-2025-089123",
    household_id: "hh-thazhambur-001",
  },
  overdue_immunizations: [
    {
      vaccine_code: "PENTAVALENT-3",
      vaccine_name: "Pentavalent 3 (DPT + HepB + Hib Booster)",
      due_age: "14 weeks",
      days_overdue: 240,
      urgency: "HIGH",
    },
    {
      vaccine_code: "MR-1",
      vaccine_name: "Measles-Rubella 1st Dose + Vitamin A",
      due_age: "9-12 months",
      days_overdue: 60,
      urgency: "CRITICAL",
    },
  ],
  asha_copilot_behavior: {
    prompt_trigger: "ON_HOUSEHOLD_VISIT_EXIT_CHECK",
    ui_card_color: "AMBER",
    localized_hesitancy_audio: {
      tamil_asset_url: "https://filenest.nhm.gov.in/api/v1/media/health-education/ta/mr_safety_counseling.opus",
      tamil_script:
        "அம்மா, தம்பி கவினுக்கு ஒரு வயசு முடிஞ்சிருச்சு. தட்டம்மை (Measles-Rubella) தடுப்பூசியும், பென்டாவேலன்ட் 3-வது தவணையும் இன்னும் போடல. தடுப்பூசி போடுவதால் குழந்தைக்கு எந்த ஆபத்தும் வராது. வர்ற புதன்கிழமை நம்ம ஆரம்ப சுகாதார நிலையத்துல (PHC) இலவசமா போட்டுடலாம் அம்மா.",
      hindi_asset_url: "https://filenest.nhm.gov.in/api/v1/media/health-education/hi/mr_safety_counseling.opus",
      hindi_script:
        "माताजी, कवीन 14 महीने का हो गया है। खसरा-रूबेला (MR-1) और पेंटावेलेंट-3 का टीका अभी बाकी है। टीका पूरी तरह सुरक्षित है। आने वाले बुधवार को उप-केंद्र पर अवश्य लगवाएं।",
    },
  },
};

export const SCENARIO_C: ClinicalScenarioC = {
  scenario_name: "Scenario C: Remote Offline Voice Sync & Telemetry Pipeline",
  category: "OFFLINE_SYNC_RESILIENCE_TELEMETRY",
  device_state: {
    connectivity: "OFFLINE",
    cache_backend: "SQLite / MMKV",
    offline_token_valid: true,
  },
  queued_offline_visits: [
    {
      visit_uuid: "vst-off-20261022-thz-001",
      household_id: "hh-thazhambur-002",
      patient_id: "pat-deepa-murugan",
      beneficiary_name: "Deepa Murugan (20w ANC)",
      encounter_type: "ANC_TRIMESTER_2_CHECKUP",
      audio_note_size_bytes: 42800,
      recorded_at: "2026-10-22T04:15:00Z",
    },
    {
      visit_uuid: "vst-off-20261022-thz-002",
      household_id: "hh-thazhambur-003",
      patient_id: "pat-venkatesan-ramasamy",
      beneficiary_name: "Venkatesan Ramasamy (62y Elder)",
      encounter_type: "NCD_CBAC_SCREENING",
      audio_note_size_bytes: 38200,
      recorded_at: "2026-10-22T04:35:00Z",
    },
    {
      visit_uuid: "vst-off-20261022-thz-003",
      household_id: "hh-thazhambur-004",
      patient_id: "pat-lakshmi-ravi",
      beneficiary_name: "Lakshmi Ravi (Postnatal Day 42)",
      encounter_type: "PNC_POSTNATAL_CHECKUP",
      audio_note_size_bytes: 51400,
      recorded_at: "2026-10-22T04:55:00Z",
    },
  ],
  reconnection_sync_flow: {
    batch_mutation: "sync_offline_field_visits",
    media_upload_bucket: "asha-field-media",
    telemetry_updates: {
      average_voice_doc_time_seconds: 91.2,
      manual_baseline_seconds: 480.0,
      doc_time_saved_percent: 81.0,
      sync_success_rate: 100.0,
      asr_confidence_score: 0.964,
    },
  },
};

// ── Master Seed Generator & Export ───────────────────────────────────────────
export function generateMasterSevaFirstDemoBundle() {
  const households = generate15Households();

  return {
    metadata: {
      project: "SevaFirst: AI Copilot for ASHA Workers & Frontline Health Teams",
      authority: "Government of India - National Health Mission (NHM)",
      standard: "ABDM / HL7 FHIR R4 / SNOMED-CT / LOINC",
      generated_at: new Date().toISOString(),
      state: GEOGRAPHY.STATE,
      district: GEOGRAPHY.DISTRICT,
      village: GEOGRAPHY.VILLAGE_NAME,
      village_lgd_code: GEOGRAPHY.VILLAGE_LGD_CODE,
    },
    phc_facility: PHC_THAZHAMBUR_SEED,
    asha_workers: ASHA_WORKERS_SEED,
    households: households,
    total_households_count: households.length,
    total_beneficiaries_count: households.reduce((acc, h) => acc + h.members.length, 0),
    clinical_scenarios: {
      scenario_a_maternal_emergency: SCENARIO_A,
      scenario_b_pediatric_care_gap: SCENARIO_B,
      scenario_c_offline_sync: SCENARIO_C,
    },
  };
}

// ── Standalone CLI Runner ───────────────────────────────────────────────────
export function runSeeding() {
  console.log("===============================================================================");
  console.log("  SEVAFIRST: MASTER SEED SCRIPT FOR FRONTLINE ASHA COPILOT DEMO DATA");
  console.log("===============================================================================");

  const bundle = generateMasterSevaFirstDemoBundle();

  const outDir = path.resolve(__dirname, "seed-data");
  if (!fs.existsSync(outDir)) {
    fs.mkdirSync(outDir, { recursive: true });
  }

  const outFilePath = path.join(outDir, "sevafirst-demo-dataset.json");
  fs.writeFileSync(outFilePath, JSON.stringify(bundle, null, 2), "utf-8");

  console.log(`✓ Master Seed Data compiled successfully!`);
  console.log(`  File: ${outFilePath}`);
  console.log(`-------------------------------------------------------------------------------`);
  console.log(`1. Primary Health Centre:`);
  console.log(`   - Facility: ${bundle.phc_facility.name} (LGD: ${bundle.phc_facility.village_lgd_code})`);
  console.log(`   - Medical Officer: ${bundle.phc_facility.medical_officer.name}`);
  console.log(`   - HPR ID: ${bundle.phc_facility.medical_officer.hpr_id}`);
  console.log(`   - Sub-centre Supplies Seeded: ${bundle.phc_facility.supplies_stock.length} inventory lines`);
  console.log(`-------------------------------------------------------------------------------`);
  console.log(`2. ASHA Frontline Workers:`);
  bundle.asha_workers.forEach((w, idx) => {
    console.log(`   - ASHA ${idx + 1}: ${w.name} (${w.role}) | Phone: ${w.phone} | HPR: ${w.hpr_id}`);
    console.log(`     Assigned Households: ${w.assigned_households.length} | 14-Day Offline Token: ${w.offline_token.token_id}`);
  });
  console.log(`-------------------------------------------------------------------------------`);
  console.log(`3. Rural Household Registry:`);
  console.log(`   - Seeded Households: ${bundle.total_households_count} (Groups)`);
  console.log(`   - Seeded Beneficiaries: ${bundle.total_beneficiaries_count} (Patients with ABHA & RCH IDs)`);
  console.log(`-------------------------------------------------------------------------------`);
  console.log(`4. Production Clinical Scenarios Ready in Mobile UI:`);
  console.log(`   [Scenario A] High-Risk Maternal: Priya Anbarasan (32w G2P1) -> BP 152/98 -> 108 Emergency Escalate`);
  console.log(`   [Scenario B] Pediatric Care Gap: Baby Kavin (14mo) -> Overdue Pentavalent-3 & MR-1 -> Audio Counseling`);
  console.log(`   [Scenario C] Offline Sync: 3 Voice Encounters Queued -> Auto-sync & Telemetry Update (81% time saved)`);
  console.log("===============================================================================");
}

// Run when executed
runSeeding();
