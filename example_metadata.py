from vivent_client import ViventClient

# ---------------------------------------------------------------------------
# Example Usage – Metadata
# ---------------------------------------------------------------------------

AUTH_CODE = ""
USERNAME  = ""
PASSWORD  = ""


# ---------------------------------------------------------------------------
# Fetch
# ---------------------------------------------------------------------------

def fetch_trials(client: ViventClient):
    return client.list_trials(
        start_ts="2024-01-01T00:00:00Z",
        size=5,
    )


def fetch_groups(client: ViventClient, trial_id: str):
    return client.list_groups(
        trial_id=trial_id,
        size=5,
    )


def fetch_connections(client: ViventClient, group_id: str):
    return client.list_connections(
        sub_level_id=group_id,
        size=5,
    )


def fetch_devices(client: ViventClient):
    return client.list_devices(
        start_ts="2024-01-01T00:00:00Z",
        size=5,
    )


# ---------------------------------------------------------------------------
# Print
# ---------------------------------------------------------------------------

def print_trials(trials_page) -> None:
    print("\n=== Trials ===")
    print(f"Total trials: {trials_page.total}  |  Page {trials_page.page}, size {trials_page.size}")
    for trial in trials_page.data:
        plant  = trial.plant_type.name    if trial.plant_type    else "N/A"
        stress = trial.stressor_type.name if trial.stressor_type else "N/A"
        print(
            f"  [{trial.id}]  {trial.name}"
            f"  |  {trial.start_ts or 'N/A'} → {trial.stop_ts or 'N/A'}"
            f"  |  plant: {plant}  |  stressor: {stress}"
        )


def print_groups(groups_page, trial_name: str) -> None:
    print(f"\n=== Groups in trial '{trial_name}' ===")
    print(f"Total groups: {groups_page.total}  |  Page {groups_page.page}, size {groups_page.size}")
    for group in groups_page.data:
        substrate = group.substrate_type.name if group.substrate_type else "N/A"
        print(
            f"  [{group.id}]  {group.name}"
            f"  |  {group.start_ts or 'N/A'} → {group.stop_ts or 'N/A'}"
            f"  |  substrate: {substrate}"
        )


def print_connections(connections_page, group_name: str) -> None:
    print(f"\n=== Connections in group '{group_name}' ===")
    print(f"Total connections: {connections_page.total}  |  Page {connections_page.page}, size {connections_page.size}")
    for conn in connections_page.data:
        print(
            f"  [{conn.id}]  channel: {conn.channel_id}"
            f"  |  {conn.start_ts or 'N/A'} → {conn.stop_ts or 'N/A'}"
        )


def print_devices(devices_page) -> None:
    print("\n=== Devices ===")
    print(f"Total devices: {devices_page.total}  |  Page {devices_page.page}, size {devices_page.size}")
    for device in devices_page.data:
        print(
            f"  [{device.id}]  {device.name}"
            f"  |  hw: {device.hardware_type or 'N/A'}"
            f"  |  location: {device.geo_location or 'N/A'}"
            f"  |  note: {device.note or 'N/A'}"
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    client = ViventClient(auth_code=AUTH_CODE, username=USERNAME, password=PASSWORD)

    trials_page = fetch_trials(client)
    print_trials(trials_page)

    if trials_page.data:
        first_trial = trials_page.data[0]
        groups_page = fetch_groups(client, first_trial.id)
        print_groups(groups_page, first_trial.name)

        if groups_page.data:
            first_group = groups_page.data[0]
            connections_page = fetch_connections(client, first_group.id)
            print_connections(connections_page, first_group.name)

    devices_page = fetch_devices(client)
    print_devices(devices_page)