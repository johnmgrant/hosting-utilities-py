import sys

from dotenv import load_dotenv

from hosting_utilities.backup_site import backup_site_main
from hosting_utilities.cli_utils import request_cli_input
from hosting_utilities.constants.cli_arguments import (
    EXISTING_SUB_ENV_ARGS,
)
from hosting_utilities.op_utils import is_op_authorized


async def main() -> None:
    load_dotenv()
    if len(sys.argv) < 2:
        print("Usage: hosting_utilities <subprogram> [options]")
        sys.exit(1)

    op_authorized = await is_op_authorized()
    if not op_authorized:
        print("1Password Connect client or Service account is not authorized.")
        sys.exit(1)

    subprogram = sys.argv[1]
    sys.argv = [sys.argv[0]] + sys.argv[2:]  # Remove subprogram from args

    if subprogram == "backup_site":
        args = request_cli_input(
            "backup_site",
            EXISTING_SUB_ENV_ARGS,
        )
        await backup_site_main(args.site_name)
    else:
        print(f"Unknown subprogram: {subprogram}")
        sys.exit(1)
