"""
Vivent Biosignals API client.

Provides :class:`ViventClient`, a high-level wrapper around the Vivent
public REST API, handling authentication, token refresh, and all
resource endpoints.
"""
import logging

from .auth_mixin import AuthMixin
from .metadata_mixin import MetadataMixin
from .resource_mixin import ResourceMixin

logger = logging.getLogger(__name__)


class ViventClient(AuthMixin, ResourceMixin, MetadataMixin):

    def __init__(self, auth_code: str, username: str, password: str):
        """
        :param auth_code: The Basic AUTH_CODE provided by Vivent.
        :param username:  The USERNAME provided by Vivent.
        :param password:  The PASSWORD provided by Vivent.
        """
        super().__init__(auth_code, username, password)

    BASE_URL = "https://pubapi.vivent-biosignals.com/pub/v1"

    def _auth_headers(self) -> dict:
        """Builds the Authorization header using a valid access token."""
        return {
            **self.RESOURCE_HEADERS,
            "Authorization": f"Bearer {self.get_valid_token()}",
        }

    def _get_base_url(self) -> str:
        return self.BASE_URL
