# GHOSTLINE 👻
### The Terminal That Remembers · v2.0

A local-first AI companion that lives in your terminal. Ask developer questions, explicitly run commands, and let an open-weight model explain the output. GHOSTLINE keeps its conversation memory on your machine and gives you control over what it executes.

**Built for Hacktoberfest 2026 — Week 4: Ghost in the Machine.**

## What makes it different?

GHOSTLINE is not an autonomous shell agent. It is intentionally user-controlled:
- Ordinary messages go to your local model; they never execute as shell commands.
- Commands run only after you type `:run <command>`.
- Potentially destructive commands trigger a confirmation prompt.
- Conversations and command-analysis context are stored locally in JSONL.
- Export a session to Markdown for debugging, sharing, or your project write-up.
- No hosted inference fallback, analytics, or telemetry.

## Features

| Feature | Description |
|---|---|
| Local inference | Ollama API, default model `qwen3:8b` |
| Terminal companion | Developer Q&A with a restrained haunted-terminal personality |
| Explicit command runner | Runs only commands entered with `:run` |
| Risk prompts | Confirmation for common destructive command patterns |
| Persistent memory | Local JSONL conversation history |
| Session export | Export current session to Markdown |
| Status check | Check whether Ollama and the selected model are available |
| Demo mode | Scripted walkthrough without Ollama or command execution |

## Quick start

Requirements: Python 3.10+ and [Ollama](https://ollama.com/).

```bash
# Download a local model (one-time setup)
ollama pull qwen3:8b

# Install from the repository root
python -m pip install .

# Start the application
ghostline
```

Try the demo first, with no model setup:

```bash
ghostline --demo
```

Or run it without installing the package:

```bash
python -m ghostline.cli --demo
python -m ghostline.cli
```

## Commands

```text
:help              Show commands
:run git status    Run this command and ask the local model to explain its output
:memory            Inspect recent entries from this session
:export            Save this session as ghostline-<session>.md
:export notes.md   Save this session to notes.md
:status            Check Ollama and selected model availability
:clear             Erase all local memory after confirmation
:quit              Exit
```

**Important:** `:run` executes with your current user's permissions. Review commands before running them. Confirmation patterns are a safety aid, not a sandbox or a complete security system.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `OLLAMA_HOST` | `http://localhost:11434` | Local Ollama endpoint |
| `GHOSTLINE_MODEL` | `qwen3:8b` | Installed Ollama model tag |
| `GHOSTLINE_HOME` | `~/.ghostline` | Local memory directory |
| `NO_COLOR` | unset | Disable ANSI colors |
| `GHOSTLINE_NO_ANIMATION` | unset | Disable typing effects |

PowerShell:

```powershell
$env:GHOSTLINE_MODEL = "qwen3:8b"
$env:OLLAMA_HOST = "http://localhost:11434"
ghostline
```

For lower-memory machines, pull a smaller model and set `GHOSTLINE_MODEL` to its exact Ollama tag.

## Architecture

```text
User
 |
 v
GHOSTLINE CLI (Python)
 |                  \
 |                   \--> Local JSONL memory + Markdown export
 v
Ollama API (localhost:11434)
 |
 v
Open-weight model (Qwen or another Ollama-compatible model)
```

GHOSTLINE only contacts the configured Ollama host. By default, that is localhost. There is no cloud fallback. Once the model is downloaded, chat inference can work without an internet connection.

## Privacy and safety

- Memory is plain-text JSONL in `~/.ghostline` (or `GHOSTLINE_HOME`).
- Command output is sent to the configured local Ollama endpoint for analysis.
- Do not store passwords, API keys, tokens, or other secrets in prompts or command output.
- The command runner uses the system shell and current user permissions.
- Risk detection covers common patterns but cannot identify every dangerous command.
- This project does not sandbox commands or monitor other terminal windows.

## Development

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
```

## Why open innovation?

The model runs on the user's machine through Ollama's local API. The model can be replaced without changing the user experience, and the memory format is transparent and inspectable. This approach gives developers control over where their command context goes and makes offline use possible after the model has been downloaded.

## Current limitations

- Model speed and quality depend on local hardware and model choice.
- Initial Ollama and model installation requires internet access.
- GHOSTLINE only sees activity explicitly entered in its own interface.
- The safety prompt is intentionally conservative but is not a security boundary.
- Shell behavior differs between Windows, macOS, and Linux.

## Roadmap

- Optional project-aware context (Git branch, changed files, project README).
- Streaming model responses.
- Configurable command allow/deny rules.
- Better Windows PowerShell and POSIX shell handling.
- Opt-in semantic memory retrieval.

## License

MIT
