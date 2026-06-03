# Friday v0.1 — AI Agent

An AI agent with system control, web browsing, PDF reading (with OCR), and OpenRouter model support. Built with a ReAct (Reasoning + Acting) loop pattern.

## Features

- **ReAct Agent** — thinks, uses tools, observes results, and responds
- **300+ LLM Models** — via OpenRouter (GPT-4o, Claude, Gemini, Llama, DeepSeek, etc.)
- **12+ Built-in Tools** — file operations, shell commands, web search, PDF reading
- **PDF OCR** — reads text PDFs and scanned/image-based PDFs via OCR fallback
- **Rich CLI** — markdown rendering, streaming output, cost tracking
- **Session Management** — save/load conversations, context compaction
- **Multi-line Input** — use `\` at end of line for multi-line prompts
- **Safety Gates** — dangerous commands require explicit approval

## Prerequisites

- **Python 3.10+**
- **Tesseract OCR** (optional, for scanned PDFs only)
  - Windows: Download from [UB-Mannheim Tesseract wiki](https://github.com/UB-Mannheim/tesseract/wiki)
  - macOS: `brew install tesseract`
  - Linux: `sudo apt install tesseract-ocr`
- **OpenRouter API key** — get one at [openrouter.ai/keys](https://openrouter.ai/keys)

## Quick Start

### Windows (auto-setup)

```powershell
# Run the setup script (creates venv, installs deps, sets up .env)
.\setup.ps1

# Activate the environment
.\venv\Scripts\Activate

# Edit .env with your OpenRouter API key, then run:
python -m src.main
```

### Manual setup (any OS)

```bash
# Create virtual environment
python -m venv venv

# Activate it
# Windows:
venv\Scripts\Activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env from example
cp .env.example .env
# Edit .env and add your OPENROUTER_API_KEY

# Run the agent
python -m src.main
```

## Configuration

Edit `.env` in the project root:

```env
# Required: OpenRouter API key
OPENROUTER_API_KEY=sk-or-v1-...

# Optional: Default model (defaults to openai/gpt-4o)
OPENROUTER_MODEL=openai/gpt-4o

# Optional: Tavily API key for enhanced web search
TAVILY_API_KEY=tvly-...
```

## Usage

Once running, you'll see an interactive prompt. Type your requests and the agent will use tools as needed.

```
┌─────────────────────────────────────────────────────────┐
│ Friday v0.1  |  Model: openai/gpt-4o  |  Tools: 12    │
│ /new  /model  /cost  /sessions  /load  /help  |  exit  │
└─────────────────────────────────────────────────────────┘
You: what files are in the current directory?
```

### Commands

| Command | Description |
|---------|-------------|
| `/new` | Start a new session |
| `/model <name>` | Switch model (e.g., `/model anthropic/claude-sonnet-4`) |
| `/cost` | Show token usage and cost |
| `/sessions` | List all saved sessions |
| `/load <id>` | Load a saved session |
| `/help` | Show command reference |
| `exit` / `quit` | Exit the agent |
| `\` (trailing backslash) | Continue input on next line |

### Popular Models

- `openai/gpt-4o` / `openai/gpt-4o-mini`
- `anthropic/claude-sonnet-4` / `anthropic/claude-3.5-haiku`
- `google/gemini-2.0-flash`
- `meta-llama/llama-4`
- `deepseek/deepseek-chat`
- `qwen/qwen-max`
- `mistralai/mistral-large`

## Tools

| Tool | Description | Safety |
|------|-------------|--------|
| `read_file` | Read file with offset/limit | Safe |
| `write_file` | Create or overwrite file | ⚠️ Confirm |
| `edit_file` | Search-and-replace text in file | ⚠️ Confirm |
| `list_directory` | List directory contents | Safe |
| `glob_files` | Find files by glob pattern | Safe |
| `grep_content` | Regex search in file contents | Safe |
| `execute_command` | Run shell command with timeout | 🔴 Explicit |
| `web_search` | Search via DuckDuckGo or Tavily | Safe |
| `web_fetch` | Fetch URL and extract text | Safe |
| `read_pdf` | Extract text from PDF (with OCR fallback) | Safe |
| `system_info` | Get OS / CPU / RAM / disk info | Safe |
| `get_datetime` | Current date and time | Safe |

**Safety levels:**
- **Safe** — executes immediately
- **⚠️ Confirm** — asks `y/N` before executing
- **🔴 Explicit** — shows full command, requires typing `yes`

## Project Structure

```
friday-v-0.1/
├── .env                    # Your API keys (not in git)
├── .env.example            # Template for .env
├── requirements.txt        # Python dependencies
├── setup.ps1               # Windows setup script
├── README.md               # This file
├── PLAN.md                 # Architecture plan
└── src/
    ├── main.py             # Entry point — rich REPL loop
    ├── agent/
    │   ├── core.py         # ReAct loop
    │   └── prompt.py       # System prompt
    ├── llm/
    │   └── client.py       # OpenRouter wrapper
    ├── tools/
    │   ├── registry.py     # @tool decorator
    │   ├── filesystem.py   # File operations
    │   ├── shell.py        # Shell commands
    │   ├── web.py          # Web search & fetch
    │   ├── pdf.py          # PDF reader (text + OCR)
    │   └── system.py       # System info
    └── safety/
        └── permissions.py  # Approval prompts
```

## OCR for PDFs

The PDF reader has two modes:

1. **Text extraction** (PyMuPDF) — fast, works for PDFs with selectable text
2. **OCR fallback** (pdf2image + Tesseract) — activated when no text is found

If you encounter OCR issues:

```bash
# Windows: make sure Tesseract is in your PATH, or install via Chocolatey
choco install tesseract

# Verify installation
tesseract --version
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'src'` | Run `python -m src.main` instead of `python src\main.py` |
| `OPENROUTER_API_KEY not set` | Copy `.env.example` to `.env` and add your key |
| `Tesseract not found` | Install Tesseract OCR (see OCR section above) |
| Rich rendering issues | Use Windows Terminal (not cmd.exe) for best experience |
