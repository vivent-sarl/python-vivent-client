from vivent_client import ViventClient
import csv
import io
from datetime import datetime, timezone
from typing import List

# ---------------------------------------------------------------------------
# Example Usage
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

if __name__ == "__main__":
    # --- Credentials (replace with values provided by Vivent) ---
    AUTH_CODE = ""
    USERNAME  = ""
    PASSWORD  = ""

    client = ViventClient(auth_code=AUTH_CODE, username=USERNAME, password=PASSWORD)

    # 1. List available channels
    print("\n=== Available Channels ===")
    channels = client.list_channels(
        start_ts="2026-06-05T14:00:00Z",
        stop_ts="2026-06-06T15:00:00Z",
    )
    print(f"Total channels: {len(channels)}")
    for ch in channels:
        print(f"  Channel: {ch.channel_id}  |  {ch.start_ts} → {ch.stop_ts or 'N/A'}")

    # 2. List available metrics
    print("\n=== Available Metrics ===")
    metrics = client.list_metrics()
    for m in metrics:
        print(f"  - {m}")

    # 3. Get single-channel metric (JSON)
    print("\n=== Single Channel Metric (JSON) ===")
    metric_data = client.get_metric(
        metric="water-status-ssp",
        source_id="251775-1",
        start_ts="2024-01-31T14:00:00Z",
        stop_ts="2024-01-31T14:15:00Z",
        resolution="MINUTES_5",
    )
    for record in metric_data.to_records():
        print(f"  {record['datetime']}  →  {record['value']:.4f}")

    # 4. Get single-channel metric (CSV) and save to file
    print("\n=== Single Channel Metric (CSV) ===")
    raw_csv = client.get_metric_csv(
        metric="phosphorus-status-25q2",
        source_id="2561775-1",
        start_ts="2026-06-05T14:00:00Z",
        stop_ts="2026-06-06T14:15:00Z",
        resolution="MINUTES_5",
    )
    parsed = parse_csv(raw_csv)
    for record in parsed:
        print(f"  {record['datetime']}  →  {record['value']:.4f}")
    save_csv(raw_csv, "water_status_single.csv")

    # 5. Get aggregated metric across multiple channels (JSON)
    print("\n=== Aggregate Metric (JSON) ===")
    agg_data = client.get_aggregate_metric(
        metric="phosphorus-status-25q2",
        source_ids=["2561775-1", "2561662-1"],
        start_ts="2026-06-05T10:00:00Z",
        stop_ts="2026-06-05T06:15:00Z",
        resolution="MINUTES_5",
        function="MEAN",
        partials_strategy="SKIP",
    )
    for record in agg_data.to_records():
        print(f"  {record['datetime']}  →  {record['value']:.4f}")

    # 6. Get aggregated metric (CSV) and save to file
    print("\n=== Aggregate Metric (CSV) ===")
    raw_agg_csv = client.get_aggregate_metric_csv(
        metric="phosphorus-status-25q2",
        source_ids=["2561775-1", "2561662-1"],
        start_ts="2026-06-04T14:00:00Z",
        stop_ts="2026-06-05T14:15:00Z",
        resolution="MINUTES_5",
        function="MEAN",
    )
    save_csv(raw_agg_csv, "water_status_aggregate.csv")
