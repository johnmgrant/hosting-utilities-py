from typing import Dict

from hosting_utilities.models.cli_argument_options import CLIArgumentOptions

OP_CLIENT_ENV_ARGS: Dict[str, CLIArgumentOptions] = {
    "op_connect_token": {"help": "1Password Connect token", "required": True},
    "op_connect_host": {"help": "1Password Connect host", "required": True},
}

OPTIONAL_SUB_PROGRAM_SITE_ARGS: Dict[str, CLIArgumentOptions] = {
    "op_item_name": {"help": "1Password item name", "required": False},
    "op_vault_name": {"help": "1Password vault name", "required": False},
}

REQUIRED_SUB_ENV_ARGS: Dict[str, CLIArgumentOptions] = {
    "site_name": {"help": "Name of the site to backup", "required": True},
}

EXISTING_SUB_ENV_ARGS: Dict[str, CLIArgumentOptions] = {
    **REQUIRED_SUB_ENV_ARGS,
    **OPTIONAL_SUB_PROGRAM_SITE_ARGS,
}

REQUIRED_NEW_SUB_ENV_ARGS: Dict[str, CLIArgumentOptions] = {
    k: {**v, "required": True}
    for d in (REQUIRED_SUB_ENV_ARGS, OPTIONAL_SUB_PROGRAM_SITE_ARGS)
    for k, v in d.items()
}
