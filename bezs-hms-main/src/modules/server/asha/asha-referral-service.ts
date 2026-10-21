/**
 * Frontline ASHA Referrals & PHC Triage Domain Service.
 * Connects village fieldwork from DrGodly & langcare-mcp-fhir to bezs-hms.
 */

export interface HighRiskReferralTicket {
  ticketId: string;
  patientId: string;
  patientName: string;
  patientPhone: string;
  villageLgdCode: string;
  villageName: string;
  phcId: string;
  subcentreId: string;
  workerId: string;
  workerName: string;
  riskLevel: "HIGH" | "MODERATE" | "LOW";
  category: "MATERNAL_PREECLAMPSIA" | "MATERNAL_SEVERE_ANEMIA" | "PEDIATRIC_INFECTION" | "NEONATAL_DANGER";
  dangerFlags: string[];
  vitals: {
    systolicBp?: number;
    diastolicBp?: number;
    hemoglobin?: number;
    spo2?: number;
    temperatureC?: number;
    fetalHeartRate?: number;
    pulse?: number;
  };
  voiceAudioUrl?: string;
  clinicalNotes: string;
  status: "PENDING_ARRIVAL" | "ARRIVED_AT_PHC" | "108_AMBULANCE_DISPATCHED" | "RESOLVED";
  escalatedAt: string;
  arrivalVerifiedAt?: string;
}

export interface SupplyStockoutAlert {
  alertId: string;
  subcentreId: string;
  subcentreName: string;
  villageLgdCode: string;
  workerId: string;
  workerName: string;
  itemCode: "ORS_PACKETS" | "IFA_TABLETS" | "UPT_KITS" | "PARACETAMOL_SYRUP" | "ZINC_TABLETS";
  itemName: string;
  stockStatus: "CRITICAL_STOCKOUT" | "LOW_STOCK";
  quantityRequested: number;
  currentStock: number;
  reportedViaVoice: boolean;
  voiceTranscriptSnippet: string;
  reportedAt: string;
  approvalStatus: "PENDING_APPROVAL" | "APPROVED_DISPATCHED" | "REJECTED";
}

// In-memory backing store for live demo and offline-synced instances
const highRiskReferralsStore: HighRiskReferralTicket[] = [
  {
    ticketId: "TKT-REF-2026-901",
    patientId: "patient-asha-anita-patra",
    patientName: "Anita Patra",
    patientPhone: "+919876500112",
    villageLgdCode: "215432",
    villageName: "Rampur Ward 3",
    phcId: "phc-rampur-central",
    subcentreId: "sc-rampur-01",
    workerId: "usr-asha-sunita",
    workerName: "Sunita Behera (ASHA)",
    riskLevel: "HIGH",
    category: "MATERNAL_PREECLAMPSIA",
    dangerFlags: [
      "Blood Pressure 148/96 mmHg (>= 140/90 danger threshold)",
      "Severe Maternal Anemia: Hb 6.4 g/dL (< 7.0 g/dL)",
      "Antepartum spotting / vaginal bleeding reported",
      "Bilateral pedal edema and severe headache",
    ],
    vitals: {
      systolicBp: 148,
      diastolicBp: 96,
      hemoglobin: 6.4,
      spo2: 95,
      temperatureC: 37.1,
      fetalHeartRate: 138,
      pulse: 88,
    },
    voiceAudioUrl: "http://localhost:8002/api/v1/media/asha/stream/anc_visit_audio_01.opus",
    clinicalNotes:
      "Gravida 2 Para 1, 32 weeks gestation. Severe pre-eclampsia warning signs with high BP and pedal edema. Family advised for immediate 108 ambulance transfer to Rampur PHC/FRU.",
    status: "108_AMBULANCE_DISPATCHED",
    escalatedAt: "2026-10-22T08:15:00Z",
  },
  {
    ticketId: "TKT-REF-2026-902",
    patientId: "patient-asha-baby-aarav",
    patientName: "Baby Aarav Patra (8 Months)",
    patientPhone: "+919876500112",
    villageLgdCode: "215432",
    villageName: "Rampur Ward 3",
    phcId: "phc-rampur-central",
    subcentreId: "sc-rampur-01",
    workerId: "usr-asha-sunita",
    workerName: "Sunita Behera (ASHA)",
    riskLevel: "HIGH",
    category: "PEDIATRIC_INFECTION",
    dangerFlags: [
      "Lower chest wall indrawing (Severe Pneumonia)",
      "Fast breathing (RR 56 breaths/min)",
      "Inability to breastfeed / suckle",
      "High fever: 39.2 deg C with SpO2 89%",
    ],
    vitals: {
      temperatureC: 39.2,
      spo2: 89,
      pulse: 142,
    },
    voiceAudioUrl: "http://localhost:8002/api/v1/media/asha/stream/pediatric_triage_02.opus",
    clinicalNotes:
      "IMNCI Pink Category: Severe Pneumonia / Very Severe Disease. Immediate oxygen therapy and intravenous/oral amoxicillin required upon arrival.",
    status: "PENDING_ARRIVAL",
    escalatedAt: "2026-10-22T09:30:00Z",
  },
];

const supplyStockoutsStore: SupplyStockoutAlert[] = [
  {
    alertId: "SUP-ALERT-101",
    subcentreId: "sc-rampur-01",
    subcentreName: "Rampur Sub-Centre",
    villageLgdCode: "215432",
    workerId: "usr-asha-sunita",
    workerName: "Sunita Behera (ASHA)",
    itemCode: "IFA_TABLETS",
    itemName: "Iron and Folic Acid (IFA) Tablets (Red)",
    stockStatus: "CRITICAL_STOCKOUT",
    quantityRequested: 500,
    currentStock: 0,
    reportedViaVoice: true,
    voiceTranscriptSnippet: "दीदी हमारे उप-केंद्र में गर्भवती महिलाओं के लिए लाल वाली आयरन की गोली (IFA) पूरी तरह खत्म हो गई है।",
    reportedAt: "2026-10-22T07:45:00Z",
    approvalStatus: "PENDING_APPROVAL",
  },
  {
    alertId: "SUP-ALERT-102",
    subcentreId: "sc-rampur-01",
    subcentreName: "Rampur Sub-Centre",
    villageLgdCode: "215432",
    workerId: "usr-anm-meena",
    workerName: "Meena Kumari (ANM)",
    itemCode: "ORS_PACKETS",
    itemName: "Oral Rehydration Salt (ORS) WHO Packets",
    stockStatus: "LOW_STOCK",
    quantityRequested: 200,
    currentStock: 12,
    reportedViaVoice: true,
    voiceTranscriptSnippet: "ଝାଡ଼ା ରୋଗ ପାଇଁ ORS ପ୍ୟାକେଟ ଆଉ ମାତ୍ର ୧୨ ଟି ବଳିଛି, ନୂଆ ପ୍ୟାକେଟ ଦରକାର।",
    reportedAt: "2026-10-22T08:00:00Z",
    approvalStatus: "PENDING_APPROVAL",
  },
  {
    alertId: "SUP-ALERT-103",
    subcentreId: "sc-rampur-02",
    subcentreName: "Gopalpur Sub-Centre",
    villageLgdCode: "215433",
    workerId: "usr-asha-radha",
    workerName: "Radha Murmu (ASHA)",
    itemCode: "UPT_KITS",
    itemName: "Nischay Urine Pregnancy Test (UPT) Kits",
    stockStatus: "CRITICAL_STOCKOUT",
    quantityRequested: 100,
    currentStock: 0,
    reportedViaVoice: true,
    voiceTranscriptSnippet: "नए विवाह वाले घरों में जांच के लिए यूपीटी किट खत्म हो गई हैं।",
    reportedAt: "2026-10-22T08:30:00Z",
    approvalStatus: "APPROVED_DISPATCHED",
  },
];

export class AshaReferralService {
  static getHighRiskReferrals(): HighRiskReferralTicket[] {
    return [...highRiskReferralsStore];
  }

  static createReferral(data: Partial<HighRiskReferralTicket>): HighRiskReferralTicket {
    const ticketId = `TKT-REF-2026-${Math.floor(100 + Math.random() * 900)}`;
    const newTicket: HighRiskReferralTicket = {
      ticketId,
      patientId: data.patientId || "patient-unknown",
      patientName: data.patientName || "Beneficiary",
      patientPhone: data.patientPhone || "+919876543210",
      villageLgdCode: data.villageLgdCode || "215432",
      villageName: data.villageName || `Village LGD ${data.villageLgdCode || "215432"}`,
      phcId: data.phcId || "phc-rampur-central",
      subcentreId: data.subcentreId || "sc-rampur-01",
      workerId: data.workerId || "usr-asha-sunita",
      workerName: data.workerName || "ASHA Worker",
      riskLevel: data.riskLevel || "HIGH",
      category: data.category || "MATERNAL_PREECLAMPSIA",
      dangerFlags: data.dangerFlags || [],
      vitals: data.vitals || {},
      voiceAudioUrl: data.voiceAudioUrl,
      clinicalNotes: data.clinicalNotes || "Automated frontline triage escalation.",
      status: "PENDING_ARRIVAL",
      escalatedAt: data.escalatedAt || new Date().toISOString(),
    };

    highRiskReferralsStore.unshift(newTicket);
    return newTicket;
  }

  static updateReferralStatus(
    ticketId: string,
    status: HighRiskReferralTicket["status"],
  ): HighRiskReferralTicket | null {
    const item = highRiskReferralsStore.find((t) => t.ticketId === ticketId);
    if (!item) return null;
    item.status = status;
    if (status === "ARRIVED_AT_PHC") {
      item.arrivalVerifiedAt = new Date().toISOString();
    }
    return item;
  }

  static getSupplyStockouts(): SupplyStockoutAlert[] {
    return [...supplyStockoutsStore];
  }

  static createSupplyAlert(data: Partial<SupplyStockoutAlert>): SupplyStockoutAlert {
    const alertId = `SUP-ALERT-${Math.floor(100 + Math.random() * 900)}`;
    const newAlert: SupplyStockoutAlert = {
      alertId,
      subcentreId: data.subcentreId || "sc-rampur-01",
      subcentreName: data.subcentreName || "Sub-Centre",
      villageLgdCode: data.villageLgdCode || "215432",
      workerId: data.workerId || "usr-asha-sunita",
      workerName: data.workerName || "ASHA Worker",
      itemCode: data.itemCode || "IFA_TABLETS",
      itemName: data.itemName || "Essential Drug Kit Item",
      stockStatus: data.stockStatus || "CRITICAL_STOCKOUT",
      quantityRequested: data.quantityRequested || 100,
      currentStock: data.currentStock || 0,
      reportedViaVoice: data.reportedViaVoice ?? true,
      voiceTranscriptSnippet: data.voiceTranscriptSnippet || "",
      reportedAt: new Date().toISOString(),
      approvalStatus: "PENDING_APPROVAL",
    };

    supplyStockoutsStore.unshift(newAlert);
    return newAlert;
  }

  static approveSupplyDispatch(alertId: string): SupplyStockoutAlert | null {
    const alert = supplyStockoutsStore.find((a) => a.alertId === alertId);
    if (!alert) return null;
    alert.approvalStatus = "APPROVED_DISPATCHED";
    return alert;
  }
}
