import json

from src.llm.client import LLMClient
from src.tools.registry import get_tool_schemas, get_tool_safety, execute_tool
from src.safety.permissions import require_approval


class ReActAgent:
    def __init__(self, llm_client: LLMClient, system_prompt: str, max_iterations: int = 20):
        self.llm = llm_client
        self.system_prompt = system_prompt
        self.max_iterations = max_iterations
        self.messages: list = []
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost = 0.0
        self._on_tool_call = None

    def set_on_tool_call(self, callback):
        self._on_tool_call = callback

    def run(self, user_input: str) -> str:
        if not self.messages:
            self.messages.append({"role": "system", "content": self.system_prompt})

        self.messages.append({"role": "user", "content": user_input})

        for _ in range(self.max_iterations):
            response = self.llm.chat(self.messages, tools=get_tool_schemas(), stream=False)
            self.messages.append(response)

            if response.usage:
                self.total_input_tokens += response.usage.prompt_tokens or 0
                self.total_output_tokens += response.usage.completion_tokens or 0

            if response.tool_calls:
                for tool_call in response.tool_calls:
                    name = tool_call.function.name
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        arguments = {}

                    safety = get_tool_safety(name)
                    if self._on_tool_call:
                        self._on_tool_call(name, arguments, safety)

                    approved = require_approval(name, arguments, safety)
                    if not approved:
                        self.messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": "Operation cancelled by user.",
                        })
                        continue

                    result = execute_tool(name, arguments)
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    })
            else:
                return response.content or ""

        return "I've reached the maximum number of iterations. Please refine your request."

    def get_cost_summary(self) -> str:
        return (
            f"Input tokens: {self.total_input_tokens}  |  "
            f"Output tokens: {self.total_output_tokens}  |  "
            f"Total: {self.total_input_tokens + self.total_output_tokens}"
        )

    def reset(self):
        self.messages = []
        self.total_input_tokens = 0
        self.total_output_tokens = 0
