/**
 * Frontline ASHA Referrals & Triage Command Center Page.
 *
 * Route: /[locale]/(apps)/bezs/telemedicine/doctor/asha-referrals
 *
 * Displays live high-risk village triage handoffs from DrGodly mobile clients,
 * audio recordings from bezs-filenest, and Sub-Centre supply stockout requests.
 */

import React from "react";
import { AshaReferralService } from "@/modules/server/asha/asha-referral-service";
import { AshaReferralsDashboard } from "@/modules/client/telemedicine/doctor/component/asha-referrals/AshaReferralsDashboard";

export default async function AshaReferralsPage() {
  const referrals = AshaReferralService.getHighRiskReferrals();
  const supplies = AshaReferralService.getSupplyStockouts();

  return (
    <div className="w-full">
      <AshaReferralsDashboard
        initialReferrals={referrals}
        initialSupplies={supplies}
      />
    </div>
  );
}
