import json

from src.llm.client import LLMClient
from src.tools.registry import get_tool_schemas, execute_tool


class ReActAgent:
    def __init__(self, llm_client: LLMClient, system_prompt: str, max_iterations: int = 20):
        self.llm = llm_client
        self.system_prompt = system_prompt
        self.max_iterations = max_iterations
        self.messages: list = []

    def run(self, user_input: str) -> str:
        if not self.messages:
            self.messages.append({"role": "system", "content": self.system_prompt})

        self.messages.append({"role": "user", "content": user_input})

        for _ in range(self.max_iterations):
            response = self.llm.chat(self.messages, tools=get_tool_schemas(), stream=False)
            self.messages.append(response)

            if response.tool_calls:
                for tool_call in response.tool_calls:
                    name = tool_call.function.name
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        arguments = {}

                    result = execute_tool(name, arguments)
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    })
            else:
                return response.content or ""

        return "I've reached the maximum number of iterations. Please refine your request."

    def reset(self):
        self.messages = []
