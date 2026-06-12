from openai import OpenAI

from src.models.registry import get_model_ids


class LLMClient:
    def __init__(self, api_key: str, model: str = "openai/gpt-4o", base_url: str = "https://openrouter.ai/api/v1"):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def set_model(self, model: str):
        self.model = model

    def chat(self, messages: list, tools: list | None = None, stream: bool = False):
        kwargs = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
        }
        if tools:
            kwargs["tools"] = tools

        response = self.client.chat.completions.create(**kwargs)

        if stream:
            return response

        message = response.choices[0].message
        message.usage = getattr(response, "usage", None)
        return message

    def available_models(self):
        return get_model_ids()
