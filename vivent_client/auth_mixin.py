import logging
from typing import Optional

import requests

from vivent_client import TokenResponse

logger = logging.getLogger(__name__)

class AuthMixin:
    RESOURCE_HEADERS = {
        "Content-Encoding": "gzip",
        "Accept": "*/*",
    }
    AUTH_URL = "https://auth.vivent-biosignals.com/realms/master/protocol/openid-connect/token"

    def __init__(self, auth_code: str, username: str, password: str):
        self.auth_code = auth_code
        self.username = username
        self.password = password
        self._token: Optional[TokenResponse] = None

    def authenticate(self) -> TokenResponse:
        """Obtains a fresh access token using username/password credentials."""
        logger.debug("Requesting new access token.")
        response = requests.post(
            self.AUTH_URL,
            headers={"Authorization": f"Basic {self.auth_code}"},
            files={
                "grant_type": (None, "password"),
                "username": (None, self.username),
                "password": (None, self.password),
            },
        )
        response.raise_for_status()
        data = response.json()
        self._token = TokenResponse(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            expires_in=data["expires_in"],
            refresh_expires_in=data["refresh_expires_in"],
            token_type=data["token_type"],
        )
        logger.debug("Access token obtained successfully.")
        return self._token

    def refresh_token(self) -> TokenResponse:
        """Refreshes the access token using the stored refresh token."""
        if self._token is None:
            raise RuntimeError("No token available to refresh. Call authenticate() first.")

        logger.debug("Refreshing access token.")
        response = requests.post(
            self.AUTH_URL,
            headers={"Authorization": f"Basic {self.auth_code}"},
            files={
                "grant_type": (None, "refresh_token"),
                "refresh_token": (None, self._token.refresh_token),
            },
        )
        response.raise_for_status()
        data = response.json()
        self._token = TokenResponse(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            expires_in=data["expires_in"],
            refresh_expires_in=data["refresh_expires_in"],
            token_type=data["token_type"],
        )
        logger.debug("Access token refreshed successfully.")
        return self._token

    def get_valid_token(self) -> str:
        """
        Returns a valid access token, automatically refreshing or
        re-authenticating as needed.
        """
        if self._token is None:
            self.authenticate()
        elif self._token.is_refresh_expired():
            # Both tokens are expired — full re-authentication needed
            self.authenticate()
        elif self._token.is_expired():
            # Access token expired, but refresh token still valid
            self.refresh_token()

        return self._token.access_token

