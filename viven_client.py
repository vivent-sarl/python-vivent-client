from typing import Optional, List, Literal

import requests

from models import MetricData, TokenResponse, Channel


class ViventClient:
    AUTH_URL = "https://auth.vivent-biosignals.com/realms/master/protocol/openid-connect/token"
    BASE_URL = "https://pubapi.vivent-biosignals.com/pub/v1"

    # Required headers for all resource endpoints
    RESOURCE_HEADERS = {
        "Content-Encoding": "gzip",
        "Accept": "*/*",
    }

    def __init__(self, auth_code: str, username: str, password: str):
        """
        :param auth_code: The Basic AUTH_CODE provided by Vivent.
        :param username:  The USERNAME provided by Vivent.
        :param password:  The PASSWORD provided by Vivent.
        """
        self.auth_code = auth_code
        self.username = username
        self.password = password
        self._token: Optional[TokenResponse] = None

    def authenticate(self) -> TokenResponse:
        """Obtains a fresh access token using username/password credentials."""
        print("[Auth] Requesting new access token...")
        response = requests.post(
            self.AUTH_URL,
            headers={"Authorization": f"Basic {self.auth_code}"},
            files={
                "grant_type": (None, "password"),
                "username":   (None, self.username),
                "password":   (None, self.password),
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
        print("[Auth] Access token obtained successfully.")
        return self._token

    def refresh_token(self) -> TokenResponse:
        """Refreshes the access token using the stored refresh token."""
        if self._token is None:
            raise RuntimeError("No token available to refresh. Call authenticate() first.")

        print("[Auth] Refreshing access token...")
        response = requests.post(
            self.AUTH_URL,
            headers={"Authorization": f"Basic {self.auth_code}"},
            files={
                "grant_type":    (None, "refresh_token"),
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
        print("[Auth] Token refreshed successfully.")
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

    def _auth_headers(self) -> dict:
        """Builds the Authorization header using a valid access token."""
        return {
            **self.RESOURCE_HEADERS,
            "Authorization": f"Bearer {self.get_valid_token()}",
        }


    def list_channels(
            self,
            start_ts: str,
            stop_ts: Optional[str] = None,
            page: Optional[int] = None,
            size: Optional[int] = None,
    ) -> List[Channel]:
        """
        Lists available channels (sources) for a given time range.

        :param start_ts: Start timestamp, eg. '2024-01-31T14:00:00Z'
        :param stop_ts:  (Optional) Stop timestamp, eg. '2024-01-31T15:00:00Z'
        :param page:     (Optional) Zero-based page number.
        :param size:     (Optional) Page size (default: 10).
        :return:         List of Channel objects.
        """
        params = {"startTs": start_ts}
        if stop_ts:
            params["stopTs"] = stop_ts
        if page is not None:
            params["page"] = page
        if size is not None:
            params["size"] = size

        response = requests.get(
            f"{self.BASE_URL}/sources/channels",
            headers=self._auth_headers(),
            params=params,
        )
        response.raise_for_status()
        return [
            Channel(
                channel_id=entry["channelId"],
                start_ts=entry["startTs"],
                stop_ts=entry.get("stopTs"),
            )
            for entry in response.json()["data"]
        ]

    def list_metrics(self) -> List[str]:
        """
        Lists all available metric types for the authenticated client.

        :return: A list of metric name strings, eg. ['water-status-ssp', 'gi']
        """
        response = requests.get(
            f"{self.BASE_URL}/metrics",
            headers=self._auth_headers(),
        )
        response.raise_for_status()
        return [entry["metric"] for entry in response.json()]

    def _fetch_metric_raw(self, url: str, params) -> requests.Response:
        """Executes a metric GET request and returns the raw response."""
        response = requests.get(url, headers=self._auth_headers(), params=params)
        response.raise_for_status()
        return response

    def _build_metric_params(
            self,
            start_ts: str,
            resolution: str,
            source_id: str,
            stop_ts: Optional[str],
    ) -> dict:
        params = {"startTs": start_ts, "resolution": resolution, "sourceId": source_id}
        if stop_ts:
            params["stopTs"] = stop_ts
        return params

    def _build_aggregate_params(
            self,
            start_ts: str,
            resolution: str,
            function: str,
            source_ids: List[str],
            stop_ts: Optional[str],
            partials_strategy: Optional[str],
    ) -> list:
        params = [
            ("startTs", start_ts),
            ("resolution", resolution),
            ("function", function),
        ]
        if stop_ts:
            params.append(("stopTs", stop_ts))
        if partials_strategy:
            params.append(("partialsStrategy", partials_strategy))
        for sid in source_ids:
            params.append(("sourceIds", sid))
        return params

    def get_metric(
            self,
            metric: str,
            source_id: str,
            start_ts: str,
            resolution: str,
            stop_ts: Optional[str] = None,
    ) -> MetricData:
        """
        Retrieves time-series data for a single channel.

        :param metric:     The metric name, eg. 'water-status-ssp'
        :param source_id:  The channel ID, eg. '02b82b-1'
        :param start_ts:   Start timestamp, eg. '2024-01-31T14:00:00Z'
        :param resolution: Desired resolution, eg. 'MINUTES_5'
        :param stop_ts:    (Optional) Stop timestamp.
        :return:           MetricData object.
        """
        url = f"{self.BASE_URL}/metrics/{metric}"
        params = self._build_metric_params(start_ts, resolution, source_id, stop_ts)
        data = self._fetch_metric_raw(url, params).json()
        return MetricData(timestamps=data["timestamp"], values=data["value"])

    def get_metric_csv(
            self,
            metric: str,
            source_id: str,
            start_ts: str,
            resolution: str,
            stop_ts: Optional[str] = None,
    ) -> str:
        """
        Retrieves time-series data for a single channel as a raw CSV string.

        :param metric:     The metric name, eg. 'water-status-ssp'
        :param source_id:  The channel ID, eg. '02b82b-1'
        :param start_ts:   Start timestamp, eg. '2024-01-31T14:00:00Z'
        :param resolution: Desired resolution, eg. 'MINUTES_5'
        :param stop_ts:    (Optional) Stop timestamp.
        :return:           Raw CSV string.
        """
        url = f"{self.BASE_URL}/metrics/{metric}/.csv"
        params = self._build_metric_params(start_ts, resolution, source_id, stop_ts)
        return self._fetch_metric_raw(url, params).text

    def get_aggregate_metric(
            self,
            metric: str,
            source_ids: List[str],
            start_ts: str,
            resolution: str,
            function: str,
            stop_ts: Optional[str] = None,
            partials_strategy: Optional[Literal["SKIP", "SHOW", "SET_NAN"]] = None,
    ) -> MetricData:
        """
        Retrieves aggregated time-series data across multiple channels.

        :param metric:            The metric name, eg. 'water-status-ssp'
        :param source_ids:        List of channel IDs, eg. ['02b82b-1', '02b82b-2']
        :param start_ts:          Start timestamp, eg. '2024-01-31T14:00:00Z'
        :param resolution:        Desired resolution, eg. 'MINUTES_5'
        :param function:          Aggregation function, eg. 'MEAN'
        :param stop_ts:           (Optional) Stop timestamp.
        :param partials_strategy: (Optional) 'SKIP' | 'SHOW' | 'SET_NAN'
        :return:                  MetricData object.
        """
        url = f"{self.BASE_URL}/metrics/{metric}/aggregate"
        params = self._build_aggregate_params(start_ts, resolution, function, source_ids, stop_ts, partials_strategy)
        data = self._fetch_metric_raw(url, params).json()
        return MetricData(timestamps=data["timestamp"], values=data["value"])

    def get_aggregate_metric_csv(
            self,
            metric: str,
            source_ids: List[str],
            start_ts: str,
            resolution: str,
            function: str,
            stop_ts: Optional[str] = None,
            partials_strategy: Optional[Literal["SKIP", "SHOW", "SET_NAN"]] = None,
    ) -> str:
        """
        Retrieves aggregated time-series data across multiple channels as a raw CSV string.

        :param metric:            The metric name, eg. 'water-status-ssp'
        :param source_ids:        List of channel IDs, eg. ['02b82b-1', '02b82b-2']
        :param start_ts:          Start timestamp, eg. '2024-01-31T14:00:00Z'
        :param resolution:        Desired resolution, eg. 'MINUTES_5'
        :param function:          Aggregation function, eg. 'MEAN'
        :param stop_ts:           (Optional) Stop timestamp.
        :param partials_strategy: (Optional) 'SKIP' | 'SHOW' | 'SET_NAN'
        :return:                  Raw CSV string.
        """
        url = f"{self.BASE_URL}/metrics/{metric}/aggregate/.csv"
        params = self._build_aggregate_params(start_ts, resolution, function, source_ids, stop_ts, partials_strategy)
        return self._fetch_metric_raw(url, params).text
