import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class TokenResponse:
    access_token: str
    refresh_token: str
    expires_in: int
    refresh_expires_in: int
    token_type: str
    issued_at: float = field(default_factory=time.time)

    def is_expired(self, buffer_seconds: int = 30) -> bool:
        """Returns True if the access token is expired (with a safety buffer)."""
        return time.time() >= self.issued_at + self.expires_in - buffer_seconds

    def is_refresh_expired(self, buffer_seconds: int = 30) -> bool:
        """Returns True if the refresh token is expired."""
        return time.time() >= self.issued_at + self.refresh_expires_in - buffer_seconds


@dataclass
class Channel:
    channel_id: str
    start_ts: str
    stop_ts: Optional[str]


@dataclass
class MetricData:
    timestamps: List[int]
    values: List[float]

    def to_records(self) -> List[dict]:
        """Zips timestamps and values into a list of dicts."""
        return [
            {
                "timestamp": ts,
                "datetime": datetime.fromtimestamp(ts / 1000, tz=timezone.utc).isoformat(),
                "value": val,
            }
            for ts, val in zip(self.timestamps, self.values)
        ]
