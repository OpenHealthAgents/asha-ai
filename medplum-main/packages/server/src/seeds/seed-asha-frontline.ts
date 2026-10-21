// SPDX-FileCopyrightText: Copyright Orangebot, Inc. and Medplum contributors
// SPDX-License-Identifier: Apache-2.0
import type {
  Group,
  Patient,
  RelatedPerson,
  QuestionnaireResponse,
  Immunization,
  ImmunizationRecommendation,
  Practitioner,
} from '@medplum/fhirtypes';
import {
  ABDM_SYSTEMS,
  ASHA_EXTENSIONS,
  CbacQuestionnaire,
  AncHighRiskQuestionnaire,
  ImnciPediatricTriageQuestionnaire,
  buildImmunizationRecommendations,
} from './asha-fhir-profiles';

/**
 * Generates sample rural household, maternal, and pediatric records for ASHA AI Copilot.
 */
export function generateAshaSeedBundle() {
  // 1. Frontline ASHA Practitioner
  const ashaPractitioner: Practitioner = {
    resourceType: 'Practitioner',
    id: 'practitioner-asha-sunita',
    identifier: [
      {
        system: ABDM_SYSTEMS.HPR_ID,
        value: 'HPR-ASHA-OR-215432',
      },
    ],
    name: [{ use: 'official', family: 'Devi', given: ['Sunita'] }],
    telecom: [{ system: 'phone', value: '+919876543210' }],
    gender: 'female',
  };

  // 2. Rural Head of Household (RelatedPerson)
  const headOfHousehold: RelatedPerson = {
    resourceType: 'RelatedPerson',
    id: 'relperson-hh-head-ramesh',
    patient: { reference: 'Patient/patient-asha-anita-patra' },
    relationship: [
      {
        coding: [
          {
            system: 'http://terminology.hl7.org/CodeSystem/v3-RoleCode',
            code: 'HUSB',
            display: 'Husband / Head of Household',
          },
        ],
      },
    ],
    name: [{ use: 'official', family: 'Patra', given: ['Ramesh'] }],
    telecom: [{ system: 'phone', value: '+919876500112' }],
    gender: 'male',
    address: [
      {
        line: ['House No. 42, Ward 3, Rampur Village'],
        city: 'Bhadrak',
        district: 'dist-bhadrak',
        state: 'Odisha',
        postalCode: '756100',
        country: 'India',
      },
    ],
  };

  // 3. Maternal Patient (High-Risk Pregnant Woman)
  const maternalPatient: Patient = {
    resourceType: 'Patient',
    id: 'patient-asha-anita-patra',
    identifier: [
      {
        system: ABDM_SYSTEMS.ABHA_NUMBER,
        value: '91-8842-1094-5512',
      },
      {
        system: ABDM_SYSTEMS.ABHA_ADDRESS,
        value: 'anita.patra@abdm',
      },
      {
        system: ABDM_SYSTEMS.RCH_ID,
        value: 'RCH-OR-215432-0941',
      },
    ],
    name: [{ use: 'official', family: 'Patra', given: ['Anita'] }],
    gender: 'female',
    birthDate: '1998-05-14',
    telecom: [{ system: 'phone', value: '+919876500112' }],
    address: [
      {
        use: 'home',
        line: ['House No. 42, Ward 3, Rampur'],
        city: 'Bhadrak',
        state: 'Odisha',
        postalCode: '756100',
      },
    ],
    extension: [
      {
        url: ASHA_EXTENSIONS.LGD_HIERARCHY,
        extension: [
          { url: 'state_code', valueString: 'OR' },
          { url: 'district_code', valueString: 'dist-bhadrak' },
          { url: 'block_code', valueString: 'blk-bhadrak' },
          { url: 'phc_id', valueString: 'phc-bhadrak-01' },
          { url: 'subcentre_id', valueString: 'sc-rampur-01' },
          { url: 'village_lgd_code', valueString: '215432' },
        ],
      },
      {
        url: ASHA_EXTENSIONS.ASHA_ASSIGNED,
        valueReference: { reference: `Practitioner/${ashaPractitioner.id}` },
      },
      {
        url: ASHA_EXTENSIONS.BPL_CARD,
        valueBoolean: true,
      },
      {
        url: ASHA_EXTENSIONS.HIGH_RISK_ANC,
        valueBoolean: true,
      },
    ],
  };

  // 4. Infant Patient (Anita's 2-month-old Child)
  const infantPatient: Patient = {
    resourceType: 'Patient',
    id: 'patient-asha-baby-aarav',
    identifier: [
      {
        system: ABDM_SYSTEMS.ABHA_NUMBER,
        value: '91-4412-9012-3321',
      },
      {
        system: ABDM_SYSTEMS.RCH_ID,
        value: 'RCH-OR-215432-0941-C1',
      },
    ],
    name: [{ use: 'official', family: 'Patra', given: ['Aarav'] }],
    gender: 'male',
    birthDate: '2026-08-15',
    extension: [
      {
        url: ASHA_EXTENSIONS.LGD_HIERARCHY,
        extension: [
          { url: 'state_code', valueString: 'OR' },
          { url: 'district_code', valueString: 'dist-bhadrak' },
          { url: 'block_code', valueString: 'blk-bhadrak' },
          { url: 'phc_id', valueString: 'phc-bhadrak-01' },
          { url: 'subcentre_id', valueString: 'sc-rampur-01' },
          { url: 'village_lgd_code', valueString: '215432' },
        ],
      },
      {
        url: ASHA_EXTENSIONS.ASHA_ASSIGNED,
        valueReference: { reference: `Practitioner/${ashaPractitioner.id}` },
      },
    ],
  };

  // 5. Adult Patient 45-years-old for CBAC NCD Screening
  const adultPatient: Patient = {
    resourceType: 'Patient',
    id: 'patient-asha-ramesh-patra',
    identifier: [
      {
        system: ABDM_SYSTEMS.ABHA_NUMBER,
        value: '91-7712-4432-8871',
      },
      {
        system: ABDM_SYSTEMS.ABHA_ADDRESS,
        value: 'ramesh.patra@abdm',
      },
    ],
    name: [{ use: 'official', family: 'Patra', given: ['Ramesh'] }],
    gender: 'male',
    birthDate: '1979-03-22',
    extension: [
      {
        url: ASHA_EXTENSIONS.LGD_HIERARCHY,
        extension: [
          { url: 'state_code', valueString: 'OR' },
          { url: 'district_code', valueString: 'dist-bhadrak' },
          { url: 'block_code', valueString: 'blk-bhadrak' },
          { url: 'phc_id', valueString: 'phc-bhadrak-01' },
          { url: 'subcentre_id', valueString: 'sc-rampur-01' },
          { url: 'village_lgd_code', valueString: '215432' },
        ],
      },
    ],
  };

  // 6. Rural Household Group
  const ruralHouseholdGroup: Group = {
    resourceType: 'Group',
    id: 'group-household-rampur-042',
    type: 'person',
    actual: true,
    name: 'Rampur Household HH-215432-042 (Patra Family)',
    characteristic: [
      {
        code: {
          coding: [{ system: ABDM_SYSTEMS.LGD_VILLAGE, code: 'village_lgd_code', display: 'Village LGD' }],
        },
        valueCodeableConcept: {
          coding: [{ system: ABDM_SYSTEMS.LGD_VILLAGE, code: '215432', display: 'Rampur' }],
        },
        exclude: false,
      },
      {
        code: {
          coding: [{ system: 'https://nhm.gov.in/subcentre', code: 'subcentre_id', display: 'Sub-Centre' }],
        },
        valueCodeableConcept: {
          coding: [{ code: 'sc-rampur-01', display: 'Rampur Sub-Centre' }],
        },
        exclude: false,
      },
      {
        code: {
          coding: [{ system: 'https://nhm.gov.in/phc', code: 'phc_id', display: 'Primary Health Centre' }],
        },
        valueCodeableConcept: {
          coding: [{ code: 'phc-bhadrak-01', display: 'Bhadrak PHC' }],
        },
        exclude: false,
      },
    ],
    extension: [
      {
        url: ASHA_EXTENSIONS.HEAD_OF_HOUSEHOLD,
        valueReference: { reference: `RelatedPerson/${headOfHousehold.id}` },
      },
    ],
    member: [
      { entity: { reference: `Patient/${maternalPatient.id}` } },
      { entity: { reference: `Patient/${infantPatient.id}` } },
      { entity: { reference: `Patient/${adultPatient.id}` } },
    ],
  };

  // 7. Structured CBAC QuestionnaireResponse
  const cbacResponse: QuestionnaireResponse = {
    resourceType: 'QuestionnaireResponse',
    id: 'qr-cbac-ramesh-patra',
    questionnaire: CbacQuestionnaire.url,
    status: 'completed',
    subject: { reference: `Patient/${adultPatient.id}` },
    author: { reference: `Practitioner/${ashaPractitioner.id}` },
    authored: '2026-10-18T10:30:00+05:30',
    item: [
      {
        linkId: 'part-a',
        item: [
          { linkId: 'cbac-age', answer: [{ valueCoding: { code: '0', display: '30-49 years' } }] },
          { linkId: 'cbac-tobacco', answer: [{ valueCoding: { code: '2', display: 'Yes, daily chewing' } }] },
          { linkId: 'cbac-alcohol', answer: [{ valueBoolean: false }] },
          { linkId: 'cbac-waist', answer: [{ valueDecimal: 92.5 }] },
          { linkId: 'cbac-physical-activity', answer: [{ valueBoolean: false }] },
          { linkId: 'cbac-family-history', answer: [{ valueBoolean: true }] },
          { linkId: 'cbac-total-score', answer: [{ valueInteger: 5 }] }, // Score 5 -> High risk, PHC referral required
        ],
      },
      {
        linkId: 'part-b',
        item: [
          { linkId: 'cbac-oral-signs', answer: [{ valueBoolean: true }] }, // Non-healing ulcer alert
        ],
      },
      {
        linkId: 'part-c',
        item: [
          { linkId: 'cbac-vision-cataract', answer: [{ valueBoolean: false }] },
          { linkId: 'cbac-mobility-unsteady', answer: [{ valueBoolean: false }] },
        ],
      },
    ],
  };

  // 8. Structured ANC High-Risk QuestionnaireResponse
  const ancResponse: QuestionnaireResponse = {
    resourceType: 'QuestionnaireResponse',
    id: 'qr-anc-anita-patra-visit3',
    questionnaire: AncHighRiskQuestionnaire.url,
    status: 'completed',
    subject: { reference: `Patient/${maternalPatient.id}` },
    author: { reference: `Practitioner/${ashaPractitioner.id}` },
    authored: '2026-10-20T09:15:00+05:30',
    item: [
      {
        linkId: 'anc-gestational-info',
        item: [
          { linkId: 'anc-lmp', answer: [{ valueDate: '2026-03-10' }] },
          { linkId: 'anc-edd', answer: [{ valueDate: '2026-12-17' }] },
          { linkId: 'anc-gestational-weeks', answer: [{ valueInteger: 32 }] },
          { linkId: 'anc-gravida', answer: [{ valueInteger: 2 }] },
          { linkId: 'anc-parity', answer: [{ valueInteger: 1 }] },
        ],
      },
      {
        linkId: 'anc-vitals-danger',
        item: [
          { linkId: 'anc-bp-systolic', answer: [{ valueInteger: 148 }] }, // Severe Preeclampsia danger
          { linkId: 'anc-bp-diastolic', answer: [{ valueInteger: 96 }] },
          { linkId: 'anc-pre-eclampsia', answer: [{ valueBoolean: true }] },
          { linkId: 'anc-hb', answer: [{ valueDecimal: 6.8 }] }, // Severe Anemia danger
          { linkId: 'anc-severe-anemia', answer: [{ valueBoolean: true }] },
          { linkId: 'anc-vaginal-bleeding', answer: [{ valueBoolean: false }] },
          { linkId: 'anc-pedal-edema', answer: [{ valueBoolean: true }] },
          { linkId: 'anc-fetal-movement-reduced', answer: [{ valueBoolean: false }] },
          { linkId: 'anc-previous-csection', answer: [{ valueBoolean: true }] },
        ],
      },
      {
        linkId: 'anc-triage-outcome',
        item: [
          { linkId: 'anc-is-high-risk', answer: [{ valueBoolean: true }] },
          { linkId: 'anc-referral-facility', answer: [{ valueString: 'Bhadrak PHC (Medical Officer Emergency Triage)' }] },
        ],
      },
    ],
  };

  // 9. Structured IMNCI Pediatric Triage QuestionnaireResponse
  const imnciResponse: QuestionnaireResponse = {
    resourceType: 'QuestionnaireResponse',
    id: 'qr-imnci-aarav-triage',
    questionnaire: ImnciPediatricTriageQuestionnaire.url,
    status: 'completed',
    subject: { reference: `Patient/${infantPatient.id}` },
    author: { reference: `Practitioner/${ashaPractitioner.id}` },
    authored: '2026-10-21T11:45:00+05:30',
    item: [
      {
        linkId: 'imnci-general-danger',
        item: [
          { linkId: 'imnci-unable-to-drink', answer: [{ valueBoolean: false }] },
          { linkId: 'imnci-vomits-everything', answer: [{ valueBoolean: false }] },
          { linkId: 'imnci-convulsions', answer: [{ valueBoolean: false }] },
          { linkId: 'imnci-lethargic-unconscious', answer: [{ valueBoolean: false }] },
        ],
      },
      {
        linkId: 'imnci-respiratory-assessment',
        item: [
          { linkId: 'imnci-cough-days', answer: [{ valueInteger: 3 }] },
          { linkId: 'imnci-respiratory-rate', answer: [{ valueInteger: 54 }] }, // Fast breathing in 2-month-old (>50 breaths/min)
          { linkId: 'imnci-chest-indrawing', answer: [{ valueBoolean: true }] }, // Subcostal indrawing = Severe Pneumonia
          { linkId: 'imnci-stridor', answer: [{ valueBoolean: false }] },
        ],
      },
      {
        linkId: 'imnci-dehydration-malnutrition',
        item: [
          { linkId: 'imnci-diarrhea-present', answer: [{ valueBoolean: false }] },
          { linkId: 'imnci-sunken-eyes', answer: [{ valueBoolean: false }] },
          { linkId: 'imnci-skin-pinch', answer: [{ valueCoding: { code: 'NORMAL', display: 'Goes back immediately' } }] },
          { linkId: 'imnci-muac', answer: [{ valueDecimal: 122.0 }] },
          { linkId: 'imnci-bilateral-edema', answer: [{ valueBoolean: false }] },
        ],
      },
      {
        linkId: 'imnci-classification-outcome',
        answer: [
          {
            valueCoding: {
              code: 'RED',
              display: 'RED: Severe Pneumonia with chest indrawing - Immediate PHC Emergency Referral & Oxygen',
            },
          },
        ],
      },
    ],
  };

  // 10. Administered Immunization (BCG, OPV-0, HepB-0)
  const immunizationBcg: Immunization = {
    resourceType: 'Immunization',
    id: 'imm-aarav-bcg',
    status: 'completed',
    vaccineCode: {
      coding: [{ system: ABDM_SYSTEMS.NIS_VACCINE_CODE, code: 'BCG', display: 'Bacillus Calmette-Guerin' }],
    },
    patient: { reference: `Patient/${infantPatient.id}` },
    occurrenceDateTime: '2026-08-16T10:00:00+05:30',
    primarySource: true,
    performer: [{ actor: { reference: `Practitioner/${ashaPractitioner.id}` } }],
  };

  // 11. NIS Immunization Recommendations
  const infantRecommendations = buildImmunizationRecommendations(infantPatient.id!, infantPatient.birthDate!, 'infant');
  const maternalRecommendations = buildImmunizationRecommendations(maternalPatient.id!, '2026-03-10', 'maternal');

  return {
    ashaPractitioner,
    headOfHousehold,
    maternalPatient,
    infantPatient,
    adultPatient,
    ruralHouseholdGroup,
    cbacResponse,
    ancResponse,
    imnciResponse,
    immunizationBcg,
    infantRecommendations,
    maternalRecommendations,
  };
}
