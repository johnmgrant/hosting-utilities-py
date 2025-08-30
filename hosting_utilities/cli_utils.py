import argparse
import os
from typing import Any, Dict


def request_cli_input(subprogram: str, arg_definitions: Dict[str, Dict[str, Any]]):
    """
    Reusable function to request input fields for CLI commands.
    subprogram: Name of the subprogram (str)
    arg_definitions: Dict of argument definitions, e.g.:
        {
            'site_name': {'help': 'Name of the site', 'required': True},
            ...
        }
    Returns: argparse.Namespace with parsed arguments
    """
    parser = argparse.ArgumentParser(prog=subprogram)
    for arg, opts in arg_definitions.items():
        parser.add_argument(f"--{arg}", **opts)
    return parser.parse_args()


def extract_env_vars(site_name: str, env_dir: str = "environments") -> Dict[str, str]:
    """
    Extract variables from .env file for the given site_name.
    Returns a dict of env variables if file exists, else empty dict.
    """
    env_path = os.path.join(env_dir, f".{site_name}.env")
    env_vars = {}
    if os.path.isfile(env_path):
        with open(env_path) as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, sep, value = line.partition("=")
                    if sep:
                        env_vars[key.strip()] = value.strip()
    return env_vars
