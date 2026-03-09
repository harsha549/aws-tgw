# =============================================================================
# config.py — Central configuration for tgw_debug tool
# =============================================================================
# Edit the values in this file before running debug_traffic.sh
# =============================================================================

# -----------------------------------------------------------------------------
# Target IPs — set these before each run, or pass via CLI args in the shell script
# -----------------------------------------------------------------------------
SRC_IP = "10.0.1.5"       # Source IP to investigate
DST_IP = "10.2.1.8"       # Destination IP to investigate

# -----------------------------------------------------------------------------
# Account short codes — used in GetAWSCredentials <short_code> calls
# -----------------------------------------------------------------------------
ACCOUNTS = {
    "src":  "acct-a",     # Account owning the source VPC
    "dst":  "acct-b",     # Account owning the destination VPC
    "hub":  "acct-n",     # Hub account owning the Transit Gateway
}

# -----------------------------------------------------------------------------
# AWS Region — all 3 accounts are in the same region
# -----------------------------------------------------------------------------
REGION = "ap-southeast-1"

# -----------------------------------------------------------------------------
# State file — shared between all modules
# -----------------------------------------------------------------------------
STATE_FILE = "/tmp/tgw_debug_state.json"

# -----------------------------------------------------------------------------
# CloudWatch Logs settings
# -----------------------------------------------------------------------------
# Log group name pattern — matches groups containing this string
CWL_LOG_GROUP_PATTERN = "vpcflowlogs"

# How far back to search logs (in minutes)
CWL_LOOKBACK_MINUTES = 60

# How long to wait for a CWL Insights query to complete (seconds)
CWL_QUERY_TIMEOUT_SECONDS = 60

# -----------------------------------------------------------------------------
# TGW Flow Log settings
# -----------------------------------------------------------------------------
# TGW flow logs also live in CloudWatch in the hub account
# Same pattern applies: log group name must contain CWL_LOG_GROUP_PATTERN
TGW_FLOW_LOG_ACCOUNT = "hub"

# -----------------------------------------------------------------------------
# Reachability check settings
# -----------------------------------------------------------------------------
# Protocols to check in SG/NACL analysis
# Common values: "tcp", "udp", "-1" (all traffic)
DEFAULT_PROTOCOL = "tcp"

# Port to check — set to None to skip port-specific SG/NACL filtering
DEFAULT_PORT = None
