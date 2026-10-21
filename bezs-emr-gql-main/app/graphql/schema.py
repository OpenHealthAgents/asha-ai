"""
Strawberry GraphQL Schema defining Query and Mutation roots for FHIR Middleware.
"""

from typing import List, Optional
import strawberry
from strawberry.types import Info

from app.auth.models import AuthUser
from app.config import settings
from app.fhir_client.client import FhirClient
from app.graphql.types import (
    CareGapSummary,
    OfflineVisitInput,
    SyncBatchPayload,
)
from app.services.care_gap_service import CareGapService
from app.services.offline_sync_service import OfflineSyncService


def _get_actor(info: Info) -> AuthUser:
    if info.context and isinstance(info.context, dict):
        request = info.context.get("request")
        if request and hasattr(request, "state") and hasattr(request.state, "user") and request.state.user:
            user_dict = request.state.user
            return AuthUser(
                sub=user_dict.get("sub", "usr-asha-sunita"),
                org_id=user_dict.get("org_id") or user_dict.get("activeOrganizationId"),
                role=user_dict.get("role", "ROLE_ASHA"),
                state_code=user_dict.get("state_code", "OR"),
                district_code=user_dict.get("district_code", "dist-bhadrak"),
                block_code=user_dict.get("block_code", "blk-bhadrak"),
                phc_id=user_dict.get("phc_id", "phc-bhadrak-01"),
                subcentre_id=user_dict.get("subcentre_id", "sc-rampur-01"),
                village_lgd_code=user_dict.get("village_lgd_code", "215432"),
                hpr_id=user_dict.get("hpr_id"),
            )
    return AuthUser(
        sub="usr-asha-sunita",
        org_id="org-nhm-india",
        role="ROLE_ASHA",
        state_code="OR",
        district_code="dist-bhadrak",
        block_code="blk-bhadrak",
        phc_id="phc-bhadrak-01",
        subcentre_id="sc-rampur-01",
        village_lgd_code="215432",
        hpr_id="HPR-ASHA-OR-215432",
    )


@strawberry.type
class Query:
    @strawberry.field
    def ping(self) -> str:
        return "pong (ASHA FHIR GraphQL Gateway)"

    @strawberry.field
    async def get_village_care_gaps(
        self,
        info: Info,
        village_lgd_code: str,
    ) -> CareGapSummary:
        """
        Returns real-time village care gaps including overdue infant immunizations,
        missed ANC trimesters / high-risk maternal alerts, and pending CBAC NCD screenings.
        """
        fhir_client = FhirClient(base_url=settings.FHIR_SERVER_URL)
        service = CareGapService(fhir_client=fhir_client)
        return await service.get_village_care_gaps(village_lgd_code=village_lgd_code)


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def sync_offline_field_visits(
        self,
        info: Info,
        visits: List[OfflineVisitInput],
    ) -> SyncBatchPayload:
        """
        Batch mutation for offline mobile clients to sync field visits with conflict resolution,
        idempotency keys (visit_uuid), and retrospective FHIR R4 encounter writes.
        """
        actor = _get_actor(info)
        fhir_client = FhirClient(base_url=settings.FHIR_SERVER_URL)
        service = OfflineSyncService(fhir_client=fhir_client)
        return await service.sync_offline_field_visits(visits=visits, actor=actor)


schema = strawberry.Schema(query=Query, mutation=Mutation)
