from abc import ABCMeta, abstractmethod
from typing import Optional, List, Literal

import requests

from .models import Channel, MetricData, Page


class ResourceMixin(metaclass=ABCMeta):
    @abstractmethod
    def _auth_headers(self):
        """Builds the Authorization header using a valid access token."""
        pass

    @abstractmethod
    def _get_base_url(self):
        """Returns the base URL for the API."""

    def list_channels(
            self,
            start_ts: str,
            stop_ts: Optional[str] = None,
            page: Optional[int] = None,
            size: Optional[int] = None,
    ) -> Page[Channel]:
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
            f"{self._get_base_url()}/sources/channels",
            headers=self._auth_headers(),
            params=params,
        )
        response.raise_for_status()
        raw = response.json()
        return Page(
            page=raw["page"],
            size=raw["size"],
            total=raw["total"],
            data=[
                Channel(
                    channel_id=entry["channelId"],
                    start_ts=entry["startTs"],
                    stop_ts=entry.get("stopTs"),
                )
                for entry in raw["data"]
            ],
        )

    def list_metrics(self) -> List[str]:
        """
        Lists all available metric types for the authenticated client.

        :return: A list of metric name strings, eg. ['water-status-ssp', 'gi']
        """
        response = requests.get(
            f"{self._get_base_url()}/metrics",
            headers=self._auth_headers(),
        )
        response.raise_for_status()
        return [entry["metric"] for entry in response.json()]

    def _fetch_metric_raw(self, url: str, params) -> requests.Response:
        """Executes a metric GET request and returns the raw response."""
        response = requests.get(url, headers=self._auth_headers(), params=params)
        response.raise_for_status()
        return response

    @staticmethod
    def _build_metric_params(
            start_ts: str,
            resolution: str,
            source_id: str,
            stop_ts: Optional[str],
    ) -> dict:
        params = {"startTs": start_ts, "resolution": resolution, "sourceId": source_id}
        if stop_ts:
            params["stopTs"] = stop_ts
        return params

    @staticmethod
    def _build_aggregate_params(
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
        url = f"{self._get_base_url()}/metrics/{metric}"
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
        url = f"{self._get_base_url()}/metrics/{metric}/.csv"
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
        url = f"{self._get_base_url()}/metrics/{metric}/aggregate"
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
        url = f"{self._get_base_url()}/metrics/{metric}/aggregate/.csv"
        params = self._build_aggregate_params(start_ts, resolution, function, source_ids, stop_ts, partials_strategy)
        return self._fetch_metric_raw(url, params).text
