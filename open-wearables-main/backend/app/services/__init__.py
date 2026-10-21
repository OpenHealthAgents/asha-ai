from app.utils.auth import DeveloperDep, SDKAuthDep

from .api_key_service import ApiKeyDep, StreamingApiKeyDep, api_key_service
from .application_service import application_service
from .archival_service import archival_service
from .developer_service import developer_service

try:
    from .event_record_service import event_record_service
except ModuleNotFoundError:
    event_record_service = None

try:
    from .invitation_service import invitation_service
except ModuleNotFoundError:
    invitation_service = None
try:
    from .priority_service import PriorityService
except ModuleNotFoundError:
    PriorityService = None

try:
    from .providers.apple.apple_xml.presigned_url_service import presigned_url_service
except ModuleNotFoundError:
    presigned_url_service = None

from .refresh_token_service import refresh_token_service

try:
    from .sdk.import_service import import_service as sdk_import_service
except ModuleNotFoundError:
    sdk_import_service = None

from .sdk_token_service import create_sdk_user_token
from .services import AppService

try:
    from .summaries_service import summaries_service
except ModuleNotFoundError:
    summaries_service = None

try:
    from .system_info_service import system_info_service
except ModuleNotFoundError:
    system_info_service = None

try:
    from .timeseries_service import timeseries_service
except ModuleNotFoundError:
    timeseries_service = None

try:
    from .user_connection_service import user_connection_service
except ModuleNotFoundError:
    user_connection_service = None

try:
    from .user_invitation_code_service import user_invitation_code_service
except ModuleNotFoundError:
    user_invitation_code_service = None

from .point_of_care_adapter import PointOfCareAdapter
from .fhir_observation_transformer import FhirObservationTransformer

try:
    from .user_service import user_service
except ModuleNotFoundError:
    user_service = None

__all__ = [
    "AppService",
    "api_key_service",
    "application_service",
    "archival_service",
    "create_sdk_user_token",
    "developer_service",
    "invitation_service",
    "refresh_token_service",
    "user_invitation_code_service",
    "DeveloperDep",
    "ApiKeyDep",
    "StreamingApiKeyDep",
    "SDKAuthDep",
    "user_connection_service",
    "user_service",
    "sdk_import_service",
    "event_record_service",
    "summaries_service",
    "timeseries_service",
    "system_info_service",
    "PriorityService",
    "presigned_url_service",
]
