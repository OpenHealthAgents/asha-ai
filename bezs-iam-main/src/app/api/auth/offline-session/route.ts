import { NextRequest, NextResponse } from "next/server";
import { OfflineSessionService } from "@/modules/server/auth/offline-session.service";
import { verifyAccessToken } from "@/lib/verifyAccessToken";

/**
 * POST /api/auth/offline-session
 * Exchanges an active online session or refresh token for a 14-day cryptographic offline token.
 */
export async function POST(req: NextRequest) {
  try {
    const body = await req.json().catch(() => ({}));
    const { grant_type, refresh_token, client_id, device_id } = body;

    // Grant type: refresh_token (offline renewal)
    if (grant_type === "refresh_token" && refresh_token) {
      const refreshed = await OfflineSessionService.refreshOfflineSession(
        refresh_token,
        client_id || "com.drgodly.app"
      );
      return NextResponse.json(refreshed);
    }

    // Grant type: online session bearer exchange
    const authHeader = req.headers.get("authorization");
    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      return NextResponse.json(
        { error: "unauthorized", message: "Bearer token required to mint offline session" },
        { status: 401 }
      );
    }

    const token = authHeader.substring(7);
    const verification = await verifyAccessToken(token);

    if (!verification.valid || !verification.payload) {
      return NextResponse.json(
        { error: "invalid_token", message: verification.message ?? "Access token verification failed" },
        { status: 401 }
      );
    }

    const userId = verification.payload.sub as string;
    const session = await OfflineSessionService.issueOfflineSession(
      userId,
      client_id || "com.drgodly.app",
      device_id
    );

    return NextResponse.json(session);
  } catch (err: unknown) {
    const errorMsg = err instanceof Error ? err.message : "Internal error";
    return NextResponse.json({ error: "server_error", message: errorMsg }, { status: 500 });
  }
}

/**
 * GET /api/auth/offline-session
 * Verifies and introspects an offline token.
 */
export async function GET(req: NextRequest) {
  try {
    const authHeader = req.headers.get("authorization");
    if (!authHeader || !authHeader.startsWith("Bearer ")) {
      return NextResponse.json(
        { error: "unauthorized", message: "Bearer offline token required" },
        { status: 401 }
      );
    }

    const token = authHeader.substring(7);
    const result = await OfflineSessionService.verifyOfflineSession(token);

    if (!result.valid) {
      return NextResponse.json({ valid: false, error: result.error }, { status: 401 });
    }

    return NextResponse.json({ valid: true, payload: result.payload });
  } catch (err: unknown) {
    return NextResponse.json(
      { valid: false, error: err instanceof Error ? err.message : "Verification error" },
      { status: 500 }
    );
  }
}
