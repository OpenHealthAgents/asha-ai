import { SignJWT, jwtVerify, importJWK, exportJWK, generateKeyPair } from "jose";
import { createHash, randomUUID } from "crypto";
import { prisma } from "../../../../prisma/db";
import { FRONTLINE_ROLE_PERMISSIONS, FrontlineRole } from "../../../../../permissions";

const OFFLINE_TOKEN_SECRET = process.env.OFFLINE_TOKEN_SECRET || "asha-offline-cryptographic-signing-key-32b-secret!!";
const SECRET_KEY_BYTES = new TextEncoder().encode(OFFLINE_TOKEN_SECRET);
const OFFLINE_LIFETIME_DAYS = 14;
const OFFLINE_LIFETIME_SECONDS = OFFLINE_LIFETIME_DAYS * 24 * 60 * 60; // 1,209,600s

export interface FrontlineHierarchyMetadata {
  state_code: string | null;
  district_code: string | null;
  block_code: string | null;
  phc_id: string | null;
  subcentre_id: string | null;
  village_lgd_code: string | null;
  hpr_id: string | null;
}

export interface OfflineSessionPayload {
  sub: string;
  name: string;
  email: string;
  role: FrontlineRole | string;
  permissions: string[];
  hierarchy: FrontlineHierarchyMetadata;
  offline: {
    max_days: number;
    issued_at: string;
    expires_at: string;
    offline_session_id: string;
    client_id: string;
    device_id?: string;
  };
}

export interface OfflineSessionTokens {
  offlineAccessToken: string;
  offlineRefreshToken: string;
  tokenType: "Bearer";
  expiresIn: number;
  expiresAt: string;
  workerProfile: {
    id: string;
    name: string;
    email: string;
    role: string;
    hierarchy: FrontlineHierarchyMetadata;
    permissions: string[];
  };
}

export class OfflineSessionService {
  /**
   * Issues a cryptographically signed offline access token and refresh token
   * valid for up to 14 days without network connectivity.
   */
  static async issueOfflineSession(
    userId: string,
    clientId = "com.drgodly.app",
    deviceId?: string
  ): Promise<OfflineSessionTokens> {
    const user = await prisma.user.findUnique({
      where: { id: userId },
      select: {
        id: true,
        name: true,
        email: true,
        role: true,
        stateCode: true,
        districtCode: true,
        blockCode: true,
        phcId: true,
        subcentreId: true,
        villageLgdCode: true,
        hprId: true,
      },
    });

    if (!user) {
      throw new Error(`User not found: ${userId}`);
    }

    const role = (user.role ?? "ROLE_ASHA") as FrontlineRole;
    const permissions = [...(FRONTLINE_ROLE_PERMISSIONS[role] ?? [])];
    const hierarchy: FrontlineHierarchyMetadata = {
      state_code: user.stateCode,
      district_code: user.districtCode,
      block_code: user.blockCode,
      phc_id: user.phcId,
      subcentre_id: user.subcentreId,
      village_lgd_code: user.villageLgdCode,
      hpr_id: user.hprId,
    };

    const now = Math.floor(Date.now() / 1000);
    const expiresAtSeconds = now + OFFLINE_LIFETIME_SECONDS;
    const expiresAtIso = new Date(expiresAtSeconds * 1000).toISOString();
    const offlineSessionId = randomUUID();

    const payload: OfflineSessionPayload = {
      sub: user.id,
      name: user.name,
      email: user.email,
      role,
      permissions,
      hierarchy,
      offline: {
        max_days: OFFLINE_LIFETIME_DAYS,
        issued_at: new Date(now * 1000).toISOString(),
        expires_at: expiresAtIso,
        offline_session_id: offlineSessionId,
        client_id: clientId,
        device_id: deviceId,
      },
    };

    // Sign offline access token (14 days)
    const offlineAccessToken = await new SignJWT(payload as unknown as Record<string, unknown>)
      .setProtectedHeader({ alg: "HS256", typ: "JWT" })
      .setIssuer(process.env.BETTER_AUTH_URL || "https://iam.drgodly.com")
      .setAudience("asha-mobile-offline")
      .setSubject(user.id)
      .setIssuedAt(now)
      .setExpirationTime(expiresAtSeconds)
      .setJti(offlineSessionId)
      .sign(SECRET_KEY_BYTES);

    // Generate cryptographic refresh token (30 days for cycle refresh)
    const refreshId = randomUUID();
    const offlineRefreshToken = await new SignJWT({
      sub: user.id,
      sid: offlineSessionId,
      typ: "offline_refresh",
    })
      .setProtectedHeader({ alg: "HS256", typ: "JWT" })
      .setIssuer(process.env.BETTER_AUTH_URL || "https://iam.drgodly.com")
      .setAudience("asha-mobile-offline-refresh")
      .setIssuedAt(now)
      .setExpirationTime(now + 30 * 24 * 60 * 60)
      .setJti(refreshId)
      .sign(SECRET_KEY_BYTES);

    // Record session verification in database for audit and revocation
    await prisma.verification.create({
      data: {
        id: randomUUID(),
        identifier: `offline:${offlineSessionId}`,
        value: createHash("sha256").update(offlineAccessToken).digest("hex"),
        expiresAt: new Date(expiresAtSeconds * 1000),
        createdAt: new Date(),
        updatedAt: new Date(),
      },
    });

    return {
      offlineAccessToken,
      offlineRefreshToken,
      tokenType: "Bearer",
      expiresIn: OFFLINE_LIFETIME_SECONDS,
      expiresAt: expiresAtIso,
      workerProfile: {
        id: user.id,
        name: user.name,
        email: user.email,
        role,
        hierarchy,
        permissions,
      },
    };
  }

  /**
   * Cryptographically validates an offline session token.
   * Can be executed by the client device or server without active external calls.
   */
  static async verifyOfflineSession(token: string): Promise<{
    valid: boolean;
    payload?: OfflineSessionPayload;
    error?: string;
  }> {
    try {
      const { payload } = await jwtVerify(token, SECRET_KEY_BYTES, {
        issuer: process.env.BETTER_AUTH_URL || "https://iam.drgodly.com",
        audience: "asha-mobile-offline",
      });

      return {
        valid: true,
        payload: payload as unknown as OfflineSessionPayload,
      };
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Verification failed";
      return {
        valid: false,
        error: msg,
      };
    }
  }

  /**
   * Refreshes an offline session when mobile app detects connection.
   */
  static async refreshOfflineSession(
    refreshToken: string,
    clientId = "com.drgodly.app"
  ): Promise<OfflineSessionTokens> {
    try {
      const { payload } = await jwtVerify(refreshToken, SECRET_KEY_BYTES, {
        issuer: process.env.BETTER_AUTH_URL || "https://iam.drgodly.com",
        audience: "asha-mobile-offline-refresh",
      });

      const userId = payload.sub;
      if (!userId) {
        throw new Error("Invalid refresh token payload");
      }

      return await this.issueOfflineSession(userId, clientId);
    } catch (err: unknown) {
      throw new Error(`Offline session refresh failed: ${err instanceof Error ? err.message : String(err)}`);
    }
  }
}
