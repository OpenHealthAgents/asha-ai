"""
Lightweight data model representing the authenticated user for the current request.

AuthUser is constructed from the decoded JWT payload and passed into service and
client layers so they can attach actor identity to every write operation sent to
the FHIR server (audit trail: who created/updated/deleted a resource).
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class AuthUser:
    """
    Immutable snapshot of the authenticated caller's identity for a single request.

    Fields are populated directly from JWT claims after successful token validation
    (see app.auth.dependencies.get_current_user).
    """

    # JWT subject — the unique, stable identifier for this user across all services.
    sub: str

    # Active organization context — used to scope all FHIR resource reads and writes
    # to the tenant the user is currently operating under. None for org-less tokens.
    org_id: Optional[str]

    # Frontline RBAC & LGD hierarchy claims
    role: Optional[str] = None
    state_code: Optional[str] = None
    district_code: Optional[str] = None
    block_code: Optional[str] = None
    phc_id: Optional[str] = None
    subcentre_id: Optional[str] = None
    village_lgd_code: Optional[str] = None
    hpr_id: Optional[str] = None
