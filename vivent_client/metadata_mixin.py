from abc import ABCMeta, abstractmethod
from typing import Optional

import requests

from .models import Connection, Device, Group, NamedEntity, Page, Trial


class MetadataMixin(metaclass=ABCMeta):

    @abstractmethod
    def _get_base_url(self) -> str:
        """Returns the base URL for metadata API requests."""
        pass

    @abstractmethod
    def _auth_headers(self):
        pass

    @staticmethod
    def _build_params(required: dict = None, optional: dict = None) -> dict:
        """
        Builds a query parameter dict from required and optional values.

        :param required: Params that are always included as-is.
        :param optional: Params included only when their value is not None.
        :return:         Merged params dict.
        """
        params = dict(required or {})
        for key, value in (optional or {}).items():
            if value is not None:
                params[key] = value
        return params

    def _get(self, path: str, params: dict = None) -> dict:
        """
        Performs an authenticated GET request and returns the parsed JSON body.

        :param path:   Path segment appended to the base URL, eg. '/metadata/trials'.
        :param params: Query parameters to include in the request.
        :return:       Parsed JSON response as a dict.
        """
        response = requests.get(
            f"{self._get_base_url()}{path}",
            headers=self._auth_headers(),
            params=params,
        )
        response.raise_for_status()
        return response.json()

    def list_trials(
            self,
            query: Optional[str] = None,
            start_ts: Optional[str] = None,
            stop_ts: Optional[str] = None,
            page: Optional[int] = None,
            size: Optional[int] = None,
    ) -> Page[Trial]:
        """
        Returns the list of trials accessible to the authenticated client.

        A trial is included if its active period overlaps with the requested
        time window; not necessarily fully contained within it.

        :param query:    (Optional) Text search filter, eg. 'my trial'.
        :param start_ts: (Optional) Inclusive start of the time window, eg. '2024-01-15T08:00:00.000Z'.
        :param stop_ts:  (Optional) Inclusive stop of the time window, eg. '2024-06-30T18:00:00.000Z'.
        :param page:     (Optional) Zero-based page number.
        :param size:     (Optional) Page size (default: 10).
        :return:         Paginated Page[Trial] response.
        """
        params = self._build_params(optional={
            "query": query,
            "startTs": start_ts,
            "stopTs": stop_ts,
            "page": page,
            "size": size,
        })
        raw = self._get("/metadata/trials", params)
        return Page(
            page=raw["page"],
            size=raw["size"],
            total=raw["total"],
            data=[self._build_trial(item) for item in raw["data"]],
        )

    def list_groups(
            self,
            trial_id: str,
            query: Optional[str] = None,
            device_id: Optional[str] = None,
            channel_id: Optional[str] = None,
            page: Optional[int] = None,
            size: Optional[int] = None,
    ) -> Page[Group]:
        """
        Returns the list of groups (sub-levels) within a given trial.

        :param trial_id:   UUID of the parent trial, eg. 'f47ac10b-58cc-4372-a567-0e02b2c3d479'.
        :param query:      (Optional) Text search filter.
        :param device_id:  (Optional) Filter by device ID, eg. '02b82b'.
        :param channel_id: (Optional) Filter by channel ID, eg. '02b82b-1'.
        :param page:       (Optional) Zero-based page number.
        :param size:       (Optional) Page size (default: 10).
        :return:           Paginated Page[Group] response.
        """
        params = self._build_params(
            required={"trialId": trial_id},
            optional={"query": query, "deviceId": device_id, "channelId": channel_id, "page": page, "size": size},
        )
        raw = self._get("/metadata/groups", params)
        return Page(
            page=raw["page"],
            size=raw["size"],
            total=raw["total"],
            data=[self._build_group(item) for item in raw["data"]],
        )

    def list_devices(
            self,
            start_ts: str,
            query: Optional[str] = None,
            stop_ts: Optional[str] = None,
            page: Optional[int] = None,
            size: Optional[int] = None,
    ) -> Page[Device]:
        """
        Returns the list of devices accessible to the authenticated client.

        :param start_ts: Inclusive start of the time window, eg. '2024-01-15T08:00:00.000Z'.
        :param query:    (Optional) Text search filter.
        :param stop_ts:  (Optional) Inclusive stop of the time window, eg. '2024-06-30T18:00:00.000Z'.
        :param page:     (Optional) Zero-based page number.
        :param size:     (Optional) Page size (default: 10).
        :return:         Paginated Page[Device] response.
        """
        params = self._build_params(
            required={"startTs": start_ts},
            optional={"query": query, "stopTs": stop_ts, "page": page, "size": size},
        )
        raw = self._get("/metadata/devices", params)
        return Page(
            page=raw["page"],
            size=raw["size"],
            total=raw["total"],
            data=[self._build_device(item) for item in raw["data"]],
        )

    def list_connections(
            self,
            sub_level_id: str,
            device_id: Optional[str] = None,
            channel_id: Optional[str] = None,
            page: Optional[int] = None,
            size: Optional[int] = None,
    ) -> Page[Connection]:
        """
        Returns the list of device-channel connections for a given group (sub-level).

        :param sub_level_id: UUID of the group (sub-level), eg. 'b2c3d4e5-1234-5678-9abc-def012345678'.
        :param device_id:    (Optional) Filter by device ID, eg. '02b82b'.
        :param channel_id:   (Optional) Filter by channel ID, eg. '02b82b-1'.
        :param page:         (Optional) Zero-based page number.
        :param size:         (Optional) Page size (default: 10).
        :return:             Paginated Page[Connection] response.
        """
        params = self._build_params(
            required={"subLevelId": sub_level_id},
            optional={"deviceId": device_id, "channelId": channel_id, "page": page, "size": size},
        )
        raw = self._get("/metadata/connections", params)
        return Page(
            page=raw["page"],
            size=raw["size"],
            total=raw["total"],
            data=[self._build_connection(item) for item in raw["data"]],
        )

    @staticmethod
    def _build_trial(item: dict) -> Trial:
        return Trial(
            id=item["id"],
            name=item["name"],
            start_ts=item.get("startTs"),
            stop_ts=item.get("stopTs"),
            description=item.get("description"),
            plant_type=NamedEntity(**item["plantType"]) if item.get("plantType") else None,
            stressor_type=NamedEntity(**item["stressorType"]) if item.get("stressorType") else None,
            substrate_type=NamedEntity(**item["substrateType"]) if item.get("substrateType") else None,
            chamber_type=NamedEntity(**item["chamberType"]) if item.get("chamberType") else None,
            geo_location=item.get("geoLocation"),
        )

    @staticmethod
    def _build_group(item: dict) -> Group:
        return Group(
            id=item["id"],
            trial_id=item["trialId"],
            name=item["name"],
            description=item.get("description"),
            start_ts=item.get("startTs"),
            stop_ts=item.get("stopTs"),
            plant_type=NamedEntity(**item["plantType"]) if item.get("plantType") else None,
            stressor_type=NamedEntity(**item["stressorType"]) if item.get("stressorType") else None,
            substrate_type=NamedEntity(**item["substrateType"]) if item.get("substrateType") else None,
        )

    @staticmethod
    def _build_device(item: dict) -> Device:
        return Device(
            id=item["id"],
            name=item["name"],
            note=item.get("note"),
            hardware_type=item.get("hardwareType"),
            geo_location=item.get("geoLocation"),
        )

    @staticmethod
    def _build_connection(item: dict) -> Connection:
        return Connection(
            id=item["id"],
            channel_id=item["channelId"],
            start_ts=item.get("startTs"),
            stop_ts=item.get("stopTs"),
        )
