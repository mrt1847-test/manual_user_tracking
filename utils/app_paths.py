from pathlib import Path
import sys


def get_resource_root() -> Path:
    """Return the directory that contains bundled runtime resources."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent


def get_config_path() -> Path:
    return get_resource_root() / "config.json"


def get_tracking_schemas_root() -> Path:
    return get_resource_root() / "tracking_schemas"


def get_common_fields_by_event_path() -> Path:
    return get_tracking_schemas_root() / "_common_fields_by_event.json"
