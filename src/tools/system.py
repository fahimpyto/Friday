import os
import platform
import shutil
from datetime import datetime

from src.tools.registry import tool


@tool
def system_info() -> str:
    """Get information about the operating system, CPU, and available disk space."""
    info = [
        f"OS:          {platform.system()} {platform.release()}",
        f"Version:     {platform.version()}",
        f"Machine:     {platform.machine()}",
        f"Processor:   {platform.processor()}",
        f"Hostname:    {platform.node()}",
        f"Python:      {platform.python_version()}",
    ]

    if os.name == "nt":
        import ctypes
        kernel32 = ctypes.windll.kernel32
        cpu_count = os.cpu_count()
        info.append(f"CPU Cores:   {cpu_count}")
    else:
        info.append(f"CPU Cores:   {os.cpu_count()}")

    total, used, free = shutil.disk_usage(os.getcwd())
    info.append(f"Disk Free:   {free // (2**30)} GB / {total // (2**30)} GB")

    return "\n".join(info)


@tool
def get_datetime() -> str:
    """Get the current date and time."""
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S (%A)")
