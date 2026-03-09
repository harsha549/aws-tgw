#!/bin/bash
# =============================================================================
# debug_traffic.sh — TGW traffic path debugger
# =============================================================================
# Usage:
#   ./debug_traffic.sh <src_ip> <dst_ip>
#
# Example:
#   ./debug_traffic.sh 10.0.1.5 10.2.1.8
#
# Prerequisites:
#   - GetAWSCredentials must be available in PATH on this machine
#   - Python 3 and boto3 must be installed
#   - config.py must have correct account short codes and region
# =============================================================================

set -e  # Exit immediately on any error

SRC_IP=$1
DST_IP=$2

# -----------------------------------------------------------------------------
# Validate inputs
# -----------------------------------------------------------------------------
if [ -z "$SRC_IP" ] || [ -z "$DST_IP" ]; then
    echo "Usage: ./debug_traffic.sh <src_ip> <dst_ip>"
    echo "Example: ./debug_traffic.sh 10.0.1.5 10.2.1.8"
    exit 1
fi

# Load short codes from config (keep them in one place)
ACCT_SRC=$(python3 -c "from config import ACCOUNTS; print(ACCOUNTS['src'])")
ACCT_DST=$(python3 -c "from config import ACCOUNTS; print(ACCOUNTS['dst'])")
ACCT_HUB=$(python3 -c "from config import ACCOUNTS; print(ACCOUNTS['hub'])")

echo ""
echo "============================================================"
echo "  TGW Traffic Path Debugger"
echo "============================================================"
echo "  Source IP:      $SRC_IP"
echo "  Dest IP:        $DST_IP"
echo "  Source account: $ACCT_SRC"
echo "  Dest account:   $ACCT_DST"
echo "  Hub account:    $ACCT_HUB"
echo "============================================================"
echo ""

# -----------------------------------------------------------------------------
# Step 1a — Resolve source IP (Account A)
# -----------------------------------------------------------------------------
echo "[Step 1a] Resolving source IP in account: $ACCT_SRC"
GetAWSCredentials $ACCT_SRC
python3 1_resolve_ips.py --ip $SRC_IP --role src --init --dst-ip $DST_IP

# -----------------------------------------------------------------------------
# Step 1b — Resolve destination IP (Account B)
# -----------------------------------------------------------------------------
echo "[Step 1b] Resolving destination IP in account: $ACCT_DST"
GetAWSCredentials $ACCT_DST
python3 1_resolve_ips.py --ip $DST_IP --role dst

# -----------------------------------------------------------------------------
# Step 2 — Discover path via TGW (Account N)
# [TODO] — 2_discover_path.py
# -----------------------------------------------------------------------------
echo "[Step 2] Discovering TGW path in hub account: $ACCT_HUB"
GetAWSCredentials $ACCT_HUB
# python3 2_discover_path.py
echo "[Step 2] (not yet implemented)"

# -----------------------------------------------------------------------------
# Step 3 — Check hops: VPC routes, SGs, NACLs
# [TODO] — 3_check_hops.py
# -----------------------------------------------------------------------------
echo "[Step 3a] Checking source-side hops in account: $ACCT_SRC"
GetAWSCredentials $ACCT_SRC
# python3 3_check_hops.py --account src
echo "[Step 3a] (not yet implemented)"

echo "[Step 3b] Checking hub-side TGW routes in account: $ACCT_HUB"
GetAWSCredentials $ACCT_HUB
# python3 3_check_hops.py --account hub
echo "[Step 3b] (not yet implemented)"

echo "[Step 3c] Checking destination-side hops in account: $ACCT_DST"
GetAWSCredentials $ACCT_DST
# python3 3_check_hops.py --account dst
echo "[Step 3c] (not yet implemented)"

# -----------------------------------------------------------------------------
# Step 4 — Query flow logs
# [TODO] — 4_query_logs.py
# -----------------------------------------------------------------------------
echo "[Step 4a] Querying VPC flow logs in source account: $ACCT_SRC"
GetAWSCredentials $ACCT_SRC
# python3 4_query_logs.py --account src
echo "[Step 4a] (not yet implemented)"

echo "[Step 4b] Querying TGW flow logs in hub account: $ACCT_HUB"
GetAWSCredentials $ACCT_HUB
# python3 4_query_logs.py --account hub
echo "[Step 4b] (not yet implemented)"

echo "[Step 4c] Querying VPC flow logs in dest account: $ACCT_DST"
GetAWSCredentials $ACCT_DST
# python3 4_query_logs.py --account dst
echo "[Step 4c] (not yet implemented)"

# -----------------------------------------------------------------------------
# Step 5 — Summarize findings
# [TODO] — 5_summarize.py
# -----------------------------------------------------------------------------
echo "[Step 5] Summarizing findings..."
# python3 5_summarize.py
echo "[Step 5] (not yet implemented)"

echo ""
echo "============================================================"
echo "  Run complete. State saved to: $(python3 -c 'from config import STATE_FILE; print(STATE_FILE)')"
echo "============================================================"
