import { NextRequest, NextResponse } from "next/server";
import { AshaReferralService } from "@/modules/server/asha/asha-referral-service";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const referrals = AshaReferralService.getHighRiskReferrals();
    const match = referrals.find((r) => r.patientId === body.patientId);

    const arrivalStatus = match && match.status === "ARRIVED_AT_PHC"
      ? "ARRIVED_CONFIRMED"
      : "PENDING_FIELD_VISIT";

    return NextResponse.json({
      status: "VERIFIED",
      patientId: body.patientId,
      phcId: body.phcId,
      workerId: body.workerId,
      arrivalStatus,
      followupAction: arrivalStatus === "ARRIVED_CONFIRMED"
        ? "Patient received care at PHC. No further urgent action needed."
        : "Patient has NOT reached PHC. Frontline ASHA worker must conduct urgent home visit.",
    });
  } catch (error) {
    return NextResponse.json(
      { status: "ERROR", message: String(error) },
      { status: 500 }
    );
  }
}
