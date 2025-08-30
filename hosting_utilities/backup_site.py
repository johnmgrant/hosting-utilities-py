import os
import subprocess

try:
    from onepasswordconnectsdk.client import Client as OPClient
except ImportError:
    OPClient = None

# These must match the field *labels* in your 1Password item
OP_FIELD_NAMES = [
    "user",
    "server",
    "port",
    "password",
    "remote_backup_dir",
    "local_dest_dir",
]

ENV_FIELD_MAP = {
    "user": "REMOTE_USER",
    "server": "REMOTE_HOST",
    "port": "REMOTE_SSH_PORT",
    "password": "REMOTE_PASSWORD",
    "remote_backup_dir": "REMOTE_WP_CONTENT",
    "local_dest_dir": "LOCAL_DEST_DIR",
}

PROMPTS = {
    "user": "Remote SSH username",
    "server": "Remote SSH server hostname",
    "port": "Remote SSH port",
    "password": "Remote SSH password",
    "remote_backup_dir": "Remote WordPress content directory (absolute path)",
    "local_dest_dir": "Local destination directory (absolute path)",
}


def fetch_fields_from_1password():
    """
    Fetch required fields from 1Password using onepasswordconnectsdk and environment variables for item and vault names.
    Returns a dict mapping ENV_FIELD_MAP values to their corresponding values.
    """
    if OPClient is None:
        raise ImportError(
            "The 'onepasswordconnectsdk' library is required to fetch credentials from 1Password Connect."
        )
    op_item_name = os.environ.get("OP_ITEM_NAME")
    op_vault_name = os.environ.get("OP_VAULT_NAME")
    op_connect_token = os.environ.get("OP_CONNECT_TOKEN")
    op_connect_host = os.environ.get("OP_CONNECT_HOST")
    if not op_item_name or not op_vault_name:
        raise RuntimeError(
            "OP_ITEM_NAME and OP_VAULT_NAME environment variables must be set."
        )
    if not op_connect_token or not op_connect_host:
        raise RuntimeError(
            "OP_CONNECT_TOKEN and OP_CONNECT_HOST environment variables must be set for 1Password Connect."
        )
    client = OPClient(url=op_connect_host, token=op_connect_token)
    item = client.get_item_by_title(op_vault_name, op_item_name)
    # item.fields is a list of field objects with 'label' and 'value', but may be None
    fields = {
        f.label: f.value for f in (item.fields or []) if f.label in OP_FIELD_NAMES
    }
    env_vars = {ENV_FIELD_MAP[k]: v for k, v in fields.items() if k in ENV_FIELD_MAP}
    return env_vars


def backup_site_main(site_name):
    env_vars = fetch_fields_from_1password()

    # Validate local destination directory
    local_dest_dir = env_vars["LOCAL_DEST_DIR"]
    local_dest_dir = os.path.expandvars(local_dest_dir)
    if not os.path.isdir(local_dest_dir):
        print(f"Error: Local destination directory '{local_dest_dir}' does not exist.")
        exit(1)

    # Ensure dir path ends with the sitename
    local_dest = os.path.join(local_dest_dir.rstrip("/"), site_name)
    os.makedirs(local_dest, exist_ok=True)

    stamp = subprocess.check_output(["date", "+%m-%d-%y"]).decode().strip()
    tmp = os.path.join(local_dest, f"{stamp}.tar.gz.part")
    final = os.path.join(local_dest, f"{stamp}.tar.gz")

    print(
        f"Backing up WordPress content from {env_vars['REMOTE_USER']}@{env_vars['REMOTE_HOST']}:{env_vars['REMOTE_WP_CONTENT']} to {final}"
    )

    ssh_cmd = [
        "ssh",
        "-p",
        env_vars["REMOTE_SSH_PORT"],
        f"{env_vars['REMOTE_USER']}@{env_vars['REMOTE_HOST']}",
        f'dir=$(dirname {env_vars["REMOTE_WP_CONTENT"]}); base=$(basename {env_vars["REMOTE_WP_CONTENT"]}); tar -C "$dir" -cz "$base"',
    ]

    with open(tmp, "wb") as out:
        proc = subprocess.run(ssh_cmd, stdout=out)
        if proc.returncode != 0:
            print("Error: SSH/tar command failed.")
            exit(1)

    # gzip integrity check
    gunzip_proc = subprocess.run(["gunzip", "-t", tmp])
    if gunzip_proc.returncode != 0:
        print("Error: gzip integrity check failed.")
        exit(1)

    os.rename(tmp, final)
    print(f"Done: {final}")
