# ASHA AI (SevaFirst)
## Frontline Clinical AI Copilot for ASHA Workers & Health Teams

An offline-capable, multilingual, voice-first clinical triage and documentation assistant built for Accredited Social Health Activists (ASHAs), Auxiliary Nurse Midwives (ANMs), and Primary Health Centre (PHC) Medical Officers under the National Health Mission (NHM) and Ayushman Bharat Digital Mission (ABDM).

---

## 🏛️ Ecosystem Repositories

| Repository | Role in Architecture |
| :--- | :--- |
| **`DrGodly-Mobile-Aplication-main`** | Offline-first Flutter mobile client with "Tap & Speak" voice UI, BLE GATT device integration, and SQLite outbox. |
| **`bezs-iam-main`** | Frontline RBAC (`ROLE_ASHA`, `ROLE_ANM`, `ROLE_PHC_MO`), LGD metadata hierarchy, and 14-day cryptographic offline JWTs. |
| **`medplum-main`** | HL7 FHIR R4 clinical data repository with rural maternal/child profiles (ABHA, RCH, CBAC, ANC, IMNCI). |
| **`bezs-emr-gql-main`** | GraphQL API gateway for retrospective offline sync and village-level care gap calculation. |
| **`bezs-filenest-main`** | Resumable chunked audio note storage (`asha-field-media`) and pre-cached localized health education clips. |
| **`open-wearables-main`** | Point-of-care Bluetooth screening ingestion (BP cuffs, pulse oximeters, glucometers, digital hemoglobinometers). |
| **`langcare-mcp-fhir-main`** | Model Context Protocol (MCP) server for Sarvam ASR extraction, IMNCI red-flag evaluation, and regional counseling scripts. |
| **`kestra-develop` / `flows`** | Event-driven triage escalation workflows, 108 ambulance dispatch, WhatsApp referral slips, and weekly defaulter queues. |
| **`bezs-hms-main`** | PHC Medical Officer Web Command Center with high-risk referral queue, audio playback, and sub-centre stockout alerts. |
| **`bezs-observability-main`**| OpenTelemetry, Prometheus metrics, and tamper-proof SHA-256 clinical audit logging. |
| **`refactoragent-master`** | Cross-repo schema verification bridge and end-to-end clinical lifecycle integration test suite. |

---

## 🚀 Quickstart: Master Stack Deployment

### 1. Spin up the Integrated Stack
```bash
docker compose -f docker-compose.sevafirst.yml up -d
```

### 2. Seed Realistic Indian Rural Healthcare Data
```bash
node --experimental-strip-types seed-sevafirst-demo.ts
```
This seeds:
- **PHC Thazhambur** (Chengalpattu, Tamil Nadu) + Medical Officer Dr. K. Radhakrishnan (`ROLE_PHC_MO`).
- **2 ASHA Worker Accounts** (`Kavitha Sundaram` & `Selvi Murugan`) with 14-day offline cryptographic tokens.
- **15 Rural Households (`Group`)** with 33 beneficiaries, ABHA IDs, RCH tracking numbers, and immunization histories.
- **3 Clinical Demo Scenarios**:
  1. *Scenario A (High-Risk Maternal Triage)*: 26yo pregnant mother (32w), BP 152/98 mmHg, pre-eclampsia danger -> 108 Emergency Ambulance & PHC escalation.
  2. *Scenario B (Pediatric Care Gap)*: 14mo infant overdue for Pentavalent-3 and MR-1 -> Localized audio counseling for parental hesitancy.
  3. *Scenario C (Offline Sync Resilience)*: 3 voice visits queued in offline SQLite outbox -> Reconnect sync flushes to Medplum & MinIO with 81% documentation time saved.

### 3. Run Cross-Repo Contract Verification & Lifecycle Test
```bash
python refactoragent-master/tools/schema_bridge/contract_scanner.py
python refactoragent-master/test/test_complete_rural_visit_lifecycle.py
```

---

## 📜 Standards & Compliance
- **FHIR R4**: Profiles for `RuralHouseholdGroup`, `AshaPatient`, `Observation`, `RiskAssessment`, `QuestionnaireResponse`.
- **ABDM**: Ayushman Bharat Health Account (ABHA) and Healthcare Professionals Registry (HPR) alignment.
- **Vocabularies**: Standard LOINC codes for vitals and SNOMED-CT for maternal/pediatric conditions.
- **Clinical Protocols**: NHM ASHA Modules 6 & 7, IMNCI Pediatric Guidelines, and ANC High-Risk Checklists.
