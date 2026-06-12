import json
import os
from pathlib import Path


def _get_config_path() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "config" / "models.json"


def _load() -> dict:
    path = _get_config_path()
    if not path.exists():
        return {"default": "openai/gpt-4o", "models": []}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _save(data: dict):
    path = _get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_default() -> str:
    data = _load()
    saved = data.get("default")
    if saved:
        return saved
    env_model = os.getenv("OPENROUTER_MODEL")
    if env_model:
        return env_model
    return "openai/gpt-4o"


def set_default(model_id: str):
    data = _load()
    data["default"] = model_id
    _save(data)


def list_models() -> list[dict]:
    data = _load()
    return data.get("models", [])


def get_model(index: int) -> dict | None:
    models = list_models()
    if 0 <= index < len(models):
        return models[index]
    return None


def get_model_by_id(model_id: str) -> dict | None:
    models = list_models()
    for m in models:
        if m["id"] == model_id:
            return m
    return None


def get_model_ids() -> list[str]:
    return [m["id"] for m in list_models()]


def _infer_name(model_id: str) -> str:
    raw = model_id.split("/")[-1]
    raw = raw.replace(":free", "").replace(":paid", "")
    return raw.replace("-", " ").replace("_", " ").title()


def _infer_provider(model_id: str) -> str:
    parts = model_id.split("/")
    return parts[0].title() if len(parts) > 1 else "Unknown"


def add_model(model_id: str) -> dict:
    data = _load()
    existing = get_model_by_id(model_id)
    if existing:
        return existing
    entry = {
        "id": model_id,
        "name": _infer_name(model_id),
        "provider": _infer_provider(model_id),
        "type": "free",
    }
    data["models"].append(entry)
    _save(data)
    return entry


def remove_model(model_id: str) -> bool:
    data = _load()
    models = data.get("models", [])
    before = len(models)
    data["models"] = [m for m in models if m["id"] != model_id]
    if len(data["models"]) == before:
        return False
    if data.get("default") == model_id:
        if data["models"]:
            data["default"] = data["models"][0]["id"]
        else:
            data["default"] = "openai/gpt-4o"
    _save(data)
    return True
