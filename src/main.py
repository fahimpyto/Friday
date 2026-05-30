import os
from dotenv import load_dotenv
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.spinner import Spinner

from src.llm.client import LLMClient
from src.agent.core import ReActAgent
from src.agent.prompt import SYSTEM_PROMPT
from src.tools.registry import get_tool_schemas

import src.tools

load_dotenv()
console = Console()


def main():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        console.print("[red]Error: OPENROUTER_API_KEY not set. Create a .env file based on .env.example[/]")
        return

    model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o")

    llm = LLMClient(api_key=api_key, model=model)
    agent = ReActAgent(llm_client=llm, system_prompt=SYSTEM_PROMPT)

    tool_count = len(get_tool_schemas())
    console.print(Panel(
        f"[bold cyan]Friday v0.1[/]  |  Model: [green]{model}[/]  |  Tools: {tool_count}\n"
        f"[dim]/new  /model  /cost  /help  |  exit[/]",
        title="🤖 Agent",
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
            user_input = Prompt.ask("[bold cyan]You[/]")
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

        md = Markdown(response)
        console.print(Panel(md, title="[bold green]Friday[/]", border_style="green"))

    cost = agent.get_cost_summary()
    console.print(f"\n[dim]Session ended. {cost}[/]")


def handle_command(cmd: str, agent: ReActAgent, llm: LLMClient):
    parts = cmd.split(maxsplit=1)
    command = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    if command == "/new":
        agent.reset()
        console.print("[yellow]Conversation reset.[/]")
    elif command == "/model":
        if args:
            llm.set_model(args)
            console.print(f"[green]Model switched to:[/] {args}")
        else:
            console.print(f"Current model: [green]{llm.model}[/]")
            console.print("[dim]Available examples:[/]")
            for m in llm.available_models():
                console.print(f"  /model {m}")
    elif command == "/cost":
        console.print(f"[dim]{agent.get_cost_summary()}[/]")
    elif command == "/help":
        table = Table(title="Commands")
        table.add_column("Command", style="cyan")
        table.add_column("Description", style="white")
        table.add_row("/new", "Reset conversation")
        table.add_row("/model <name>", "Switch model")
        table.add_row("/cost", "Show token usage")
        table.add_row("/help", "Show this help")
        table.add_row("exit", "Quit")
        console.print(table)
    else:
        console.print(f"[red]Unknown command: {command}[/]")


if __name__ == "__main__":
    main()
