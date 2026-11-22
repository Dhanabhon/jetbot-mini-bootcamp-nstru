"""Per-robot tuned values (motor trim, PID gains, thresholds) carried from one module to the next.

Stored as a flat JSON object in my_params.json at the repo root, which git ignores because
every robot has its own values.
"""
import json
import os
from typing import Any, Dict

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARAMS_PATH = os.path.join(REPO_ROOT, "my_params.json")


def load_params(path: str = PARAMS_PATH) -> Dict[str, Any]:
    """Saved values, or {} if nothing has been saved yet."""
    if not os.path.exists(path):
        return {}
    with open(path) as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("{} must hold a JSON object, found {}".format(path, type(data).__name__))
    return data


def save_params(path: str = PARAMS_PATH, **updates: Any) -> Dict[str, Any]:
    """Merge updates into the saved values and return the new full set."""
    merged = dict(load_params(path), **updates)
    tmp = path + ".tmp"
    with open(tmp, "w") as handle:
        json.dump(merged, handle, indent=2, sort_keys=True)
    os.replace(tmp, path)  # never leave a half-written file if the kernel dies mid-save
    return merged
