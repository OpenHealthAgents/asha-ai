/**
 * Seed runner for ASHA AI Frontline Healthcare FHIR R4 Profiles & Data.
 * Generates and writes the full FHIR R4 Transaction Bundle.
 */

import * as fs from 'fs';
import * as path from 'path';
import {
  RuralHouseholdGroupProfile,
  AshaPatientProfile,
  CbacQuestionnaire,
  AncHighRiskQuestionnaire,
  ImnciPediatricTriageQuestionnaire,
} from '../packages/server/src/seeds/asha-fhir-profiles';
import { generateAshaSeedBundle } from '../packages/server/src/seeds/seed-asha-frontline';

async function main() {
  console.log('================================================================');
  console.log('   Compiling Medplum FHIR R4 ASHA Healthcare Transaction Bundle ');
  console.log('================================================================');

  const seed = generateAshaSeedBundle();

  const resources = [
    // 1. StructureDefinitions
    RuralHouseholdGroupProfile,
    AshaPatientProfile,

    // 2. Questionnaires
    CbacQuestionnaire,
    AncHighRiskQuestionnaire,
    ImnciPediatricTriageQuestionnaire,

    // 3. Practitioner & Patients
    seed.ashaPractitioner,
    seed.headOfHousehold,
    seed.maternalPatient,
    seed.infantPatient,
    seed.adultPatient,

    // 4. Household Group
    seed.ruralHouseholdGroup,

    // 5. QuestionnaireResponses (CBAC, ANC High-Risk, IMNCI)
    seed.cbacResponse,
    seed.ancResponse,
    seed.imnciResponse,

    // 6. Immunization & Recommendations
    seed.immunizationBcg,
    seed.infantRecommendations,
    seed.maternalRecommendations,
  ];

  const transactionBundle = {
    resourceType: 'Bundle',
    type: 'transaction',
    entry: resources.map((res) => ({
      resource: res,
      request: {
        method: 'PUT',
        url: `${res.resourceType}/${res.id}`,
      },
    })),
  };

  const outputPath = path.resolve(__dirname, 'asha-frontline-fhir-bundle.json');
  fs.writeFileSync(outputPath, JSON.stringify(transactionBundle, null, 2), 'utf-8');

  console.log(`✓ Successfully compiled FHIR R4 Transaction Bundle with ${resources.length} resources.`);
  console.log(`✓ Bundle saved to: ${outputPath}`);
  console.log('\nIncluded Resources:');
  for (const r of resources) {
    console.log(`  - [${r.resourceType}] ${r.id} (${(r as any).title ?? (r as any).name ?? ''})`);
  }
}

main().catch((err) => {
  console.error('Error compiling FHIR bundle:', err);
  process.exit(1);
});
