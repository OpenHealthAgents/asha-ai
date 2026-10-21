// SPDX-FileCopyrightText: Copyright Orangebot, Inc. and Medplum contributors
// SPDX-License-Identifier: Apache-2.0
import type {
  Group,
  Patient,
  RelatedPerson,
  Questionnaire,
  QuestionnaireResponse,
  Immunization,
  ImmunizationRecommendation,
  StructureDefinition,
} from '@medplum/fhirtypes';

/**
 * ─────────────────────────────────────────────────────────────────────────────
 * ABDM & NHM India URL Constants & Identifiers
 * ─────────────────────────────────────────────────────────────────────────────
 */
export const ABDM_SYSTEMS = {
  ABHA_NUMBER: 'https://healthid.ndhm.gov.in',
  ABHA_ADDRESS: 'https://abdm.gov.in/abha-address',
  RCH_ID: 'https://rch.nhm.gov.in/rch/',
  HPR_ID: 'https://hpr.ndhm.gov.in',
  HFR_ID: 'https://facility.ndhm.gov.in',
  LGD_VILLAGE: 'https://lgdirectory.gov.in/village',
  LGD_DISTRICT: 'https://lgdirectory.gov.in/district',
  LGD_STATE: 'https://lgdirectory.gov.in/state',
  NIS_VACCINE_CODE: 'https://nhm.gov.in/nis/vaccines',
} as const;

export const ASHA_EXTENSIONS = {
  LGD_HIERARCHY: 'https://nrces.in/ndhm/fhir/r4/StructureDefinition/LgdHierarchy',
  ASHA_ASSIGNED: 'https://nrces.in/ndhm/fhir/r4/StructureDefinition/AshaWorkerAssigned',
  HEAD_OF_HOUSEHOLD: 'https://nrces.in/ndhm/fhir/r4/StructureDefinition/HeadOfHousehold',
  BPL_CARD: 'https://nrces.in/ndhm/fhir/r4/StructureDefinition/BplStatus',
  HIGH_RISK_ANC: 'https://nrces.in/ndhm/fhir/r4/StructureDefinition/HighRiskMaternalFlag',
} as const;

/**
 * ─────────────────────────────────────────────────────────────────────────────
 * 1. FHIR StructureDefinitions
 * ─────────────────────────────────────────────────────────────────────────────
 */

export const RuralHouseholdGroupProfile: StructureDefinition = {
  resourceType: 'StructureDefinition',
  id: 'RuralHouseholdGroup',
  url: 'https://nrces.in/ndhm/fhir/r4/StructureDefinition/RuralHouseholdGroup',
  name: 'RuralHouseholdGroup',
  title: 'Rural Frontline Household Group Profile',
  status: 'active',
  description: 'Represents a rural household unit managed by an ASHA worker, linked via village LGD code and Head of Household.',
  fhirVersion: '4.0.1',
  kind: 'resource',
  abstract: false,
  type: 'Group',
  baseDefinition: 'http://hl7.org/fhir/StructureDefinition/Group',
  derivation: 'constraint',
};

export const AshaPatientProfile: StructureDefinition = {
  resourceType: 'StructureDefinition',
  id: 'AshaPatient',
  url: 'https://nrces.in/ndhm/fhir/r4/StructureDefinition/AshaPatient',
  name: 'AshaPatient',
  title: 'Frontline Patient Profile (ABHA + RCH + LGD Hierarchy)',
  status: 'active',
  description: 'Rural frontline patient profile tracked by ASHA/ANM workers, linked to ABDM ABHA ID, RCH portal, and village LGD codes.',
  fhirVersion: '4.0.1',
  kind: 'resource',
  abstract: false,
  type: 'Patient',
  baseDefinition: 'http://hl7.org/fhir/StructureDefinition/Patient',
  derivation: 'constraint',
};

/**
 * ─────────────────────────────────────────────────────────────────────────────
 * 2. Community Based Assessment Checklist (CBAC) for NCDs (Age 30+)
 * ─────────────────────────────────────────────────────────────────────────────
 */
export const CbacQuestionnaire: Questionnaire = {
  resourceType: 'Questionnaire',
  id: 'cbac-ncd-v1',
  url: 'https://nhm.gov.in/fhir/r4/Questionnaire/CBAC-NCD-v1',
  name: 'CBAC_NCD_V1',
  title: 'Community Based Assessment Checklist (CBAC) for Early Detection of NCDs',
  status: 'active',
  subjectType: ['Patient'],
  description: 'Government of India National NCD Screening Checklist administered by ASHA workers for individuals aged 30 and older.',
  item: [
    {
      linkId: 'part-a',
      text: 'Part A: Risk Assessment (Scoring: 0 - 10)',
      type: 'group',
      item: [
        {
          linkId: 'cbac-age',
          text: 'What is your age category?',
          type: 'choice',
          required: true,
          answerOption: [
            { valueCoding: { code: '0', display: '30-49 years (Score: 0)' } },
            { valueCoding: { code: '1', display: '50-59 years (Score: 1)' } },
            { valueCoding: { code: '2', display: '60 years or above (Score: 2)' } },
          ],
        },
        {
          linkId: 'cbac-tobacco',
          text: 'Do you currently smoke or consume smokeless tobacco products (gutka/khaini)?',
          type: 'choice',
          required: true,
          answerOption: [
            { valueCoding: { code: '0', display: 'Never (Score: 0)' } },
            { valueCoding: { code: '1', display: 'Used to in the past, but quit (Score: 1)' } },
            { valueCoding: { code: '2', display: 'Yes, daily or occasionally (Score: 2)' } },
          ],
        },
        {
          linkId: 'cbac-alcohol',
          text: 'Do you consume alcohol daily or weekly?',
          type: 'boolean',
          required: true,
        },
        {
          linkId: 'cbac-waist',
          text: 'Waist circumference in centimetres',
          type: 'decimal',
          required: true,
        },
        {
          linkId: 'cbac-physical-activity',
          text: 'Do you undertake at least 150 minutes of physical activity per week?',
          type: 'boolean',
          required: true,
        },
        {
          linkId: 'cbac-family-history',
          text: 'Family history of High Blood Pressure, Diabetes or Heart Disease?',
          type: 'boolean',
          required: true,
        },
        {
          linkId: 'cbac-total-score',
          text: 'Total CBAC Risk Score (Calculated 0 to 10; Score >= 4 requires immediate PHC referral)',
          type: 'integer',
          required: true,
        },
      ],
    },
    {
      linkId: 'part-b',
      text: 'Part B: Early Warning Signs & Cancer Screening',
      type: 'group',
      item: [
        {
          linkId: 'cbac-oral-signs',
          text: 'Any white or red patch in the mouth, or non-healing mouth ulcer > 2 weeks?',
          type: 'boolean',
          required: true,
        },
        {
          linkId: 'cbac-breast-lump',
          text: 'For women: Any palpable lump in breast, nipple retraction or discharge?',
          type: 'boolean',
          required: false,
        },
        {
          linkId: 'cbac-cervical-bleeding',
          text: 'For women: Bleeding between periods, post-coital bleeding, or post-menopausal bleeding?',
          type: 'boolean',
          required: false,
        },
      ],
    },
    {
      linkId: 'part-c',
      text: 'Part C: Elderly Care, Mobility & Vision Screening',
      type: 'group',
      item: [
        {
          linkId: 'cbac-vision-cataract',
          text: 'Difficulty seeing distant objects or cloudy vision (suspected cataract)?',
          type: 'boolean',
          required: true,
        },
        {
          linkId: 'cbac-mobility-unsteady',
          text: 'Unsteady walking or history of falls in the past 6 months?',
          type: 'boolean',
          required: true,
        },
      ],
    },
  ],
};

/**
 * ─────────────────────────────────────────────────────────────────────────────
 * 3. Antenatal Care (ANC) High-Risk Checklist
 * ─────────────────────────────────────────────────────────────────────────────
 */
export const AncHighRiskQuestionnaire: Questionnaire = {
  resourceType: 'Questionnaire',
  id: 'anc-highrisk-v1',
  url: 'https://nhm.gov.in/fhir/r4/Questionnaire/ANC-HighRisk-v1',
  name: 'ANC_HighRisk_V1',
  title: 'Antenatal Care (ANC) High-Risk Maternal Screening Checklist',
  status: 'active',
  subjectType: ['Patient'],
  description: 'Guidelines for identification and immediate PHC escalation of High-Risk Pregnancies (HRP) by ASHA and ANM workers.',
  item: [
    {
      linkId: 'anc-gestational-info',
      text: 'Obstetric History & Gestational Timeline',
      type: 'group',
      item: [
        { linkId: 'anc-lmp', text: 'Last Menstrual Period (LMP) Date', type: 'date', required: true },
        { linkId: 'anc-edd', text: 'Expected Date of Delivery (EDD)', type: 'date', required: true },
        { linkId: 'anc-gestational-weeks', text: 'Current Gestational Age (weeks)', type: 'integer', required: true },
        { linkId: 'anc-gravida', text: 'Gravida (Total number of pregnancies)', type: 'integer', required: true },
        { linkId: 'anc-parity', text: 'Parity (Total viable deliveries)', type: 'integer', required: true },
      ],
    },
    {
      linkId: 'anc-vitals-danger',
      text: 'Clinical Danger Signs & Point-of-Care Vitals',
      type: 'group',
      item: [
        { linkId: 'anc-bp-systolic', text: 'Systolic Blood Pressure (mmHg)', type: 'integer', required: true },
        { linkId: 'anc-bp-diastolic', text: 'Diastolic Blood Pressure (mmHg)', type: 'integer', required: true },
        {
          linkId: 'anc-pre-eclampsia',
          text: 'Severe Pre-eclampsia Alert (BP >= 140/90 with headache or blurred vision)',
          type: 'boolean',
          required: true,
        },
        { linkId: 'anc-hb', text: 'Hemoglobin Level (g/dL)', type: 'decimal', required: true },
        {
          linkId: 'anc-severe-anemia',
          text: 'Severe Anemia Alert (Hb < 7.0 g/dL requiring urgent iron sucrose infusion / transfusion)',
          type: 'boolean',
          required: true,
        },
        { linkId: 'anc-vaginal-bleeding', text: 'Antepartum Hemorrhage / Active vaginal bleeding', type: 'boolean', required: true },
        { linkId: 'anc-pedal-edema', text: 'Severe bilateral pitting pedal edema or facial puffiness', type: 'boolean', required: true },
        { linkId: 'anc-fetal-movement-reduced', text: 'Reduced or absent fetal movements in last 12 hours', type: 'boolean', required: true },
        { linkId: 'anc-previous-csection', text: 'History of previous Cesarean Section or obstructed labour', type: 'boolean', required: true },
      ],
    },
    {
      linkId: 'anc-triage-outcome',
      text: 'Triage & Referral Determination',
      type: 'group',
      item: [
        {
          linkId: 'anc-is-high-risk',
          text: 'Is this a High-Risk Pregnancy (HRP) requiring urgent referral to PHC Medical Officer?',
          type: 'boolean',
          required: true,
        },
        {
          linkId: 'anc-referral-facility',
          text: 'Designated Referral Health Facility (PHC / CHC / District Hospital)',
          type: 'string',
          required: false,
        },
      ],
    },
  ],
};

/**
 * ─────────────────────────────────────────────────────────────────────────────
 * 4. IMNCI Pediatric Infection & Triage Checklist (0 - 59 Months)
 * ─────────────────────────────────────────────────────────────────────────────
 */
export const ImnciPediatricTriageQuestionnaire: Questionnaire = {
  resourceType: 'Questionnaire',
  id: 'imnci-pediatric-triage-v1',
  url: 'https://nhm.gov.in/fhir/r4/Questionnaire/IMNCI-Pediatric-Triage-v1',
  name: 'IMNCI_Pediatric_Triage_V1',
  title: 'Integrated Management of Neonatal & Childhood Illness (IMNCI) Triage Checklist',
  status: 'active',
  subjectType: ['Patient'],
  description: 'National protocol for rapid assessment of acute pediatric infections, respiratory distress, dehydration, and severe malnutrition in rural children under 5.',
  item: [
    {
      linkId: 'imnci-general-danger',
      text: 'General Danger Signs (Any YES = Immediate Emergency Referral)',
      type: 'group',
      item: [
        { linkId: 'imnci-unable-to-drink', text: 'Child unable to breastfeed or drink liquids', type: 'boolean', required: true },
        { linkId: 'imnci-vomits-everything', text: 'Child vomits everything consumed', type: 'boolean', required: true },
        { linkId: 'imnci-convulsions', text: 'Child had convulsions or fits during this illness episode', type: 'boolean', required: true },
        { linkId: 'imnci-lethargic-unconscious', text: 'Child is abnormally sleepy, lethargic or unresponsive', type: 'boolean', required: true },
      ],
    },
    {
      linkId: 'imnci-respiratory-assessment',
      text: 'Pneumonia & Respiratory Distress Assessment',
      type: 'group',
      item: [
        { linkId: 'imnci-cough-days', text: 'Duration of cough or difficulty breathing (days)', type: 'integer', required: true },
        { linkId: 'imnci-respiratory-rate', text: 'Respiratory Rate (breaths per minute counted for 60 seconds)', type: 'integer', required: true },
        { linkId: 'imnci-chest-indrawing', text: 'Subcostal chest indrawing present in calm child', type: 'boolean', required: true },
        { linkId: 'imnci-stridor', text: 'Stridor heard while child is calm and resting', type: 'boolean', required: true },
      ],
    },
    {
      linkId: 'imnci-dehydration-malnutrition',
      text: 'Diarrhea, Dehydration & Malnutrition Screening',
      type: 'group',
      item: [
        { linkId: 'imnci-diarrhea-present', text: 'Child has loose watery stools or diarrhea', type: 'boolean', required: true },
        { linkId: 'imnci-sunken-eyes', text: 'Sunken eyes present', type: 'boolean', required: true },
        {
          linkId: 'imnci-skin-pinch',
          text: 'Abdominal skin pinch test',
          type: 'choice',
          required: true,
          answerOption: [
            { valueCoding: { code: 'NORMAL', display: 'Goes back immediately (< 1s)' } },
            { valueCoding: { code: 'SLOW', display: 'Goes back slowly (1 - 2s)' } },
            { valueCoding: { code: 'VERY_SLOW', display: 'Goes back very slowly (> 2s) - Severe Dehydration' } },
          ],
        },
        {
          linkId: 'imnci-muac',
          text: 'Mid-Upper Arm Circumference (MUAC) in millimetres (< 115mm indicates Severe Acute Malnutrition)',
          type: 'decimal',
          required: true,
        },
        { linkId: 'imnci-bilateral-edema', text: 'Bilateral pitting edema of both feet (Kwashiorkor sign)', type: 'boolean', required: true },
      ],
    },
    {
      linkId: 'imnci-classification-outcome',
      text: 'IMNCI Colour-Coded Triage Classification',
      type: 'choice',
      required: true,
      answerOption: [
        { valueCoding: { code: 'RED', display: 'RED: Severe Pneumonia / Dehydration / SAM - Emergency PHC Ambulance Referral' } },
        { valueCoding: { code: 'YELLOW', display: 'YELLOW: Some Dehydration / Moderate Illness - Sub-centre ANM Oral Antibiotics / ORS' } },
        { valueCoding: { code: 'GREEN', display: 'GREEN: No Pneumonia / Mild Cold - Home Care, Continued Breastfeeding & Zinc' } },
      ],
    },
  ],
};

/**
 * ─────────────────────────────────────────────────────────────────────────────
 * 5. National Immunization Schedule (NIS) India Seed Templates
 * ─────────────────────────────────────────────────────────────────────────────
 */
export interface NisVaccineDefinition {
  code: string;
  display: string;
  targetAgeWeeks: number;
  targetAgeMonths?: number;
  doseNumber: number;
  series: string;
  category: 'infant' | 'child' | 'maternal';
}

export const NATIONAL_IMMUNIZATION_SCHEDULE: NisVaccineDefinition[] = [
  // At Birth
  { code: 'BCG', display: 'Bacillus Calmette-Guerin (BCG)', targetAgeWeeks: 0, doseNumber: 1, series: 'BCG', category: 'infant' },
  { code: 'OPV-0', display: 'Oral Polio Vaccine Birth Dose (OPV-0)', targetAgeWeeks: 0, doseNumber: 0, series: 'OPV', category: 'infant' },
  { code: 'HepB-0', display: 'Hepatitis B Birth Dose', targetAgeWeeks: 0, doseNumber: 0, series: 'HepB', category: 'infant' },

  // 6 Weeks
  { code: 'PENTA-1', display: 'Pentavalent 1 (DPT + HepB + Hib)', targetAgeWeeks: 6, doseNumber: 1, series: 'Pentavalent', category: 'infant' },
  { code: 'OPV-1', display: 'Oral Polio Vaccine 1 (OPV-1)', targetAgeWeeks: 6, doseNumber: 1, series: 'OPV', category: 'infant' },
  { code: 'ROTA-1', display: 'Rotavirus Vaccine 1', targetAgeWeeks: 6, doseNumber: 1, series: 'Rotavirus', category: 'infant' },
  { code: 'fIPV-1', display: 'Fractional IPV 1', targetAgeWeeks: 6, doseNumber: 1, series: 'fIPV', category: 'infant' },
  { code: 'PCV-1', display: 'Pneumococcal Conjugate Vaccine 1', targetAgeWeeks: 6, doseNumber: 1, series: 'PCV', category: 'infant' },

  // 10 Weeks
  { code: 'PENTA-2', display: 'Pentavalent 2 (DPT + HepB + Hib)', targetAgeWeeks: 10, doseNumber: 2, series: 'Pentavalent', category: 'infant' },
  { code: 'OPV-2', display: 'Oral Polio Vaccine 2 (OPV-2)', targetAgeWeeks: 10, doseNumber: 2, series: 'OPV', category: 'infant' },
  { code: 'ROTA-2', display: 'Rotavirus Vaccine 2', targetAgeWeeks: 10, doseNumber: 2, series: 'Rotavirus', category: 'infant' },

  // 14 Weeks
  { code: 'PENTA-3', display: 'Pentavalent 3 (DPT + HepB + Hib)', targetAgeWeeks: 14, doseNumber: 3, series: 'Pentavalent', category: 'infant' },
  { code: 'OPV-3', display: 'Oral Polio Vaccine 3 (OPV-3)', targetAgeWeeks: 14, doseNumber: 3, series: 'OPV', category: 'infant' },
  { code: 'ROTA-3', display: 'Rotavirus Vaccine 3', targetAgeWeeks: 14, doseNumber: 3, series: 'Rotavirus', category: 'infant' },
  { code: 'fIPV-2', display: 'Fractional IPV 2', targetAgeWeeks: 14, doseNumber: 2, series: 'fIPV', category: 'infant' },
  { code: 'PCV-2', display: 'Pneumococcal Conjugate Vaccine 2', targetAgeWeeks: 14, doseNumber: 2, series: 'PCV', category: 'infant' },

  // 9 - 12 Months
  { code: 'MR-1', display: 'Measles-Rubella 1', targetAgeWeeks: 39, targetAgeMonths: 9, doseNumber: 1, series: 'MR', category: 'infant' },
  { code: 'JE-1', display: 'Japanese Encephalitis 1 (Endemic districts)', targetAgeWeeks: 39, targetAgeMonths: 9, doseNumber: 1, series: 'JE', category: 'infant' },
  { code: 'PCV-BOOSTER', display: 'Pneumococcal Conjugate Booster', targetAgeWeeks: 39, targetAgeMonths: 9, doseNumber: 3, series: 'PCV', category: 'infant' },
  { code: 'VITA-1', display: 'Vitamin A First Dose (1 Lakh IU)', targetAgeWeeks: 39, targetAgeMonths: 9, doseNumber: 1, series: 'VitaminA', category: 'infant' },

  // 16 - 24 Months
  { code: 'MR-2', display: 'Measles-Rubella 2', targetAgeWeeks: 69, targetAgeMonths: 16, doseNumber: 2, series: 'MR', category: 'child' },
  { code: 'DPT-BOOSTER-1', display: 'DPT First Booster', targetAgeWeeks: 69, targetAgeMonths: 16, doseNumber: 4, series: 'DPT', category: 'child' },
  { code: 'OPV-BOOSTER', display: 'OPV Booster', targetAgeWeeks: 69, targetAgeMonths: 16, doseNumber: 4, series: 'OPV', category: 'child' },

  // Maternal Vaccines
  { code: 'TD-1', display: 'Tetanus-Diphtheria Toxoid (Td-1) in Pregnancy', targetAgeWeeks: 0, doseNumber: 1, series: 'Td-Maternal', category: 'maternal' },
  { code: 'TD-2', display: 'Tetanus-Diphtheria Toxoid (Td-2) in Pregnancy (4 wks after Td-1)', targetAgeWeeks: 4, doseNumber: 2, series: 'Td-Maternal', category: 'maternal' },
  { code: 'TD-BOOSTER', display: 'Td Booster (if vaccinated in last 3 years)', targetAgeWeeks: 0, doseNumber: 3, series: 'Td-Maternal', category: 'maternal' },
];

/**
 * Generates an NIS Immunization Recommendation Bundle for an infant or pregnant mother.
 */
export function buildImmunizationRecommendations(
  patientId: string,
  birthDateIso: string,
  category: 'infant' | 'maternal' = 'infant'
): ImmunizationRecommendation {
  const birthDate = new Date(birthDateIso);

  const recommendations = NATIONAL_IMMUNIZATION_SCHEDULE.filter((v) =>
    category === 'infant' ? (v.category === 'infant' || v.category === 'child') : v.category === 'maternal'
  ).map((vaccine) => {
    const dueDate = new Date(birthDate);
    dueDate.setDate(dueDate.getDate() + vaccine.targetAgeWeeks * 7);

    return {
      vaccineCode: [
        {
          coding: [
            {
              system: ABDM_SYSTEMS.NIS_VACCINE_CODE,
              code: vaccine.code,
              display: vaccine.display,
            },
          ],
        },
      ],
      targetDisease: {
        coding: [{ system: 'http://hl7.org/fhir/sid/icd-10', code: vaccine.series }],
      },
      forecastStatus: {
        coding: [
          {
            system: 'http://terminology.hl7.org/CodeSystem/immunization-recommendation-status',
            code: 'due',
            display: 'Due',
          },
        ],
      },
      dateCriterion: [
        {
          code: {
            coding: [
              {
                system: 'http://loinc.org',
                code: '30980-7',
                display: 'Date vaccine due',
              },
            ],
          },
          value: dueDate.toISOString().slice(0, 10),
        },
      ],
      doseNumberPositiveInt: vaccine.doseNumber,
      series: vaccine.series,
    };
  });

  return {
    resourceType: 'ImmunizationRecommendation',
    id: `recom-${patientId}`,
    patient: { reference: `Patient/${patientId}` },
    date: new Date().toISOString(),
    recommendation: recommendations,
  };
}
