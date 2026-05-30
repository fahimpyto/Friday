from rich.console import Console
from rich.prompt import Confirm, Prompt

console = Console()


def require_approval(tool_name: str, arguments: dict, safety_level: str) -> bool:
    if safety_level == "safe":
        return True

    tool_label = f"[bold yellow]{tool_name}[/]"
    args_str = ", ".join(f"{k}={v}" for k, v in arguments.items())

    if safety_level == "confirm":
        return Confirm.ask(
            f"{tool_label} with args ({args_str}) — approve?",
            default=True,
        )

    if safety_level == "dangerous":
        console.print(f"\n[bold red]⚠ DANGEROUS OPERATION[/]")
        console.print(f"  Tool: {tool_label}")
        console.print(f"  Args: {args_str}")
        result = Prompt.ask(
            f'  [red]Type [bold]yes[/] to confirm, or anything else to deny[/]',
        )
        return result.strip().lower() == "yes"

    return True
