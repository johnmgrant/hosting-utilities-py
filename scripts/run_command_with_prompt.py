from io import BufferedWriter
from typing import Optional

import pexpect


def run_command_with_prompt(
    cmd: list[str],
    prompt: str,
    response: str,
    output_file: Optional[BufferedWriter] = None,
    timeout: int = 30,
) -> int:
    """
    Run a command using pexpect, wait for a prompt, and send a response.
    Optionally write stdout to output_file.
    Args:
        cmd: list of command arguments (e.g. ["ssh", ...])
        prompt: string or regex to expect (e.g. "password:")
        response: string to send when prompt is seen
        output_file: file object to write stdout to (optional)
        timeout: seconds to wait for prompt
    Returns:
        exit status (int)
    """
    child = pexpect.spawn(cmd[0], cmd[1:], timeout=timeout)  # bytes mode
    try:
        # Ensure prompt and response are bytes
        prompt_bytes = prompt if isinstance(prompt, bytes) else prompt.encode("utf-8")
        response_bytes = response if isinstance(response, bytes) else response.encode("utf-8")
        idx = child.expect([prompt_bytes, pexpect.EOF, pexpect.TIMEOUT])
        if idx == 0:
            child.sendline(response_bytes)
        if output_file and child.before:
            output_file.write(child.before)
            # Read remaining output after sending response
            child.expect(pexpect.EOF)
            output_file.write(child.before)
        else:
            # Consume all output
            child.read()

    except Exception as e:
        print(f"pexpect error: {e}")
        child.close()
        return child.exitstatus if child.exitstatus is not None else 1

    if child.exitstatus is not None and child.exitstatus != 0:
        print(f"Command failed with exit status {child.exitstatus}")
        child.close()
        return child.exitstatus

    return child.exitstatus if child.exitstatus is not None else 0
