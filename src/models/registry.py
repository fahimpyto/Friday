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
    default_id = data.get("default", "openai/gpt-4o")
    env_model = os.getenv("OPENROUTER_MODEL")
    if env_model:
        return env_model
    return default_id


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
