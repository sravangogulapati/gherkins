from __future__ import annotations

import re
import socket
import subprocess
import sys
import platform

import paramiko
from scp import SCPClient
from colorama import Fore, Style
from paramiko_expect import SSHClientInteraction


def local_exec(exec_str: str) -> None:
    """Execute shell commands locally while maintaining context between commands.

    Commands in *exec_str* are split by newline and executed sequentially
    inside a single persistent shell session (``cmd.exe`` on Windows,
    ``/bin/bash`` on Unix/macOS).  This means state-changing operations such
    as ``cd`` and ``export`` carry over to subsequent commands, unlike
    repeated ``subprocess.run`` calls.

    Each command is printed with a ``>`` prefix before execution.  Output is
    captured and displayed after each command.  Progress-indicator lines
    (e.g. ``0% [Working]``) and ANSI escape sequences are stripped from the
    output for cleaner display.

    The implementation uses unique start/end markers written to the shell's
    stdout so that each command's output can be isolated from shell prompts
    and command echoes.

    Args:
        exec_str: One or more shell commands separated by newlines.  Leading
            and trailing whitespace on each line is stripped; blank lines are
            ignored.

    Example::

        local_exec(\"\"\"
            cd ./my-project
            git pull
            docker build -t myapp .
        \"\"\")
    """
    lines = [line.strip() for line in exec_str.strip().split('\n')]
    lines = [line for line in lines if line]

    if not lines:
        return

    shell_cmd = 'cmd.exe' if platform.system() == 'Windows' else '/bin/bash'

    process = subprocess.Popen(
        shell_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    try:
        for i, line in enumerate(lines):
            print(">", line)

            start_marker = f"__CMD_{i}_START__"
            end_marker = f"__CMD_{i}_END__"

            process.stdin.write(f"echo {start_marker}\n")
            process.stdin.write(f"{line}\n")
            process.stdin.write(f"echo {end_marker}\n")
            process.stdin.flush()

            output_buffer = ""
            while True:
                try:
                    char = process.stdout.read(1)
                    if not char:
                        break
                    output_buffer += char
                    if end_marker in output_buffer:
                        break
                except (IOError, OSError, EOFError):
                    break

            output_lines = output_buffer.split('\n')
            start_idx = -1
            end_idx = -1

            for idx, out_line in enumerate(output_lines):
                if 'echo ' + start_marker in out_line or 'echo ' + end_marker in out_line:
                    continue
                if start_marker in out_line and start_idx == -1:
                    start_idx = idx
                if end_marker in out_line:
                    end_idx = idx

            if start_idx >= 0 and end_idx >= 0 and start_idx < end_idx:
                output_lines = output_lines[start_idx + 1:end_idx]
            else:
                output_lines = []

            for out_line in output_lines:
                out_line = out_line.rstrip('\r').lstrip('\r')
                out_line = re.sub(r'\x1b\[[0-9;]*m', '', out_line)
                out_line = re.sub(r'\x1b\[[?0-9;]*[a-zA-Z]', '', out_line)
                if re.match(r'^\s*\d+%', out_line) or re.search(r'\d+%\s*$', out_line):
                    continue
                if out_line and out_line.strip():
                    print(out_line)

        process.stdin.write('exit\n')
        process.stdin.flush()

    except Exception as e:
        print(Fore.RED + f"Error during execution: {e}" + Style.RESET_ALL)
    finally:
        try:
            process.stdin.close()
        except (paramiko.SSHException, socket.error):
            pass
        process.wait()


class ServerConnection:
    """SSH client wrapper for executing commands and transferring files remotely.

    Uses `paramiko <https://www.paramiko.org/>`_ for the SSH transport and
    `paramiko-expect <https://github.com/fgimian/paramiko-expect>`_ to
    maintain a persistent interactive shell session across multiple ``exec``
    calls (so state such as environment variables and working directory is
    preserved).

    Authentication is performed with a private key file (PEM format).

    Can be used as a context manager to ensure the SSH session is closed
    automatically::

        with ServerConnection(host, user, key_path) as server:
            server.exec("sudo systemctl restart myapp")

    Attributes:
        ssh: The underlying ``paramiko.SSHClient`` instance.
        interact: The ``SSHClientInteraction`` shell session, or ``None`` if
            not yet initialised.
    """

    def __init__(self, host: str, username: str, key_file_path: str) -> None:
        """Open an SSH connection to *host*.

        Args:
            host: Hostname or IP address of the remote server.
            username: SSH login username.
            key_file_path: Path to the private key file (PEM format) used for
                authentication.
        """
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(host, username=username, key_filename=key_file_path)
        self.interact = None

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def __enter__(self) -> "ServerConnection":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close_shell()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _init_shell(self) -> None:
        if self.interact is None:
            self.interact = SSHClientInteraction(self.ssh, timeout=300, display=False)
            self.interact.expect(r'.+[#$>] ?$')

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def exec(self, exec_str: str) -> None:
        """Run one or more commands on the remote server.

        Commands in *exec_str* are split by newline and executed sequentially
        inside a single persistent interactive SSH shell.  Each command is
        printed with a ``>`` prefix, and the server's output is printed to the
        console after the shell prompt reappears.

        Args:
            exec_str: One or more shell commands separated by newlines.
                Leading and trailing whitespace on each line is stripped; blank
                lines are ignored.

        Example::

            server.exec(\"\"\"
                cd /opt/app/backend
                sudo .venv/bin/pip install -r requirements.txt
            \"\"\")
        """
        lines = [line.strip() for line in exec_str.strip().split('\n')]
        lines = [line for line in lines if line]

        if not lines:
            return

        self._init_shell()

        for cmd in lines:
            print(">", cmd)
            self.interact.send(cmd)
            self.interact.expect(r'.+[#$>] ?$')
            output = self.interact.current_output_clean

            out_lines = output.splitlines()
            if out_lines and cmd in out_lines[0]:
                out_lines = out_lines[1:]

            filtered = '\n'.join(out_lines).strip()
            if filtered:
                print(filtered.encode(sys.stdout.encoding or 'utf-8', errors='replace')
                             .decode(sys.stdout.encoding or 'utf-8'))

    def scp(self, local_path: str, remote_path: str) -> None:
        """Copy a file or directory from the local machine to the remote server.

        Uses the SCP protocol (via the ``scp`` library backed by the existing
        paramiko transport).  Directory copies are recursive.

        Args:
            local_path: Path to the local file or directory to copy.
            remote_path: Destination path on the remote server.  The parent
                directory must already exist.

        Example::

            server.scp("./dist", "/opt/app")
        """
        print(Fore.YELLOW + f"Copying `{local_path}` → `{remote_path}` on remote" + Style.RESET_ALL)
        with SCPClient(self.ssh.get_transport()) as scp:
            scp.put(local_path, remote_path, recursive=True)

    def close_shell(self) -> None:
        """Close the interactive SSH shell session.

        If no shell session has been opened this is a no-op.  Errors during
        closure are silently ignored so that cleanup always succeeds.  After
        this call, ``interact`` is set to ``None``; a subsequent call to
        ``exec`` will open a new session.
        """
        if self.interact:
            try:
                self.interact.close()
            except Exception:
                pass
            self.interact = None
