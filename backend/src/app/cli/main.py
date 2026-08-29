import argparse
import json
import sys
from typing import Any

from app.cli.client import F9l3Client, F9l3CliError


def output_result(data: Any, as_json: bool = False) -> None:
    """Print command output as formatted JSON or human-readable text."""
    if as_json:
        print(json.dumps(data, indent=2))
    elif isinstance(data, dict):
        for k, v in data.items():
            print(f"  {k}: {v}")
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                tid = item.get("id", "")
                fname = item.get("filename", "")
                st = item.get("state", "")
                print(f"- {tid} | {fname} | {st}")
            else:
                print(f"- {item}")
    else:
        print(data)


def build_parser() -> argparse.ArgumentParser:
    """Build f9l3ctl argument parser with inherited global flags."""
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument(
        "--server",
        default="http://127.0.0.1:8000",
        help="Backend API server URL (default: http://127.0.0.1:8000)",
    )
    parent_parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON",
    )

    parser = argparse.ArgumentParser(
        prog="f9l3ctl",
        description="f9l3_53nd — Secure Authenticated File Transfer CLI & Automation Tool",
        parents=[parent_parser],
    )

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # login
    p_login = subparsers.add_parser(
        "login",
        parents=[parent_parser],
        help="Authenticate with server and cache session",
    )
    p_login.add_argument("--username", "-u", required=True, help="Username")
    p_login.add_argument("--password", "-p", required=True, help="Password")

    # send
    p_send = subparsers.add_parser(
        "send",
        parents=[parent_parser],
        help="Encrypt and upload a file payload",
    )
    p_send.add_argument("--file", "-f", required=True, help="Path to file to send")
    p_send.add_argument("--recipient", "-r", required=True, help="Recipient user UUID")

    # list
    p_list = subparsers.add_parser(
        "list",
        parents=[parent_parser],
        help="List transfers visible to user",
    )
    p_list.add_argument("--offset", type=int, default=0, help="Pagination offset")
    p_list.add_argument("--limit", type=int, default=50, help="Pagination limit")

    # status
    p_status = subparsers.add_parser(
        "status",
        parents=[parent_parser],
        help="Get transfer details and verification status",
    )
    p_status.add_argument("--transfer-id", "-t", required=True, help="Transfer UUID")

    # receive
    p_receive = subparsers.add_parser(
        "receive",
        parents=[parent_parser],
        help="Download, decrypt, and verify payload",
    )
    p_receive.add_argument("--transfer-id", "-t", required=True, help="Transfer UUID")
    p_receive.add_argument("--output", "-o", help="Output file path (default: original filename)")

    # verify-audit
    subparsers.add_parser(
        "verify-audit",
        parents=[parent_parser],
        help="Verify cryptographic audit log chain (Admin only)",
    )

    # network-status
    subparsers.add_parser(
        "network-status",
        parents=[parent_parser],
        help="Check WireGuard tunnel status (Admin only)",
    )

    # version
    subparsers.add_parser(
        "version",
        parents=[parent_parser],
        help="Show f9l3ctl version",
    )

    return parser


def main(args_list: list[str] | None = None) -> int:
    """CLI execution entrypoint."""
    parser = build_parser()
    args = parser.parse_args(args_list)

    if not args.command:
        parser.print_help()
        return 0

    client = F9l3Client(server_url=args.server)

    try:
        if args.command == "version":
            output_result({"version": "0.1.0", "algorithm": "AES-256-GCM"}, args.json)
            return 0

        elif args.command == "login":
            res = client.login(username=args.username, password=args.password)
            out = {
                "status": "SUCCESS",
                "message": "Authenticated successfully",
                "user": res.get("user"),
            }
            output_result(out, args.json)
            return 0

        elif args.command == "send":
            res = client.send_file(recipient_id=args.recipient, file_path=args.file)
            output_result(res, args.json)
            return 0

        elif args.command == "list":
            res = client.list_transfers(offset=args.offset, limit=args.limit)
            output_result(res, args.json)
            return 0

        elif args.command == "status":
            res = client.get_transfer_status(transfer_id=args.transfer_id)
            output_result(res, args.json)
            return 0

        elif args.command == "receive":
            out_file = client.receive_file(transfer_id=args.transfer_id, output_path=args.output)
            output_result({"status": "SUCCESS", "downloaded_file": str(out_file)}, args.json)
            return 0

        elif args.command == "verify-audit":
            res = client.verify_audit_chain()
            output_result(res, args.json)
            return 0

        elif args.command == "network-status":
            res = client.get_network_status()
            output_result(res, args.json)
            return 0

    except F9l3CliError as e:
        if args.json:
            print(json.dumps({"error": str(e)}), file=sys.stderr)
        else:
            print(f"[-] Error: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
