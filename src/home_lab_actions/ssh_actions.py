"""
AI Actions for executing commands on remote systems via SSH.
"""

import os
import io
import logging

import paramiko
from dotenv import load_dotenv
from sema4ai.actions import Response, action

load_dotenv()

logger = logging.getLogger(__name__)



@action
def execute_command_on_vision(command: str) -> Response[str]:
    """
    Executes a shell command on the remote Vision system via SSH.

    Args:
        command (str): The shell command to execute.

    Returns:
        Response[str]: The output of the command, or an error message if execution fails.

    This action is useful for remotely managing or querying the Vision system from an automation workflow.
    """

    host = os.getenv("VISION_IP")
    if not host:
        return Response(error="VISION_IP environment variable not set")

    port = 22
    username = os.getenv("VISION_USERNAME", "kdlocpanda")
    password = os.getenv("PASSWORD")
    ssh_key_env = os.getenv("SSH_KEY")
    key_content = ssh_key_env.replace('\\n', '\n') if ssh_key_env else None

    output, error = ssh_execute_command(
        host, port, username, password, key_content, command
    )

    if error:
        return Response(error=error)
    return Response(result=output)


def ssh_execute_command(
    host: str,
    port: int,
    username: str,
    password: str | None = None,
    key_content: str | None = None,
    command: str = "",
) -> tuple[str, str]:
    """Execute a command on a remote system via SSH."""
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if key_content:
            if "BEGIN OPENSSH PRIVATE KEY" in key_content:
                private_key = paramiko.Ed25519Key.from_private_key(
                    file_obj=io.StringIO(key_content)
                )
            else:
                private_key = paramiko.RSAKey.from_private_key(
                    file_obj=io.StringIO(key_content)
                )
            client.connect(
                hostname=host,
                port=port,
                username=username,
                pkey=private_key,
                timeout=10,
            )
        elif password:
            client.connect(
                hostname=host,
                port=port,
                username=username,
                password=password,
                timeout=10,
            )
        else:
            return "", "Authentication method required (key or password)"

        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode("utf-8")
        error = stderr.read().decode("utf-8")
        client.close()
        return output, error

    except Exception as e:
        return "", f"An unexpected error occurred: {e}"
