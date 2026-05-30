# Friday v0.1 — AI Agent Plan

> An AI agent with system control, internet browsing, PDF reading, and OpenRouter model support.

## Architecture

**Language:** Python 3.10+  
**Pattern:** ReAct (Reasoning + Acting) — tool-calling loop  
**LLM Provider:** OpenRouter (300+ models)  
**UI:** Rich CLI (markdown rendering, streaming, spinners)  
**Web Search:** DuckDuckGo (free, default) + Tavily (optional config)

---

## Project Structure

```
friday-v-0.1/
│
├── .env.example              # Environment variables template
├── .gitignore
├── requirements.txt           # Python dependencies
├── PLAN.md                    # This file
│
└── src/
    ├── __init__.py
    ├── main.py                # Entry point — rich REPL loop
    │
    ├── agent/
    │   ├── __init__.py
    │   ├── core.py            # ReAct loop (think → act → observe → repeat)
    │   └── prompt.py          # System prompt with tool definitions
    │
    ├── llm/
    │   ├── __init__.py
    │   └── client.py          # OpenRouter wrapper (streaming, model switch)
    │
    ├── tools/
    │   ├── __init__.py        # Auto-import all tools
    │   ├── registry.py        # @tool decorator → JSON schema from type hints
    │   ├── filesystem.py      # read, write, edit, list_dir, glob, grep
    │   ├── shell.py           # execute_command (timeout + approval gate)
    │   ├── web.py             # web_search (duckduckgo/tavily) + web_fetch
    │   ├── pdf.py             # read_pdf (PyMuPDF text extraction)
    │   └── system.py          # system_info, get_datetime
    │
    └── safety/
        ├── __init__.py
        └── permissions.py     # Approval prompts for dangerous operations
```

---

## Core Concepts

### ReAct Agent Loop

```
User Input
    ↓
Append to conversation history
    ↓
LLM (OpenRouter) responds with:
  ├── Tool call (name + args) → Execute tool → Append result → Loop
  └── Text response           → Show user → Wait for next input
    ↓
Guard: max 20 iterations | cost limit | user interrupt
```

- Uses OpenAI-compatible **function calling** (native to OpenRouter)
- Each tool has a JSON schema auto-generated from its Python signature
- Streams tokens to CLI as they arrive

### Tool Schema Generation

The `@tool` decorator in `registry.py` reads:
1. **Function name** → tool name
2. **Type hints** → parameter types
3. **Docstring** → description (first line = tool description, `:param name:` → parameter description)

```python
@tool
def read_file(path: str, offset: int = 0, limit: int = 2000) -> str:
    """Read contents of a file.
    :param path: Absolute path to the file
    :param offset: Line number to start from (0-indexed)
    :param limit: Max lines to read
    """
```

→ Auto-generates JSON schema for OpenRouter function calling.

---

## Tools

| Tool | File | Description | Safety |
|------|------|-------------|--------|
| `read_file` | filesystem.py | Read file with offset/limit | Safe |
| `write_file` | filesystem.py | Create/overwrite file | ⚠️ Confirm |
| `edit_file` | filesystem.py | Search-and-replace with diff | ⚠️ Confirm |
| `list_directory` | filesystem.py | List entries in a directory | Safe |
| `glob_files` | filesystem.py | Find files by glob pattern | Safe |
| `grep_content` | filesystem.py | Regex search in file contents | Safe |
| `execute_command` | shell.py | Run shell command with timeout | 🔴 Confirm |
| `web_search` | web.py | Search web via DuckDuckGo or Tavily | Safe |
| `web_fetch` | web.py | Fetch URL and extract clean text | Safe |
| `read_pdf` | pdf.py | Extract text from PDF | Safe |
| `system_info` | system.py | Get OS / CPU / RAM / disk info | Safe |
| `get_datetime` | system.py | Current date and time | Safe |

**Safety levels:**
- **Safe** — executes immediately
- **⚠️ Confirm** — asks user `y/N` before executing
- **🔴 Confirm** — shows full command, requires explicit `yes`

---

## Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| `openrouter` | ≥0.9.0 | OpenRouter Python SDK |
| `PyMuPDF` | ≥1.24.0 | PDF text extraction |
| `httpx` | ≥0.28.0 | Async HTTP client |
| `beautifulsoup4` | ≥4.12.0 | HTML parsing |
| `lxml` | ≥5.0.0 | HTML parser backend |
| `duckduckgo_search` | ≥7.0.0 | Free web search |
| `tavily-python` | ≥0.5.0 | Optional agent search |
| `rich` | ≥13.0.0 | Terminal UI |
| `python-dotenv` | ≥1.0.0 | .env loading |

---

## Implementation Phases

### Phase 1 — Foundation Engine ✅
- [x] `src/llm/client.py` — OpenRouter chat with streaming + model switching
- [x] `src/tools/registry.py` — `@tool` decorator + JSON schema generation
- [x] `src/agent/prompt.py` — System prompt with tool instructions
- [x] `src/agent/core.py` — ReAct loop (parse tool calls, execute, append observations)
- [x] `src/main.py` — Basic CLI: input → stream → output (no rich yet)
- [x] `requirements.txt` + `.env.example` + `.gitignore`

### Phase 2 — All Tools ✅
- [x] `src/tools/filesystem.py` — read, write, edit, list_dir, glob, grep
- [x] `src/tools/shell.py` — execute_command with timeout
- [x] `src/tools/web.py` — web_search (duckduckgo + tavily) + web_fetch
- [x] `src/tools/pdf.py` — read_pdf via PyMuPDF
- [x] `src/tools/system.py` — system_info, get_datetime
- [x] `src/tools/__init__.py` — auto-import and register all tools
- [x] Integrate all tools into ReAct loop

### Phase 3 — Safety & Rich CLI ✅
- [x] `src/safety/permissions.py` — approval prompts for dangerous tools
- [x] Integration: wire permissions into ReAct loop before tool execution
- [x] Rich CLI: markdown rendering, streaming spinner, syntax highlighting
- [x] Cost tracking per session

### Phase 4 — Advanced Features ⏳
- [x] `/model` command — switch OpenRouter model mid-session
- [x] `/new` command — clear conversation history
- [ ] Session persistence — save/load JSONL conversation logs
- [ ] Context compaction — summarize old messages to save tokens
- [ ] Multi-line input mode

---

## OpenRouter Model Support

Any model on OpenRouter works. Set via `.env` or `/model` command:

```
OPENROUTER_API_KEY=sk-or-v1-...
OPENROUTER_MODEL=openai/gpt-4o           # Default model
```

Popular choices:
- `openai/gpt-4o` / `openai/gpt-4o-mini`
- `anthropic/claude-sonnet-4` / `anthropic/claude-3.5-haiku`
- `google/gemini-2.0-flash`
- `meta-llama/llama-4`
- `deepseek/deepseek-chat`
- `qwen/qwen-max`
- `mistralai/mistral-large`

---

## Key Design Decisions

1. **OpenAI function-calling format** — LLM sends structured JSON for tool calls, not free-form text parsing. More reliable.
2. **`@tool` decorator** — Keeps tool definitions clean. One decorator handles schema generation, registration, and safety metadata.
3. **No heavy agent frameworks** — Full control. Easy to debug, extend, and understand every line.
4. **Streaming first** — Tokens appear as the LLM generates them. Better UX.
5. **Safety by default** — Shell commands and file writes require confirmation. Configurable.
