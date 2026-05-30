import inspect
import re
from typing import get_type_hints

tools_registry: dict[str, dict] = {}

TYPE_MAP = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
}


def generate_schema(func):
    sig = inspect.signature(func)
    hints = get_type_hints(func)
    doc = inspect.getdoc(func) or ""

    lines = doc.strip().split("\n")
    description = lines[0].strip() if lines else ""

    param_docs = {}
    for line in lines:
        match = re.match(r":param\s+(\w+)\s*:\s*(.+)", line.strip())
        if match:
            param_docs[match.group(1)] = match.group(2)

    properties = {}
    required = []

    for name, param in sig.parameters.items():
        if name == "return":
            continue

        param_type = hints.get(name, str)
        json_type = TYPE_MAP.get(param_type, "string")

        prop: dict = {"type": json_type}
        if name in param_docs:
            prop["description"] = param_docs[name]

        if param.default is inspect.Parameter.empty:
            required.append(name)
        else:
            existing = prop.get("description", "")
            suffix = f"(default: {param.default})"
            prop["description"] = f"{existing} {suffix}".strip()

        properties[name] = prop

    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


def tool(func=None, *, safety: str = "safe"):
    if func is None:
        return lambda f: tool(f, safety=safety)

    tools_registry[func.__name__] = {
        "func": func,
        "schema": generate_schema(func),
        "safety": safety,
    }
    return func


def get_tool_schemas() -> list:
    return [entry["schema"] for entry in tools_registry.values()]


def get_tool_safety(name: str) -> str:
    entry = tools_registry.get(name)
    return entry.get("safety", "safe") if entry else "safe"


def execute_tool(name: str, arguments: dict) -> str:
    entry = tools_registry.get(name)
    if not entry:
        return f"Error: unknown tool '{name}'"
    try:
        result = entry["func"](**arguments)
        return str(result) if result is not None else ""
    except Exception as e:
        return f"Error executing {name}: {e}"
