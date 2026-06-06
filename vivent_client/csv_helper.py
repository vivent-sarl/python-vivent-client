import csv
import io
from datetime import datetime, timezone
from typing import List

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

