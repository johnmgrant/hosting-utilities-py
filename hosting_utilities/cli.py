import sys

from hosting_utilities.backup_site import backup_site_main
from hosting_utilities.cli_utils import request_cli_input


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: hosting_utilities <subprogram> [options]")
        sys.exit(1)
    subprogram = sys.argv[1]
    sys.argv = [sys.argv[0]] + sys.argv[2:]  # Remove subprogram from args
    if subprogram == "backup-wp":
        args = request_cli_input(
            "backup-wp",
            {"site_name": {"help": "Name of the site to backup", "required": True}},
        )
        backup_site_main(args.site_name)
    else:
        print(f"Unknown subprogram: {subprogram}")
        sys.exit(1)
