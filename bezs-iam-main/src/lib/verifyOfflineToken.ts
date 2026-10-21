import { jwtVerify, errors as JoseErrors } from "jose";

const OFFLINE_TOKEN_SECRET = process.env.OFFLINE_TOKEN_SECRET || "asha-offline-cryptographic-signing-key-32b-secret!!";
const SECRET_KEY_BYTES = new TextEncoder().encode(OFFLINE_TOKEN_SECRET);

export interface OfflineVerificationResult {
  valid: boolean;
  code?: string;
  status: number;
  message?: string;
  payload?: Record<string, unknown>;
  remainingHours?: number;
}

/**
 * Validates an ASHA / ANM 14-day cryptographic offline token without network connectivity.
 */
export async function verifyOfflineToken(token: string): Promise<OfflineVerificationResult> {
  try {
    const { payload } = await jwtVerify(token, SECRET_KEY_BYTES, {
      audience: "asha-mobile-offline",
    });

    const exp = payload.exp ?? 0;
    const now = Math.floor(Date.now() / 1000);
    const remainingSeconds = exp - now;
    const remainingHours = Math.max(0, Math.floor(remainingSeconds / 3600));

    return {
      valid: true,
      status: 200,
      payload,
      remainingHours,
    };
  } catch (error) {
    if (error instanceof JoseErrors.JWTExpired) {
      return {
        valid: false,
        code: "OFFLINE_TOKEN_EXPIRED",
        status: 401,
        message: "Offline session exceeded the 14-day cryptographic limit. Re-sync with network required.",
      };
    }

    if (error instanceof JoseErrors.JWSSignatureVerificationFailed) {
      return {
        valid: false,
        code: "OFFLINE_SIGNATURE_TAMPERED",
        status: 401,
        message: "Cryptographic signature mismatch. Token has been modified or forged.",
      };
    }

    if (error instanceof JoseErrors.JWTInvalid) {
      return {
        valid: false,
        code: "OFFLINE_TOKEN_MALFORMED",
        status: 400,
        message: "Malformed offline token.",
      };
    }

    return {
      valid: false,
      code: "OFFLINE_AUTH_FAILED",
      status: 401,
      message: error instanceof Error ? error.message : "Offline token verification failed",
    };
  }
}
