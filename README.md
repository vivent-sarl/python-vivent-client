

# vivent-client

A Python client library for the [Vivent Biosignals](https://vivent-biosignals.com) public API.

## Requirements

- Python >= 3.13
- `requests`

## Installation
```
bash
pip install vivent-client
```
## Quick Start
```
python
from vivent_client import ViventClient

client = ViventClient(
    auth_code="YOUR_AUTH_CODE",
    username="YOUR_USERNAME",
    password="YOUR_PASSWORD",
)

# List available channels
channels = client.list_channels(start_ts="2024-01-31T14:00:00Z")

# List available metrics
metrics = client.list_metrics()

# Fetch time-series data for a single channel
data = client.get_metric(
    metric="water-status-ssp",
    source_id="2561775-1",
    start_ts="2024-01-31T14:00:00Z",
    stop_ts="2024-01-31T15:00:00Z",
    resolution="MINUTES_5",
)

# Fetch aggregated data across multiple channels
agg = client.get_aggregate_metric(
    metric="water-status-ssp",
    source_ids=["2561775-1", "2561662-1"],
    start_ts="2024-01-31T14:00:00Z",
    resolution="MINUTES_5",
    function="MEAN",
)
```
See [`example.py`](example.py) for a full usage walkthrough.

## Authentication

Credentials (`AUTH_CODE`, `USERNAME`, `PASSWORD`) are provided by Vivent. The client
handles token acquisition, refresh, and re-authentication automatically.

## License

MIT
