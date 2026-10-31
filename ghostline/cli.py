"""GHOSTLINE 2.0 command-line interface."""
from __future__ import annotations
import argparse
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4
from .core import Memory, ask_local_model, ollama_status, data_dir

RESET = "\033[0m"
GREEN = "\033[92m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
YELLOW = "\033[93m"
RED = "\033[91m"
DIM = "\033[2m"
BOLD = "\033[1m"

def paint(text: str, color: str) -> str:
    if os.getenv("NO_COLOR"):
        return text
    return color + text + RESET

BANNER = r"""
   ____ _  ___  ____ _____ _     ___ _   _ _____
  / ___| |/ _ \\/ ___|_   _| |   |_ _| \\ | | ____|
 | |  _| | | | \\___ \\ | | | |    | ||  \\| |  _|
 | |_| | | |_| |___) || | | |___ | || |\\  | |___
  \\____|_|\\___/|____/ |_| |_____|___|_| \\_|_____|
"""
RISK_PATTERNS = [
    r"\brm\s+-[^\n]*r[^\n]*f\b", r"\brm\s+-rf\b", r"\bdel\s+/[fq]\b",
    r"\brmdir\s+/s\b", r"\bformat\s+[a-z]:", r"\bdiskpart\b",
    r"\b(shutdown|reboot)\b", r"\bmkfs(\.| )", r"\bdd\s+if=",
    r"\bRemove-Item\b.*-Recurse", r"\bDROP\s+DATABASE\b",
    r"\bDROP\s+TABLE\b", r"\bchmod\s+-R\s+777\b",
]

def looks_destructive(command: str) -> bool:
    return any(re.search(pattern, command, re.IGNORECASE) for pattern in RISK_PATTERNS)

def run_command(command: str) -> tuple[int, str]:
    """Execute a user-entered command in the user's shell and capture output."""
    completed = subprocess.run(
        command, shell=True, text=True, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    return completed.returncode, completed.stdout or "(no output)"

def type_out(text: str, delay: float = 0.008) -> None:
    if os.getenv("GHOSTLINE_NO_ANIMATION"):
        print(text)
        return
    for char in text:
        print(char, end="", flush=True)
        if char not in "\n":
            time.sleep(delay)
    print()

def show_help() -> None:
    print("""
  :run <command>     Run a command you explicitly provide
  :memory            Show recent local memory
  :export [file.md]  Export this session as Markdown
  :status            Check local Ollama and model availability
  :clear             Erase local memory (confirmation required)
  :help              Show this help
  :quit              Exit GHOSTLINE
""")

def demo() -> int:
    print(paint(BANNER, GREEN))
    print(paint("             SIMULATED TRANSMISSION · DEMO MODE", MAGENTA))
    print("\nThe machine is awake. This is a scripted demonstration; no commands run.\n")
    samples = [
        ("you", "Why did my build fail?"),
        ("ghost", "The compiler left a footprint: `ModuleNotFoundError`. Python cannot find the package in the active environment. Check which interpreter your terminal is using, then install the dependency there."),
        ("you", ":run git status"),
        ("system", "On branch main\\nYour branch is up to date with 'origin/main'.\\nnothing to commit, working tree clean"),
        ("ghost", "A clean tree. No uncommitted changes are waiting in the dark. Your working directory matches the current branch state."),
    ]
    for role, message in samples:
        color = CYAN if role == "you" else GREEN if role == "ghost" else DIM
        label = "YOU" if role == "you" else "GHOSTLINE" if role == "ghost" else "COMMAND OUTPUT"
        print(paint(f"{label} >", color))
        type_out(message, 0.002)
        print()
    print(paint("Demo complete. Install Ollama to use live local inference.", YELLOW))
    return 0

def interactive() -> int:
    memory = Memory()
    session_id = str(uuid4())[:8]
    print(paint(BANNER, GREEN))
    print(paint("          THE TERMINAL THAT REMEMBERS · v2.0", MAGENTA))
    print(paint(f"Session {session_id} · memory stored locally · no cloud fallback", DIM))
    print("Type :help for commands. Nothing executes unless you use :run.\n")
    while True:
        try:
            line = input(paint("you > ", CYAN)).strip()
        except (EOFError, KeyboardInterrupt):
            print("\n" + paint("The signal fades. Until next time.", GREEN))
            return 0
        if not line:
            continue
        if line in (":quit", ":q", "exit"):
            print(paint("GHOSTLINE > Until the next transmission.", GREEN))
            return 0
        if line == ":help":
            show_help()
            continue
        if line == ":status":
            online, status = ollama_status()
            print(paint(("● " if online else "○ ") + status, GREEN if online else YELLOW))
            continue
        if line == ":memory":
            rows = memory.recent(20, session_id)
            if not rows:
                print("(This session has left no memories.)")
            for row in rows:
                print(f"{row['time']} [{row['role']}/{row.get('kind','chat')}] {row['content'][:220]}")
            continue
        if line.startswith(":export"):
            parts = shlex.split(line)
            target = Path(parts[1]) if len(parts) > 1 else Path.cwd() / f"ghostline-{session_id}.md"
            try:
                result = memory.export_markdown(target, session_id)
                print(paint(f"Session archived: {result.resolve()}", GREEN))
            except OSError as exc:
                print(paint(f"Could not export: {exc}", RED))
            continue
        if line == ":clear":
            confirm = input(paint("Erase ALL local GHOSTLINE memory? [y/N] ", YELLOW)).strip().lower()
            if confirm == "y":
                memory.clear()
                print(paint("Memory erased. The room is quiet again.", GREEN))
            continue
        if line.startswith(":run "):
            command = line[5:].strip()
            if not command:
                print("Specify a command after :run.")
                continue
            if looks_destructive(command):
                confirm = input(paint("This command looks destructive. Run it anyway? [y/N] ", RED)).strip().lower()
                if confirm != "y":
                    print("Execution cancelled.")
                    continue
            print(paint(f"Executing: {command}", DIM))
            try:
                code, output = run_command(command)
            except Exception as exc:
                code, output = 1, str(exc)
            print(output.rstrip())
            context = (f"The user explicitly ran this command: {command}\n"
                       f"Exit code: {code}\nOutput:\n{output[-7000:]}\n"
                       "Explain what happened. Distinguish facts from assumptions and mention notable risks.")
            memory.add("user", context, session_id, "command")
            try:
                answer = ask_local_model(context, memory.recent(12, session_id))
                memory.add("assistant", answer, session_id, "analysis")
                print(paint("\nGHOSTLINE > ", GREEN) + answer + "\n")
            except RuntimeError as exc:
                print(paint(str(exc), RED))
            continue
        memory.add("user", line, session_id, "chat")
        try:
            answer = ask_local_model(line, memory.recent(12, session_id))
            memory.add("assistant", answer, session_id, "chat")
            print(paint("\nGHOSTLINE > ", GREEN) + answer + "\n")
        except RuntimeError as exc:
            print(paint(str(exc), RED))

def main() -> int:
    parser = argparse.ArgumentParser(description="A local AI ghost for your terminal.")
    parser.add_argument("--demo", action="store_true", help="Run a scripted demo without Ollama")
    parser.add_argument("--model", help="Ollama model name (default: qwen3:8b)")
    args = parser.parse_args()
    if args.model:
        os.environ["GHOSTLINE_MODEL"] = args.model
    return demo() if args.demo else interactive()

if __name__ == "__main__":
    sys.exit(main())
