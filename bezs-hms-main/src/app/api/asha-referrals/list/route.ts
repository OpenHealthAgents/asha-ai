import { NextResponse } from "next/server";
import { AshaReferralService } from "@/modules/server/asha/asha-referral-service";

export async function GET() {
  const referrals = AshaReferralService.getHighRiskReferrals();
  const supplyStockouts = AshaReferralService.getSupplyStockouts();

  return NextResponse.json({
    status: "ok",
    referrals,
    supplyStockouts,
    counts: {
      totalHighRiskReferrals: referrals.length,
      pendingArrivalCount: referrals.filter((r) => r.status === "PENDING_ARRIVAL").length,
      ambulanceDispatchedCount: referrals.filter((r) => r.status === "108_AMBULANCE_DISPATCHED").length,
      criticalStockoutsCount: supplyStockouts.filter((s) => s.stockStatus === "CRITICAL_STOCKOUT").length,
    },
  });
}
