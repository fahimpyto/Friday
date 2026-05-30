from openai import OpenAI


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
        return [
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "anthropic/claude-sonnet-4",
            "anthropic/claude-3.5-haiku",
            "google/gemini-2.0-flash",
            "meta-llama/llama-4",
            "deepseek/deepseek-chat",
            "qwen/qwen-max",
            "mistralai/mistral-large",
        ]
