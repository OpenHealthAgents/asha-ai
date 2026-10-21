/**
 * Seed script: Frontline Health RBAC (ROLE_ASHA, ROLE_ANM, ROLE_PHC_MO)
 * Creates frontline health workers with LGD hierarchy metadata and permissions.
 */

import { PrismaClient } from "../prisma/generated/prisma";
import { PrismaPg } from "@prisma/adapter-pg";
import { Pool } from "pg";
import { randomUUID } from "crypto";
import { FRONTLINE_ROLE_PERMISSIONS, FRONTLINE_ROLES } from "../permissions";

const pool = new Pool({ connectionString: process.env.DATABASE_URL ?? "" });
const adapter = new PrismaPg(pool);
const prisma = new PrismaClient({ adapter });

async function seedFrontlineRbac() {
  console.log("============================================================");
  console.log("   Seeding Frontline Health RBAC & LGD Hierarchy Metadata   ");
  console.log("============================================================");

  // 1. Ensure National Health Mission organization exists
  const nhmOrg = await prisma.organization.upsert({
    where: { slug: "nhm-india" },
    create: {
      id: "org-nhm-india",
      name: "National Health Mission - Odisha",
      slug: "nhm-india",
      createdAt: new Date(),
      metadata: JSON.stringify({
        state: "Odisha",
        state_code: "OR",
        tier: "Rural Frontline Health Mission",
      }),
    },
    update: {},
  });
  console.log(`✓ Organization ready: ${nhmOrg.name} (${nhmOrg.id})`);

  // 2. Create Frontline Organization Roles with permissions
  const rolesToSeed = [
    {
      role: FRONTLINE_ROLES.ROLE_ASHA,
      description: "Accredited Social Health Activist (Village Level)",
      permissions: FRONTLINE_ROLE_PERMISSIONS.ROLE_ASHA,
    },
    {
      role: FRONTLINE_ROLES.ROLE_ANM,
      description: "Auxiliary Nurse Midwife (Sub-centre Level)",
      permissions: FRONTLINE_ROLE_PERMISSIONS.ROLE_ANM,
    },
    {
      role: FRONTLINE_ROLES.ROLE_PHC_MO,
      description: "Primary Health Centre Medical Officer (PHC Level)",
      permissions: FRONTLINE_ROLE_PERMISSIONS.ROLE_PHC_MO,
    },
  ];

  const orgRoleMap: Record<string, string> = {};

  for (const r of rolesToSeed) {
    const permMap: Record<string, string[]> = {};
    for (const p of r.permissions) {
      const [res, act] = p.split(":");
      if (!permMap[res]) permMap[res] = [];
      permMap[res].push(act);
    }

    const existingRole = await prisma.organizationRole.findFirst({
      where: { organizationId: nhmOrg.id, role: r.role },
    });

    const roleRecord = existingRole
      ? await prisma.organizationRole.update({
          where: { id: existingRole.id },
          data: { permission: JSON.stringify(permMap) },
        })
      : await prisma.organizationRole.create({
          data: {
            id: randomUUID(),
            organizationId: nhmOrg.id,
            role: r.role,
            permission: JSON.stringify(permMap),
          },
        });

    orgRoleMap[r.role] = roleRecord.id;
    console.log(`✓ Role seeded: ${r.role} with ${r.permissions.length} permissions`);
  }

  // 3. Seed Frontline Workers
  const frontlineUsers = [
    {
      id: "usr-asha-sunita",
      name: "Sunita Devi",
      email: "asha.sunita.rampur@nhm.gov.in",
      username: "asha_sunita",
      role: FRONTLINE_ROLES.ROLE_ASHA,
      stateCode: "OR",
      districtCode: "dist-bhadrak",
      blockCode: "blk-bhadrak",
      phcId: "phc-bhadrak-01",
      subcentreId: "sc-rampur-01",
      villageLgdCode: "215432", // Rampur village LGD code
      hprId: "HPR-ASHA-OR-215432",
    },
    {
      id: "usr-anm-priya",
      name: "Priya Sharma",
      email: "anm.priya.rampur@nhm.gov.in",
      username: "anm_priya",
      role: FRONTLINE_ROLES.ROLE_ANM,
      stateCode: "OR",
      districtCode: "dist-bhadrak",
      blockCode: "blk-bhadrak",
      phcId: "phc-bhadrak-01",
      subcentreId: "sc-rampur-01",
      villageLgdCode: "215432",
      hprId: "HPR-ANM-OR-88219",
    },
    {
      id: "usr-mo-rajesh",
      name: "Dr. Rajesh Kumar",
      email: "mo.rajesh.bhadrak@nhm.gov.in",
      username: "dr_rajesh_mo",
      role: FRONTLINE_ROLES.ROLE_PHC_MO,
      stateCode: "OR",
      districtCode: "dist-bhadrak",
      blockCode: "blk-bhadrak",
      phcId: "phc-bhadrak-01",
      subcentreId: null,
      villageLgdCode: null,
      hprId: "HPR-MO-OR-991204",
    },
  ];

  for (const u of frontlineUsers) {
    const userRecord = await prisma.user.upsert({
      where: { email: u.email },
      create: {
        id: u.id,
        name: u.name,
        email: u.email,
        username: u.username,
        role: u.role,
        stateCode: u.stateCode,
        districtCode: u.districtCode,
        blockCode: u.blockCode,
        phcId: u.phcId,
        subcentreId: u.subcentreId,
        villageLgdCode: u.villageLgdCode,
        hprId: u.hprId,
        emailVerified: true,
      },
      update: {
        role: u.role,
        stateCode: u.stateCode,
        districtCode: u.districtCode,
        blockCode: u.blockCode,
        phcId: u.phcId,
        subcentreId: u.subcentreId,
        villageLgdCode: u.villageLgdCode,
        hprId: u.hprId,
      },
    });

    // Ensure org membership
    const member = await prisma.member.findFirst({
      where: { organizationId: nhmOrg.id, userId: userRecord.id },
    });

    if (!member) {
      await prisma.member.create({
        data: {
          id: randomUUID(),
          organizationId: nhmOrg.id,
          userId: userRecord.id,
          role: u.role,
          createdAt: new Date(),
        },
      });
    }

    // Set User Context
    await prisma.userContext.upsert({
      where: { userId: userRecord.id },
      create: {
        userId: userRecord.id,
        activeOrganizationId: nhmOrg.id,
        activeRoleId: orgRoleMap[u.role],
      },
      update: {
        activeOrganizationId: nhmOrg.id,
        activeRoleId: orgRoleMap[u.role],
      },
    });

    console.log(`✓ Frontline User ready: ${u.name} (${u.role}) - Village: ${u.villageLgdCode ?? "PHC Level"}`);
  }

  console.log("\n✓ All Frontline RBAC roles and users successfully configured.");
}

seedFrontlineRbac()
  .catch((e) => {
    console.error("Seeding error:", e);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());
