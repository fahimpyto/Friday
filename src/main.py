import sys
from pathlib import Path
import os
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from src.llm.client import LLMClient
from src.agent.core import ReActAgent
from src.agent.prompt import SYSTEM_PROMPT
from src.agent import session as session_mgr
from src.tools.registry import get_tool_schemas
from src.models.registry import list_models, get_model, get_model_by_id, remove_model, set_default, get_default, add_model

import src.tools

load_dotenv()
console = Console()


def get_multiline_input() -> str:
    lines = []
    while True:
        try:
            line = input()
        except (EOFError, KeyboardInterrupt):
            break
        if line.endswith("\\"):
            lines.append(line[:-1])
        else:
            lines.append(line)
            break
    return "".join(lines)


def run_setup(auto_install: bool = False):
    """Check and optionally install missing dependencies."""
    from src.tools.dependencies import ensure_all

    console.print("[bold cyan]Checking system dependencies...[/]")
    missing = ensure_all(verbose=True, auto_install=auto_install)

    if not missing:
        console.print("[bold green]All dependencies satisfied![/]")
    else:
        console.print(f"[bold yellow]Still missing: {', '.join(missing)}[/]")
        console.print("[yellow]Run again with --setup --auto for unattended install[/]")


def main():
    # Handle CLI flags
    if "--setup" in sys.argv:
        auto = "--auto" in sys.argv
        run_setup(auto_install=auto)
        if not auto:
            return

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        console.print("[red]Error: OPENROUTER_API_KEY not set. Create a .env file based on .env.example[/]")
        return

    model = get_default()

    llm = LLMClient(api_key=api_key, model=model)
    agent = ReActAgent(llm_client=llm, system_prompt=SYSTEM_PROMPT)

    tool_count = len(get_tool_schemas())
    console.print(Panel(
        f"[bold cyan]Friday v0.1[/]  |  Model: [green]{model}[/]  |  Tools: {tool_count}\n"
        f"[dim]/new  /model  /cost  /sessions  /load  /help  /setup  |  exit  |  use \\ for multi-line[/]",
        title="Agent",
    ))

    def on_tool_call(name, arguments, safety):
        args_str = ", ".join(f"{k}={v}" for k, v in arguments.items())
        label = f"[yellow]🔧 {name}({args_str})[/]"
        if safety == "confirm":
            label += " [dim](needs approval)[/]"
        elif safety == "dangerous":
            label += " [bold red](⚠ needs explicit approval)[/]"
        console.print(label)

    agent.set_on_tool_call(on_tool_call)

    while True:
        try:
            console.print("[bold cyan]You:[/] ", end="")
            user_input = get_multiline_input().strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit"):
            break

        if user_input.startswith("/"):
            handle_command(user_input, agent, llm)
            continue

        with console.status("[bold green]Friday is thinking...", spinner="dots"):
            response = agent.run(user_input)

        console.print(f"\n[bold green]Friday:[/]")
        console.print(Markdown(response))

    cost = agent.get_cost_summary()
    console.print(f"\n[dim]Session ended. {cost}[/]")


def handle_command(cmd: str, agent: ReActAgent, llm: LLMClient):
    parts = cmd.split(maxsplit=1)
    command = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    if command == "/new":
        agent.reset()
        console.print(f"[yellow]New session: {agent.session_id}[/]")
    elif command == "/model":
        if args:
            parts = args.split(maxsplit=1)
            sub = parts[0].lower()
            rest = parts[1] if len(parts) > 1 else ""

            if sub == "delete" and rest:
                target_id = None
                target_name = None
                if rest.isdigit():
                    idx = int(rest) - 1
                    m = get_model(idx)
                    if m:
                        target_id = m["id"]
                        target_name = m["name"]
                    else:
                        console.print(f"[red]Invalid model number: {rest}[/]")
                else:
                    target_id = rest
                    m = get_model_by_id(rest)
                    target_name = m["name"] if m else rest

                if target_id:
                    changed = llm.model == target_id
                    if remove_model(target_id):
                        console.print(f"[green]✓ Removed:[/] {target_name}")
                        if changed:
                            fallback_id = get_default()
                            llm.set_model(fallback_id)
                            console.print(f"[yellow]Switched to default:[/] {fallback_id}")
                    else:
                        console.print(f"[red]Not found:[/] {target_name}")
            else:
                selected = None
                if args.isdigit():
                    idx = int(args) - 1
                    m = get_model(idx)
                    if m:
                        selected = m["id"]
                    else:
                        console.print(f"[red]Invalid model number: {args}[/]")
                else:
                    m = get_model_by_id(args)
                    if m:
                        selected = m["id"]
                    else:
                        entry = add_model(args)
                        selected = entry["id"]
                        console.print(f"[green]✓ Added:[/] {entry['name']} [dim]({entry['id']})[/]")

                if selected:
                    llm.set_model(selected)
                    set_default(selected)
                    console.print(f"[green]✓ Switched to:[/] {selected} [dim](saved as default)[/]")
        else:
            models = list_models()
            if not models:
                console.print("[yellow]No models yet. Use /model <id> to add one.[/]")
                console.print(f"[dim]Current: [green]{llm.model}[/][/]")
            else:
                table = Table(title=f"Models  |  Current: [green]{llm.model}[/]")
                table.add_column("#", style="cyan", no_wrap=True)
                table.add_column("Model", style="white")
                table.add_column("ID", style="dim")
                table.add_column("Provider", style="blue")
                table.add_column("Type", style="yellow")

                for i, m in enumerate(models, 1):
                    marker = " ◀" if m["id"] == llm.model else ""
                    type_tag = "[bold green]FREE[/]" if m["type"] == "free" else "[bold red]PAID[/]"
                    table.add_row(
                        str(i),
                        f"{m['name']}{marker}",
                        m["id"],
                        m["provider"],
                        type_tag,
                    )
                console.print(table)
            console.print("[dim]Use /model <number> to switch, /model <id>, or /model delete <number|id>[/]")
    elif command == "/cost":
        console.print(f"[dim]{agent.get_cost_summary()}[/]")
    elif command == "/sessions":
        sessions = session_mgr.list_sessions()
        if not sessions:
            console.print("[yellow]No saved sessions.[/]")
        else:
            table = Table(title="Sessions")
            table.add_column("ID", style="cyan")
            table.add_column("Messages", style="white")
            table.add_column("Date", style="dim")
            for s in sessions:
                msgs = session_mgr.load_messages(s["id"])
                table.add_row(s["id"], str(len(msgs)), s["modified"])
            console.print(table)
    elif command == "/load":
        if not args:
            console.print("[red]Usage: /load <session_id>[/]")
        else:
            ok = agent.load_session(args)
            if ok:
                console.print(f"[green]Loaded session: {args}[/]")
            else:
                console.print(f"[red]Session not found: {args}[/]")
    elif command == "/setup":
        auto = args.strip().lower() == "--auto"
        run_setup(auto_install=auto)
    elif command == "/help":
        table = Table(title="Commands")
        table.add_column("Command", style="cyan")
        table.add_column("Description", style="white")
        table.add_row("/new", "Start a new session")
        table.add_row("/model <name>", "Switch model")
        table.add_row("/cost", "Show token usage")
        table.add_row("/sessions", "List saved sessions")
        table.add_row("/load <id>", "Load a saved session")
        table.add_row("/setup [--auto]", "Check/install missing dependencies")
        table.add_row("/help", "Show this help")
        table.add_row("exit", "Quit")
        table.add_row("\\", "Line continuation for multi-line input")
        console.print(table)
    else:
        console.print(f"[red]Unknown command: {command}[/]")


if __name__ == "__main__":
    main()
