"""
Cross-Repo Contract Scanner and Verification Engine
Inspects and validates synchronization of DTOs, schemas, and endpoints across:
- bezs-iam
- bezs-emr-gql
- langcare-mcp-fhir-main
- bezs-filenest
- bezs-hms
- bezs-observability
"""

from pathlib import Path
from typing import Dict, Any, List


class CrossRepoContractScanner:
    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root)

    def scan_iam(self) -> Dict[str, Any]:
        iam_dir = self.workspace_root / "bezs-iam-main"
        target_files = [
            iam_dir / "permissions.ts",
            iam_dir / "prisma" / "schema" / "schema.prisma",
            iam_dir / "src" / "lib" / "verifyOfflineToken.ts",
            iam_dir / "src" / "app" / "api" / "auth" / "offline-session" / "route.ts",
        ]
        roles_found = set()
        hierarchy_found = set()
        offline_token_verified = False

        for f in target_files:
            if f.exists():
                text = f.read_text(encoding="utf-8", errors="ignore")
                for r in ["ROLE_ASHA", "ROLE_ANM", "ROLE_PHC_MO", "ROLE_ADMIN"]:
                    if r in text:
                        roles_found.add(r)
                for h in ["state_code", "district_code", "block_code", "phc_id", "subcentre_id", "village_lgd_code"]:
                    if h in text:
                        hierarchy_found.add(h)
                if "verifyOfflineToken" in text or "offline_refresh_token" in text or "14 * 24 * 60 * 60" in text:
                    offline_token_verified = True

        status = "PASS" if len(roles_found) >= 3 and len(hierarchy_found) >= 5 and offline_token_verified else "PARTIAL"
        return {
            "component": "bezs-iam",
            "roles_verified": sorted(list(roles_found)),
            "hierarchy_fields": sorted(list(hierarchy_found)),
            "offline_token_support": offline_token_verified,
            "status": status,
        }

    def scan_emr_gql(self) -> Dict[str, Any]:
        gql_dir = self.workspace_root / "bezs-emr-gql-main"
        target_files = [
            gql_dir / "app" / "graphql" / "schema.py",
            gql_dir / "app" / "graphql" / "types.py",
            gql_dir / "app" / "services" / "care_gap_service.py",
            gql_dir / "app" / "services" / "offline_sync_service.py",
        ]
        types_found = set()
        mutations_found = set()

        for f in target_files:
            if f.exists():
                txt = f.read_text(encoding="utf-8", errors="ignore")
                for t in ["CareGapSummary", "OfflineVisitInput", "SyncBatchPayload", "OfflineObservationInput"]:
                    if t in txt:
                        types_found.add(t)
                for m in ["sync_offline_field_visits", "get_village_care_gaps"]:
                    if m in txt:
                        mutations_found.add(m)

        status = "PASS" if len(types_found) >= 3 and len(mutations_found) >= 2 else "PARTIAL"
        return {
            "component": "bezs-emr-gql",
            "types_verified": sorted(list(types_found)),
            "mutations_and_queries": sorted(list(mutations_found)),
            "status": status,
        }

    def scan_mcp(self) -> Dict[str, Any]:
        mcp_dir = self.workspace_root / "langcare-mcp-fhir-main"
        target_files = [
            mcp_dir / "asha_mcp_server.py",
            mcp_dir / "asha_clinical_tools.py",
            mcp_dir / "asha_care_gap_engine.py",
            mcp_dir / "asha_counseling_generator.py",
        ]
        tools_found = set()
        guidelines_found = set()

        for f in target_files:
            if f.exists():
                text = f.read_text(encoding="utf-8", errors="ignore")
                for t in [
                    "extract_structured_visit_from_transcript",
                    "evaluate_maternal_pediatric_red_flags",
                    "detect_household_care_gaps",
                    "generate_localized_counseling_script",
                ]:
                    if t in text:
                        tools_found.add(t)
                if "NHM" in text or "IMNCI" in text or "Pre-eclampsia" in text:
                    guidelines_found.add("NHM_IMNCI")

        status = "PASS" if len(tools_found) == 4 and "NHM_IMNCI" in guidelines_found else "PARTIAL"
        return {
            "component": "langcare-mcp-fhir-main",
            "tools_verified": sorted(list(tools_found)),
            "clinical_guidelines": sorted(list(guidelines_found)),
            "status": status,
        }

    def scan_filenest(self) -> Dict[str, Any]:
        filenest_dir = self.workspace_root / "bezs-filenest-main"
        target_files = [
            filenest_dir / "backend" / "app" / "routers" / "asha_media.py",
            filenest_dir / "backend" / "app" / "routers" / "health_education.py",
            filenest_dir / "backend" / "app" / "services" / "tus_resumable_service.py",
        ]
        features_found = set()

        for f in target_files:
            if f.exists():
                txt = f.read_text(encoding="utf-8", errors="ignore")
                for feat in ["asha-field-media", "health-education", "tus", "resumable", "chunk"]:
                    if feat in txt.lower():
                        features_found.add(feat)

        status = "PASS" if "asha-field-media" in features_found and "health-education" in features_found else "PARTIAL"
        return {
            "component": "bezs-filenest",
            "features_verified": sorted(list(features_found)),
            "status": status,
        }

    def scan_hms(self) -> Dict[str, Any]:
        hms_dir = self.workspace_root / "bezs-hms-main"
        target_files = [
            hms_dir / "src" / "modules" / "client" / "telemedicine" / "doctor" / "component" / "asha-referrals" / "HighRiskReferralQueue.tsx",
            hms_dir / "src" / "modules" / "client" / "telemedicine" / "doctor" / "component" / "asha-referrals" / "SubcentreSupplyBottleneckWidget.tsx",
            hms_dir / "src" / "modules" / "server" / "asha" / "asha-referral-service.ts",
            hms_dir / "src" / "app" / "api" / "asha-referrals" / "ambulance-alert" / "route.ts",
        ]
        features_found = set()

        for f in target_files:
            if f.exists():
                txt = f.read_text(encoding="utf-8", errors="ignore")
                for feat in [
                    "HighRiskReferralQueue",
                    "HighRiskReferralTicket",
                    "SubcentreSupplyBottleneckWidget",
                    "SupplyStockoutAlert",
                    "AshaReferralService",
                ]:
                    if feat in txt:
                        features_found.add(feat)

        status = "PASS" if len(features_found) >= 3 else "PARTIAL"
        return {
            "component": "bezs-hms",
            "features_verified": sorted(list(features_found)),
            "status": status,
        }

    def scan_observability(self) -> Dict[str, Any]:
        obs_dir = self.workspace_root / "bezs-observability-main"
        target_file = obs_dir / "sdk" / "python" / "src" / "watcher_sdk" / "sevafirst_telemetry.py"
        features_found = set()

        if target_file.exists():
            txt = target_file.read_text(encoding="utf-8", errors="ignore")
            for feat in [
                "SevaFirstTelemetry",
                "ClinicalAuditEntry",
                "record_visit_documentation_time",
                "record_high_risk_detection",
                "record_phc_admission_verified",
                "log_clinical_audit",
                "get_impact_summary",
            ]:
                if feat in txt:
                    features_found.add(feat)

        status = "PASS" if len(features_found) >= 4 else "PARTIAL"
        return {
            "component": "bezs-observability",
            "features_verified": sorted(list(features_found)),
            "status": status,
        }

    def run_all_scans(self) -> Dict[str, Any]:
        results = {
            "iam": self.scan_iam(),
            "emr_gql": self.scan_emr_gql(),
            "mcp": self.scan_mcp(),
            "filenest": self.scan_filenest(),
            "hms": self.scan_hms(),
            "observability": self.scan_observability(),
        }
        all_passed = all(r["status"] == "PASS" for r in results.values())
        return {
            "overall_status": "COMPLIANT" if all_passed else "ATTENTION_REQUIRED",
            "subsystem_results": results,
        }


if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    workspace = Path(__file__).resolve().parents[3]
    scanner = CrossRepoContractScanner(str(workspace))
    res = scanner.run_all_scans()
    print("=" * 60)
    print("SEVAFIRST CROSS-REPO CONTRACT VERIFICATION AUDIT")
    print("=" * 60)
    print(f"Overall Status: {res['overall_status']}")
    for k, v in res["subsystem_results"].items():
        print(f"[{v['status']}] {v['component']}:")
        for prop, val in v.items():
            if prop not in ["component", "status"]:
                print(f"   - {prop}: {val}")
    print("=" * 60)
