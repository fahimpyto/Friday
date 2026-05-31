import json
from datetime import datetime
from pathlib import Path

SESSIONS_DIR = Path("sessions")


def _ensure_dir():
    SESSIONS_DIR.mkdir(exist_ok=True)


def generate_id() -> str:
    return datetime.now().strftime("session_%Y%m%d_%H%M%S")


def save_messages(messages: list, session_id: str):
    _ensure_dir()
    path = SESSIONS_DIR / f"{session_id}.jsonl"
    with open(path, "a", encoding="utf-8") as f:
        for msg in messages:
            serializable = _make_serializable(msg)
            f.write(json.dumps(serializable, ensure_ascii=False) + "\n")


def load_messages(session_id: str) -> list:
    path = SESSIONS_DIR / f"{session_id}.jsonl"
    if not path.exists():
        return []
    messages = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                messages.append(json.loads(line))
    return messages


def list_sessions() -> list[dict]:
    _ensure_dir()
    sessions = []
    for path in sorted(SESSIONS_DIR.glob("*.jsonl"), reverse=True):
        stats = path.stat()
        sessions.append({
            "id": path.stem,
            "size": stats.st_size,
            "modified": datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M"),
        })
    return sessions


def delete_session(session_id: str):
    path = SESSIONS_DIR / f"{session_id}.jsonl"
    if path.exists():
        path.unlink()


def _make_serializable(msg) -> dict:
    # Handle OpenAI ChatCompletionMessage objects manually
    if hasattr(msg, "role"):
        result = {"role": msg.role, "content": msg.content}
        if getattr(msg, "tool_calls", None):
            result["tool_calls"] = [_tc_serializable(tc) for tc in msg.tool_calls]
        return result
    # Fallback for pydantic models
    if hasattr(msg, "model_dump"):
        return msg.model_dump()
    if hasattr(msg, "to_dict"):
        return msg.to_dict()
    if isinstance(msg, dict):
        result = {}
        for k, v in msg.items():
            if k == "tool_calls" and isinstance(v, list):
                result[k] = [_tc_serializable(tc) for tc in v]
            else:
                result[k] = v
        return result
    return {"content": str(msg)}


def _tc_serializable(tc) -> dict:
    if isinstance(tc, dict):
        return tc
    return {
        "id": tc.id,
        "type": tc.type,
        "function": {
            "name": tc.function.name,
            "arguments": tc.function.arguments,
        },
    }
