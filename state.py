# =============================================================================
# state.py — Shared state read/write helper
# =============================================================================
# All modules use this to persist findings across credential switches.
# State is stored in a JSON file at the path defined in config.STATE_FILE.
# =============================================================================

import json
import os
from config import STATE_FILE


# -----------------------------------------------------------------------------
# Initial state structure — written once at the start of a run
# -----------------------------------------------------------------------------
INITIAL_STATE = {
    "src": {
        "ip":      None,
        "eni":     None,
        "subnet":  None,
        "vpc":     None,
        "account": None,
        "sg_ids":  [],
        "az":      None,
    },
    "dst": {
        "ip":      None,
        "eni":     None,
        "subnet":  None,
        "vpc":     None,
        "account": None,
        "sg_ids":  [],
        "az":      None,
    },
    "path": {
        "hops":             [],      # ordered list: [vpc_src, tgw_id, vpc_dst]
        "tgw_id":           None,
        "src_attachment":   None,
        "dst_attachment":   None,
        "src_route_table":  None,
        "dst_route_table":  None,
        "route_found":      None,    # True/False
    },
    "checks": {
        "src_vpc_route":    None,    # PASS / FAIL / UNKNOWN
        "src_sg":           None,
        "src_nacl":         None,
        "tgw_src_route":    None,
        "tgw_dst_route":    None,
        "dst_vpc_route":    None,
        "dst_nacl":         None,
        "dst_sg":           None,
        "details":          {},      # per-check detail messages
    },
    "logs": {
        "src_vpc_flow":     None,    # ACCEPT / REJECT / NOT_FOUND / ERROR
        "tgw_flow":         None,
        "dst_vpc_flow":     None,
        "details":          {},      # raw log query results per source
    },
    "errors": [],                    # non-fatal errors encountered during run
}


def init_state(src_ip: str, dst_ip: str) -> dict:
    """Create a fresh state file for a new run."""
    state = INITIAL_STATE.copy()
    state["src"] = {**INITIAL_STATE["src"], "ip": src_ip}
    state["dst"] = {**INITIAL_STATE["dst"], "ip": dst_ip}
    write_state(state)
    print(f"[state] Initialized state file at {STATE_FILE}")
    return state


def read_state() -> dict:
    """Read current state from file. Raises if file doesn't exist."""
    if not os.path.exists(STATE_FILE):
        raise FileNotFoundError(
            f"State file not found at {STATE_FILE}. "
            "Run debug_traffic.sh from the beginning."
        )
    with open(STATE_FILE, "r") as f:
        return json.load(f)


def write_state(state: dict) -> None:
    """Write full state dict to file."""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)


def update_state(updates: dict) -> dict:
    """
    Deep-merge updates into existing state and write back.

    Usage:
        update_state({
            "src": {"eni": "eni-abc123", "vpc": "vpc-111"},
            "checks": {"src_sg": "PASS"}
        })
    """
    state = read_state()
    _deep_merge(state, updates)
    write_state(state)
    return state


def add_error(message: str) -> None:
    """Append a non-fatal error message to state."""
    state = read_state()
    state["errors"].append(message)
    write_state(state)
    print(f"[state] Error recorded: {message}")


def _deep_merge(base: dict, updates: dict) -> None:
    """Recursively merge updates into base dict in-place."""
    for key, value in updates.items():
        if (
            key in base
            and isinstance(base[key], dict)
            and isinstance(value, dict)
        ):
            _deep_merge(base[key], value)
        else:
            base[key] = value
