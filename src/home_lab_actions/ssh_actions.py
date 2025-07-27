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



def execute_command_on_vision(command: str) -> Response[str]:
    """Execute a command on the Vision system via SSH connection.

    Args:
        command (str): The command to execute on the Vision system

    Returns:
        Response[str]: A response indicating the execution status
    """
    host = os.getenv("VISION_IP")
    if not host:
        return Response(error="VISION_IP environment variable not set")

    port = 22
    username = os.getenv("VISION_USERNAME", "kdlocpanda")
    password = os.getenv("PASSWORD")
    ssh_key_env = os.getenv("SSH_KEY")
    tls_crt_env = os.getenv("TLS_CRT")

    key_content = ssh_key_env.replace('\\n', '\n') if ssh_key_env else None
    tls_crt_content = tls_crt_env.replace('\\n', '\n') if tls_crt_env else None

    output, error = ssh_execute_command(
        host, port, username, password, key_content, command, tls_crt_content
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
    tls_crt_content: str | None = None,
) -> tuple[str, str]:
    """
    SSH into a remote device and execute a command.

    Parameters:
        host (str): The hostname or IP address of the remote device.
        port (int): The SSH port (default is usually 22).
        username (str): The SSH username.
        password (str, optional): The SSH password (if using password-based auth).
        key_filepath (str, optional): Path to the private key file (if using key-based auth).
        command (str): The command to execute on the remote device.

    Returns:
        tuple: A tuple (output, error) containing the command's output and error messages.
    """
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

        # If you need to use tls_crt_content, add logic here to use it for TLS connections
        # For now, just pass it through or use as needed in your workflow

        stdin, stdout, stderr = client.exec_command(command)
        output = stdout.read().decode("utf-8")
        error = stderr.read().decode("utf-8")
        client.close()
        return output, error

    except Exception as e:
        return "", f"An unexpected error occurred: {e}"
