import subprocess
import sys

from src.tools.registry import tool


@tool
def execute_command(command: str, timeout: int = 30) -> str:
    """Execute a shell command and return its output.
    :param command: Command to execute
    :param timeout: Maximum time in seconds before the command is killed
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            if output:
                output += "\n--- stderr ---\n"
            output += result.stderr
        if result.returncode != 0:
            output += f"\n(exit code: {result.returncode})"
        return output or "(no output)"
    except subprocess.TimeoutExpired:
        return f"Command timed out after {timeout}s: {command}"
    except Exception as e:
        return f"Error executing command: {e}"
