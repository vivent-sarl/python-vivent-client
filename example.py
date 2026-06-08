
from vivent_client import ViventClient
import csv
import io
from datetime import datetime, timezone
from typing import List

# ---------------------------------------------------------------------------
# Example Usage
# ---------------------------------------------------------------------------

AUTH_CODE = ""
USERNAME  = ""
PASSWORD  = ""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_csv(raw_csv: str) -> List[dict]:
    """Parses a Vivent CSV response string into a list of record dicts."""
    reader = csv.DictReader(io.StringIO(raw_csv))
    return [
        {
            "timestamp": int(row["timestamp"]),
            "datetime": datetime.fromtimestamp(
                int(row["timestamp"]) / 1000, tz=timezone.utc
            ).isoformat(),
            "value": float(row["value"]),
        }
        for row in reader
    ]


def save_csv(raw_csv: str, filepath: str) -> None:
    """Saves a raw CSV string to a file."""
    with open(filepath, "w", newline="") as f:
        f.write(raw_csv)
    print(f"[CSV] Saved to {filepath}")


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------

def fetch_channels(client: ViventClient):
    return client.list_channels(
        start_ts="2026-06-05T14:00:00Z",
        stop_ts="2026-06-06T15:00:00Z",
    )


def fetch_metrics(client: ViventClient):
    return client.list_metrics()


def fetch_metric(client: ViventClient):
    return client.get_metric(
        metric="water-status-ssp",
        source_id="251775-1",
        start_ts="2026-06-04T14:00:00Z",
        stop_ts="2026-06-05T14:15:00Z",
        resolution="MINUTES_5",
    )


def fetch_metric_csv(client: ViventClient):
    return client.get_metric_csv(
        metric="phosphorus-status-25q2",
        source_id="2561775-1",
        start_ts="2026-06-05T14:00:00Z",
        stop_ts="2026-06-06T14:15:00Z",
        resolution="MINUTES_5",
    )


def fetch_aggregate_metric(client: ViventClient):
    return client.get_aggregate_metric(
        metric="phosphorus-status-25q2",
        source_ids=["2561775-1", "2561662-1"],
        start_ts="2026-06-04T14:00:00Z",
        stop_ts="2026-06-05T14:15:00Z",
        resolution="MINUTES_5",
        function="MEAN",
        partials_strategy="SKIP",
    )


def fetch_aggregate_metric_csv(client: ViventClient):
    return client.get_aggregate_metric_csv(
        metric="phosphorus-status-25q2",
        source_ids=["2561775-1", "2561662-1"],
        start_ts="2026-06-04T14:00:00Z",
        stop_ts="2026-06-05T14:15:00Z",
        resolution="MINUTES_5",
        function="MEAN",
    )


# ---------------------------------------------------------------------------
# Print
# ---------------------------------------------------------------------------

def print_channels(channels_page) -> None:
    print("\n=== Available Channels ===")
    print(f"Total channels: {channels_page.size}")
    for ch in channels_page.data:
        print(f"  Channel: {ch.channel_id}  |  {ch.start_ts} → {ch.stop_ts or 'N/A'}")


def print_metrics(metrics) -> None:
    print("\n=== Available Metrics ===")
    for m in metrics:
        print(f"  - {m}")


def print_metric(metric_data) -> None:
    print("\n=== Single Channel Metric (JSON) ===")
    for record in metric_data.to_records():
        print(f"  {record['datetime']}  →  {record['value']:.4f}")


def print_metric_csv(raw_csv: str) -> None:
    print("\n=== Single Channel Metric (CSV) ===")
    parsed = parse_csv(raw_csv)
    for record in parsed:
        print(f"  {record['datetime']}  →  {record['value']:.4f}")
    save_csv(raw_csv, "water_status_single.csv")


def print_aggregate_metric(agg_data) -> None:
    print("\n=== Aggregate Metric (JSON) ===")
    for record in agg_data.to_records():
        print(f"  {record['datetime']}  →  {record['value']:.4f}")


def print_aggregate_metric_csv(raw_agg_csv: str) -> None:
    print("\n=== Aggregate Metric (CSV) ===")
    save_csv(raw_agg_csv, "water_status_aggregate.csv")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    client = ViventClient(auth_code=AUTH_CODE, username=USERNAME, password=PASSWORD)

    channels_page = fetch_channels(client)
    print_channels(channels_page)

    metrics = fetch_metrics(client)
    print_metrics(metrics)

    metric_data = fetch_metric(client)
    print_metric(metric_data)

    raw_csv = fetch_metric_csv(client)
    print_metric_csv(raw_csv)

    agg_data = fetch_aggregate_metric(client)
    print_aggregate_metric(agg_data)

    raw_agg_csv = fetch_aggregate_metric_csv(client)
    print_aggregate_metric_csv(raw_agg_csv)