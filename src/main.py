import os
from dotenv import load_dotenv

from src.llm.client import LLMClient
from src.agent.core import ReActAgent
from src.agent.prompt import SYSTEM_PROMPT
from src.tools.registry import get_tool_schemas

import src.tools  # registers all @tool decorated functions

load_dotenv()


def main():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not set. Create a .env file based on .env.example")
        return

    model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o")

    llm = LLMClient(api_key=api_key, model=model)
    agent = ReActAgent(llm_client=llm, system_prompt=SYSTEM_PROMPT)

    tool_count = len(get_tool_schemas())
    print(f"Friday v0.1 — Model: {model}  |  Tools: {tool_count}")
    print("Type 'exit' to quit, '/new' to reset, '/model <name>' to switch models")
    print("-" * 50)

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit"):
            break

        if user_input.startswith("/"):
            handle_command(user_input, agent, llm)
            continue

        response = agent.run(user_input)
        print(f"\nFriday: {response}")

    print("\nGoodbye!")


def handle_command(cmd: str, agent: ReActAgent, llm: LLMClient):
    parts = cmd.split(maxsplit=1)
    command = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    if command == "/new":
        agent.reset()
        print("Conversation reset.")
    elif command == "/model":
        if args:
            llm.set_model(args)
            print(f"Model switched to: {args}")
        else:
            print(f"Current model: {llm.model}")
    elif command == "/help":
        print("Commands:")
        print("  /new           Reset conversation")
        print("  /model <name>  Switch model (e.g. /model anthropic/claude-sonnet-4)")
        print("  /help          Show this help")
        print("  exit           Quit")
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
