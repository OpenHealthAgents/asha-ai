import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    return NextResponse.json({
      status: "DISPATCHED",
      ambulanceService: "108_EMERGENCY_AMBULANCE",
      dispatchId: `AMB-108-${Date.now().toString().slice(-6)}`,
      destination: body.destinationFacility || "PHC Central",
      etaMinutes: 18,
      patientName: body.patientName,
      message: "108 emergency ambulance alerted and route mapped to village.",
    });
  } catch (error) {
    return NextResponse.json(
      { status: "ERROR", message: String(error) },
      { status: 500 }
    );
  }
}
