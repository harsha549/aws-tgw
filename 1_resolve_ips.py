#!/usr/bin/env python3
# =============================================================================
# 1_resolve_ips.py — Resolve an IP address to its AWS network context
# =============================================================================
# Usage:
#   GetAWSCredentials acct-a && python3 1_resolve_ips.py --ip 10.0.1.5 --role src
#   GetAWSCredentials acct-b && python3 1_resolve_ips.py --ip 10.2.1.8 --role dst
#
# What it does:
#   - Calls ec2:DescribeNetworkInterfaces filtered by private IP
#   - Extracts ENI, subnet, VPC, AZ, security group IDs
#   - Writes results into state.json under the given role (src or dst)
# =============================================================================

import argparse
import sys
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from config import REGION
from state import init_state, update_state, add_error, read_state, STATE_FILE
import os


# -----------------------------------------------------------------------------
# Core resolution logic
# -----------------------------------------------------------------------------

def resolve_ip(ip: str, region: str) -> dict:
    """
    Look up a private IP address and return its network context.

    Returns a dict with: eni, subnet, vpc, az, sg_ids, description, instance_id
    Raises ValueError if the IP is not found in this account.
    """
    ec2 = boto3.client("ec2", region_name=region)

    print(f"[resolve] Searching for IP {ip} in region {region}...")

    try:
        response = ec2.describe_network_interfaces(
            Filters=[
                {
                    "Name": "addresses.private-ip-address",
                    "Values": [ip]
                }
            ]
        )
    except NoCredentialsError:
        raise RuntimeError(
            "No AWS credentials found. "
            "Run GetAWSCredentials <short_code> before this script."
        )
    except ClientError as e:
        raise RuntimeError(f"EC2 API error: {e}")

    interfaces = response.get("NetworkInterfaces", [])

    if not interfaces:
        raise ValueError(
            f"IP {ip} not found in this account/region ({region}). "
            "Check that GetAWSCredentials loaded the correct account."
        )

    if len(interfaces) > 1:
        print(f"[resolve] Warning: {len(interfaces)} ENIs found for {ip}, using first match.")

    eni = interfaces[0]

    # Extract security group IDs
    sg_ids = [sg["GroupId"] for sg in eni.get("Groups", [])]

    # Extract instance ID if attached to EC2
    attachment = eni.get("Attachment", {})
    instance_id = attachment.get("InstanceId")

    result = {
        "eni":         eni["NetworkInterfaceId"],
        "subnet":      eni["SubnetId"],
        "vpc":         eni["VpcId"],
        "az":          eni["AvailabilityZone"],
        "sg_ids":      sg_ids,
        "description": eni.get("Description", ""),
        "instance_id": instance_id,
        "status":      eni.get("Status"),
    }

    return result


def get_subnet_cidr(subnet_id: str, region: str) -> str:
    """Fetch the CIDR block for a given subnet — needed for route table checks later."""
    ec2 = boto3.client("ec2", region_name=region)
    try:
        response = ec2.describe_subnets(SubnetIds=[subnet_id])
        subnets = response.get("Subnets", [])
        if subnets:
            return subnets[0]["CidrBlock"]
    except ClientError as e:
        print(f"[resolve] Warning: could not fetch subnet CIDR for {subnet_id}: {e}")
    return None


def get_vpc_cidr(vpc_id: str, region: str) -> str:
    """Fetch the primary CIDR block for a VPC."""
    ec2 = boto3.client("ec2", region_name=region)
    try:
        response = ec2.describe_vpcs(VpcIds=[vpc_id])
        vpcs = response.get("Vpcs", [])
        if vpcs:
            return vpcs[0]["CidrBlock"]
    except ClientError as e:
        print(f"[resolve] Warning: could not fetch VPC CIDR for {vpc_id}: {e}")
    return None


def get_account_id(region: str) -> str:
    """Get the current account ID via STS."""
    sts = boto3.client("sts", region_name=region)
    try:
        return sts.get_caller_identity()["Account"]
    except ClientError as e:
        print(f"[resolve] Warning: could not get account ID: {e}")
    return None


# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Resolve an IP to its AWS network context and save to state."
    )
    parser.add_argument(
        "--ip",
        required=True,
        help="Private IP address to resolve (e.g. 10.0.1.5)"
    )
    parser.add_argument(
        "--role",
        required=True,
        choices=["src", "dst"],
        help="Whether this IP is the source or destination"
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize a fresh state file (use only on first run with --role src)"
    )
    parser.add_argument(
        "--dst-ip",
        help="Destination IP (required when --init is set, to initialize full state)"
    )
    args = parser.parse_args()

    # ------------------------------------------------------------------
    # Initialize state file if requested (first run only)
    # ------------------------------------------------------------------
    if args.init:
        if args.role != "src":
            print("[resolve] Error: --init should only be used with --role src")
            sys.exit(1)
        if not args.dst_ip:
            print("[resolve] Error: --init requires --dst-ip to be set")
            sys.exit(1)
        init_state(src_ip=args.ip, dst_ip=args.dst_ip)
    else:
        # Ensure state file exists from a prior --init run
        if not os.path.exists(STATE_FILE):
            print(
                f"[resolve] Error: state file not found at {STATE_FILE}.\n"
                "Run with --init --role src first."
            )
            sys.exit(1)

    # ------------------------------------------------------------------
    # Resolve the IP
    # ------------------------------------------------------------------
    try:
        result = resolve_ip(args.ip, REGION)
    except ValueError as e:
        print(f"[resolve] Not found: {e}")
        add_error(str(e))
        sys.exit(1)
    except RuntimeError as e:
        print(f"[resolve] Error: {e}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Enrich with subnet and VPC CIDRs
    # ------------------------------------------------------------------
    result["subnet_cidr"] = get_subnet_cidr(result["subnet"], REGION)
    result["vpc_cidr"]    = get_vpc_cidr(result["vpc"], REGION)
    result["account_id"]  = get_account_id(REGION)

    # ------------------------------------------------------------------
    # Print findings
    # ------------------------------------------------------------------
    role_label = "Source" if args.role == "src" else "Destination"
    print(f"\n{'='*60}")
    print(f"  {role_label} IP resolved: {args.ip}")
    print(f"{'='*60}")
    print(f"  ENI:         {result['eni']}")
    print(f"  Subnet:      {result['subnet']}  ({result.get('subnet_cidr', 'unknown')})")
    print(f"  VPC:         {result['vpc']}  ({result.get('vpc_cidr', 'unknown')})")
    print(f"  AZ:          {result['az']}")
    print(f"  Account ID:  {result.get('account_id', 'unknown')}")
    print(f"  SGs:         {', '.join(result['sg_ids']) or 'none'}")
    print(f"  Instance:    {result.get('instance_id') or 'not an EC2 instance'}")
    print(f"  ENI Status:  {result.get('status')}")
    print(f"  Description: {result.get('description') or '—'}")
    print(f"{'='*60}\n")

    # ------------------------------------------------------------------
    # Write to state
    # ------------------------------------------------------------------
    update_state({
        args.role: {
            "ip":          args.ip,
            "eni":         result["eni"],
            "subnet":      result["subnet"],
            "subnet_cidr": result.get("subnet_cidr"),
            "vpc":         result["vpc"],
            "vpc_cidr":    result.get("vpc_cidr"),
            "az":          result["az"],
            "sg_ids":      result["sg_ids"],
            "account_id":  result.get("account_id"),
            "instance_id": result.get("instance_id"),
            "description": result.get("description"),
        }
    })

    print(f"[resolve] {role_label} context saved to state.")


if __name__ == "__main__":
    main()
