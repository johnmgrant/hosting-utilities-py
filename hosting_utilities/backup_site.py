import os
import subprocess

from hosting_utilities.op_utils import fetch_fields_from_1password
from scripts.run_command_with_prompt import run_command_with_prompt


async def backup_site_main(site_name) -> None:
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

    PASSWORD_PROMPT_TEMPLATE = "{user}@{host}'s password:"

    env_vars = await fetch_fields_from_1password(OP_FIELD_NAMES, ENV_FIELD_MAP)

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
        f"Backing up static site content from "
        f"{env_vars['REMOTE_USER']}@{env_vars['REMOTE_HOST']}:"
        f"{env_vars['REMOTE_WP_CONTENT']} to {final}"
    )

    remote_cmd = (
        'dir=$(dirname "{remote_wp_content}"); '
        'base=$(basename "{remote_wp_content}"); '
        'tar -C "$dir" -cz "$base"'
    ).format(remote_wp_content=env_vars["REMOTE_WP_CONTENT"])
    ssh_cmd = [
        "ssh",
        "-p",
        env_vars["REMOTE_SSH_PORT"],
        f"{env_vars['REMOTE_USER']}@{env_vars['REMOTE_HOST']}",
        remote_cmd,
    ]

    print(f"Running SSH command: {' '.join(ssh_cmd)}")

    # If REMOTE_PASSWORD is set, provide it to the ssh process when prompted
    ssh_password = env_vars.get("REMOTE_PASSWORD")
    with open(tmp, "wb") as out:
        if ssh_password:
            result = run_command_with_prompt(
                ssh_cmd,
                PASSWORD_PROMPT_TEMPLATE.format(
                    user=env_vars["REMOTE_USER"], host=env_vars["REMOTE_HOST"]
                ),
                ssh_password,
                output_file=out,
            )
            returncode = result if isinstance(result, int) else getattr(result, "returncode", 1)
        else:
            proc = subprocess.run(ssh_cmd, stdout=out)
            returncode = proc.returncode

        if returncode != 0:
            print("Error: SSH/tar command failed.")
            exit(1)

    # gzip integrity check
    gunzip_proc = subprocess.run(["gunzip", "-t", tmp])
    if gunzip_proc.returncode != 0:
        print("Error: gzip integrity check failed.")
        exit(1)

    os.rename(tmp, final)
    print(f"Done: {final}")
