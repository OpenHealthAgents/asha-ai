import { NextRequest, NextResponse } from "next/server";
import { AshaReferralService } from "@/modules/server/asha/asha-referral-service";

export async function GET() {
  const supplies = AshaReferralService.getSupplyStockouts();
  return NextResponse.json({ supplies });
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const alert = AshaReferralService.createSupplyAlert(body);
    return NextResponse.json({
      status: "SUCCESS",
      alertId: alert.alertId,
      message: "Supply bottleneck alert registered at PHC pharmacy.",
    });
  } catch (error) {
    return NextResponse.json(
      { status: "ERROR", message: String(error) },
      { status: 500 }
    );
  }
}

export async function PATCH(req: NextRequest) {
  try {
    const body = await req.json();
    const updated = AshaReferralService.approveSupplyDispatch(body.alertId);
    if (!updated) {
      return NextResponse.json({ error: "Alert not found" }, { status: 404 });
    }
    return NextResponse.json({
      status: "SUCCESS",
      alert: updated,
      message: "Sub-Centre kit replenishment approved and dispatched.",
    });
  } catch (error) {
    return NextResponse.json(
      { status: "ERROR", message: String(error) },
      { status: 500 }
    );
  }
}
