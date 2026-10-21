import { NextRequest, NextResponse } from "next/server";
import { AshaReferralService } from "@/modules/server/asha/asha-referral-service";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const ticket = AshaReferralService.createReferral({
      patientId: body.patientId,
      patientName: body.patientName,
      patientPhone: body.patientPhone,
      villageLgdCode: body.villageLgdCode,
      phcId: body.phcId,
      subcentreId: body.subcentreId,
      workerId: body.workerId,
      riskLevel: body.riskLevel || "HIGH",
      dangerFlags: body.dangerFlags || [],
      vitals: body.vitals || {},
      voiceAudioUrl: body.voiceAudioUrl,
      clinicalNotes: body.clinicalNotes || "High-risk triage escalated to PHC MO.",
      escalatedAt: body.escalatedAt || new Date().toISOString(),
    });

    return NextResponse.json({
      status: "SUCCESS",
      ticketId: ticket.ticketId,
      assignedPhc: ticket.phcId,
      message: "Urgent high-risk intake ticket created in PHC Command Center.",
    });
  } catch (error) {
    return NextResponse.json(
      { status: "ERROR", message: String(error) },
      { status: 500 }
    );
  }
}
