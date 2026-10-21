/**
 * @module permissions
 * @description Authoritative list of all permission strings in the system.
 *              Used by seed scripts, the `buildUserContext` nav filter,
 *              org role permission management, and `getUserPermissions`.
 *
 * **Format:** `resource:action` (e.g. `patient:read`, `encounter:create`).
 *
 * **Resources defined:**
 * - `patient` — CRUD on patient profiles
 * - `practitioner` — CRUD on healthcare practitioners
 * - `appointment` — CRUD on appointments
 * - `encounter` — CRUD on clinical encounters
 * - `questionnaire_response` — CRUD on questionnaire responses
 * - `consultagent` — chatbot access
 * - `agent` — AI agent chat access
 *
 * @category Domain
 */

export const permission = [
  "patient:create",
  "patient:read",
  "patient:update",
  "patient:delete",
  "practitioner:create",
  "practitioner:read",
  "practitioner:upadte",
  "practitioner:delete",
  "appointment:read",
  "appointment:create",
  "appointment:update",
  "appointment:delete",
  "encounter:create",
  "encounter:read",
  "encounter:update",
  "encounter:delete",
  "questionnaire_response:create",
  "questionnaire_response:read",
  "questionnaire_response:update",
  "questionnaire_response:delete",
  "observation:create",
  "observation:read",
  "observation:update",
  "observation:delete",
  "immunization:create",
  "immunization:read",
  "immunization:update",
  "immunization:delete",
  "household:create",
  "household:read",
  "household:update",
  "household:delete",
  "referral:create",
  "referral:read",
  "referral:update",
  "referral:approve",
  "referral:close",
  "medication_request:create",
  "medication_request:read",
  "medication_request:update",
  "medication_request:delete",
  "diagnostic_report:create",
  "diagnostic_report:read",
  "diagnostic_report:update",
  "diagnostic_report:delete",
  "care_gap:read",
  "consultagent:chat",
  "agent:chat",
] as const;

export type PermissionKey = (typeof permission)[number];

/**
 * Strict Frontline Healthcare Worker Roles in the Indian Public Health Delivery Hierarchy:
 * - ROLE_ASHA: Accredited Social Health Activist (Village level, ~1,000 population).
 * - ROLE_ANM: Auxiliary Nurse Midwife (Sub-Centre / Health & Wellness Centre level, ~5,000 population).
 * - ROLE_PHC_MO: Primary Health Centre Medical Officer (PHC level, ~30,000 population).
 */
export const FRONTLINE_ROLES = {
  ROLE_ASHA: "ROLE_ASHA",
  ROLE_ANM: "ROLE_ANM",
  ROLE_PHC_MO: "ROLE_PHC_MO",
} as const;

export type FrontlineRole = (typeof FRONTLINE_ROLES)[keyof typeof FRONTLINE_ROLES];

/**
 * Role-Based Permission Matrix for Frontline Health Workers
 */
export const FRONTLINE_ROLE_PERMISSIONS: Record<FrontlineRole, readonly PermissionKey[]> = {
  ROLE_ASHA: [
    "patient:create",
    "patient:read",
    "patient:update",
    "encounter:create",
    "encounter:read",
    "encounter:update",
    "questionnaire_response:create",
    "questionnaire_response:read",
    "questionnaire_response:update",
    "observation:create",
    "observation:read",
    "immunization:read",
    "household:create",
    "household:read",
    "household:update",
    "referral:create",
    "referral:read",
    "care_gap:read",
    "consultagent:chat",
    "agent:chat",
  ],
  ROLE_ANM: [
    "patient:create",
    "patient:read",
    "patient:update",
    "patient:delete",
    "appointment:read",
    "appointment:create",
    "appointment:update",
    "encounter:create",
    "encounter:read",
    "encounter:update",
    "questionnaire_response:create",
    "questionnaire_response:read",
    "questionnaire_response:update",
    "observation:create",
    "observation:read",
    "observation:update",
    "immunization:create",
    "immunization:read",
    "immunization:update",
    "household:create",
    "household:read",
    "household:update",
    "referral:create",
    "referral:read",
    "referral:update",
    "care_gap:read",
    "consultagent:chat",
    "agent:chat",
  ],
  ROLE_PHC_MO: [
    "patient:create",
    "patient:read",
    "patient:update",
    "patient:delete",
    "practitioner:read",
    "appointment:read",
    "appointment:create",
    "appointment:update",
    "appointment:delete",
    "encounter:create",
    "encounter:read",
    "encounter:update",
    "encounter:delete",
    "questionnaire_response:create",
    "questionnaire_response:read",
    "questionnaire_response:update",
    "questionnaire_response:delete",
    "observation:create",
    "observation:read",
    "observation:update",
    "observation:delete",
    "immunization:create",
    "immunization:read",
    "immunization:update",
    "immunization:delete",
    "household:create",
    "household:read",
    "household:update",
    "household:delete",
    "referral:create",
    "referral:read",
    "referral:update",
    "referral:approve",
    "referral:close",
    "medication_request:create",
    "medication_request:read",
    "medication_request:update",
    "medication_request:delete",
    "diagnostic_report:create",
    "diagnostic_report:read",
    "diagnostic_report:update",
    "diagnostic_report:delete",
    "care_gap:read",
    "consultagent:chat",
    "agent:chat",
  ],
};
