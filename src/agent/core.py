import json

from src.llm.client import LLMClient
from src.tools.registry import get_tool_schemas, get_tool_safety, execute_tool
from src.safety.permissions import require_approval
from src.agent import session


class ReActAgent:
    def __init__(self, llm_client: LLMClient, system_prompt: str, max_iterations: int = 20):
        self.llm = llm_client
        self.system_prompt = system_prompt
        self.max_iterations = max_iterations
        self.messages: list = []
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self._on_tool_call = None
        self.session_id = session.generate_id()
        self.compact_threshold = 30
        self.compact_target = 15
        self._pending_save = []

    def set_on_tool_call(self, callback):
        self._on_tool_call = callback

    def run(self, user_input: str) -> str:
        if not self.messages:
            self.messages.append({"role": "system", "content": self.system_prompt})

        self.messages.append({"role": "user", "content": user_input})
        self._flush_pending()

        self._maybe_compact()

        for _ in range(self.max_iterations):
            response = self.llm.chat(self.messages, tools=get_tool_schemas(), stream=False)
            self.messages.append(response)
            self._defer_save(response)

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
                        cancel_msg = {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": "Operation cancelled by user.",
                        }
                        self.messages.append(cancel_msg)
                        self._defer_save(cancel_msg)
                        continue

                    result = execute_tool(name, arguments)
                    tool_msg = {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    }
                    self.messages.append(tool_msg)
                    self._defer_save(tool_msg)
            else:
                self._flush_pending()
                return response.content or ""

        return "I've reached the maximum number of iterations. Please refine your request."

    def _maybe_compact(self):
        non_system = [m for m in self.messages if m.get("role") != "system"]
        if len(non_system) <= self.compact_threshold:
            return

        keep = self.messages[:1]
        to_compact = self.messages[1:]
        cutoff = max(len(to_compact) - self.compact_target, 1)
        old_part = to_compact[:cutoff]
        recent_part = to_compact[cutoff:]

        summary = self._summarize(old_part)
        keep.append({"role": "system", "content": f"[Summary of earlier conversation]\n{summary}"})
        keep.extend(recent_part)
        self.messages = keep

    def _summarize(self, msgs: list) -> str:
        text = ""
        for m in msgs:
            role = m.get("role", "unknown")
            content = str(m.get("content", ""))[:300]
            if content:
                text += f"{role}: {content}\n"

        prompt = (
            "Summarize the following conversation concisely. "
            "Keep key facts, decisions, and the user's intent:\n\n" + text
        )
        try:
            resp = self.llm.chat(
                [{"role": "user", "content": prompt}],
                tools=None,
                stream=False,
            )
            return resp.content or "(summary unavailable)"
        except Exception:
            return "(summary unavailable)"

    def _defer_save(self, msg):
        self._pending_save.append(msg)

    def _flush_pending(self):
        if self._pending_save:
            session.save_messages(self._pending_save, self.session_id)
            self._pending_save = []

    def load_session(self, session_id: str) -> bool:
        msgs = session.load_messages(session_id)
        if not msgs:
            return False
        self.messages = msgs
        self.session_id = session_id
        return True

    def get_cost_summary(self) -> str:
        return (
            f"Input tokens: {self.total_input_tokens}  |  "
            f"Output tokens: {self.total_output_tokens}  |  "
            f"Total: {self.total_input_tokens + self.total_output_tokens}"
        )

    def reset(self):
        self._flush_pending()
        self.messages = []
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.session_id = session.generate_id()
