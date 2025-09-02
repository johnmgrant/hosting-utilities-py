import argparse
import os
from typing import Dict, Optional

from dotenv import load_dotenv

from hosting_utilities.constants.cli_arguments import CLIArgumentOptions


def request_cli_input(
    subprogram: str,
    arg_definitions: Dict[str, CLIArgumentOptions],
    required_arg_definitions: Optional[Dict[str, CLIArgumentOptions]] = None,
) -> argparse.Namespace:
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

    args = parser.parse_args()

    # Check if the site environment file exists, and extract the environment variables
    env_vars: Dict[str, str] | None = None
    if args.site_name:
        env_vars = extract_env_vars(args.site_name)
        if env_vars:
            for key, value in env_vars.items():
                setattr(args, key, value)
        else:
            create_env_file(
                args.site_name,
                {
                    f"{key.upper()}": value
                    for key, value in args.__dict__.items()
                    if value is not None
                },
            )
            load_env_vars(args.site_name)

    # Verify that the required arguments are present based on if the option has
    # required set to True.
    if required_arg_definitions:
        for arg, opts in required_arg_definitions.items():
            if opts.get("required") and not getattr(args, arg, None):
                parser.error(f"Missing required argument: --{arg}")

    return args


def load_env_vars(site_name: str, env_dir: str = "environments") -> None:
    """
    Load environment variables from a .env file.
    """
    env_path = os.path.join(env_dir, f".{site_name}.env")
    load_dotenv(dotenv_path=env_path)
    print(f"Loaded environment variables from the {env_path} file.")


def extract_env_vars(site_name: str, env_dir: str = "environments") -> Dict[str, str] | None:
    """
    Extract and load variables from .env file for the given site_name.
    Returns a dict of env variables if file exists, else empty dict.
    """
    env_path = os.path.join(env_dir, f".{site_name}.env")
    env_vars: Dict[str, str] | None = None
    if os.path.isfile(env_path):
        env_vars = {}
        with open(env_path) as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, sep, value = line.partition("=")
                    if sep and value.strip():
                        env_vars[key.strip()] = value.strip()

    # If the env_vars exist, load them into the environment
    if env_vars:
        load_env_vars(site_name, env_dir)

    return env_vars


def create_env_file(
    site_name: str, env_vars: Dict[str, str], env_dir: str = "environments"
) -> None:
    """
    Create a new .env file for the given site_name with the specified environment variables.
    """
    os.makedirs(env_dir, exist_ok=True)
    env_path = os.path.join(env_dir, f".{site_name}.env")

    with open(env_path, "w") as f:
        for key, value in env_vars.items():
            f.write(f'{key.upper()}="{value}"\n')

    print(f"Created environment file at {env_path}")
