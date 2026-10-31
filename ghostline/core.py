"""Local-first intelligence, memory, and export utilities for GHOSTLINE."""
from __future__ import annotations
import json
import os
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4

SYSTEM_PROMPT = """You are GHOSTLINE, an eerie but helpful intelligence inhabiting a developer's terminal.
Use restrained supernatural atmosphere: observant, cryptic at times, occasionally witty, never obscure.
You are a practical developer assistant first. Be accurate. Never claim to have executed a command unless its output is supplied.
When analyzing command output, distinguish facts from guesses. Explain errors and risks clearly.
Never recommend destructive commands casually. Keep replies concise.
"""

def data_dir() -> Path:
    override = os.getenv("GHOSTLINE_HOME")
    return Path(override).expanduser() if override else Path.home() / ".ghostline"

class Memory:
    """Append-only local JSONL memory. No telemetry or remote storage."""
    def __init__(self, path: Path | None = None):
        self.path = path or (data_dir() / "memory.jsonl")
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def add(self, role: str, content: str, session_id: str = "default",
            kind: str = "chat") -> None:
        row = {
            "time": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "role": role,
            "kind": kind,
            "content": content,
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def all(self) -> list[dict]:
        if not self.path.exists():
            return []
        rows = []
        with self.path.open(encoding="utf-8") as f:
            for line in f:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return rows

    def recent(self, limit: int = 12, session_id: str | None = None) -> list[dict]:
        rows = self.all()
        if session_id:
            rows = [r for r in rows if r.get("session_id") == session_id]
        return rows[-limit:]

    def clear(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("", encoding="utf-8")

    def export_markdown(self, destination: Path, session_id: str | None = None) -> Path:
        rows = self.all()
        if session_id:
            rows = [r for r in rows if r.get("session_id") == session_id]
        lines = ["# GHOSTLINE Session Archive", "",
                 f"Exported: {datetime.now(timezone.utc).isoformat()}", ""]
        for row in rows:
            stamp = row.get("time", "")
            role = row.get("role", "unknown").upper()
            kind = row.get("kind", "chat")
            lines.extend([f"## {role} · {kind} · {stamp}", "", row.get("content", ""), ""])
        destination = destination.expanduser()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("\n".join(lines), encoding="utf-8")
        return destination

def ask_local_model(prompt: str, history: list[dict] | None = None) -> str:
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    model = os.getenv("GHOSTLINE_MODEL", "qwen3:8b")
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for item in (history or [])[-12:]:
        if item.get("role") in ("user", "assistant"):
            messages.append({"role": item["role"], "content": item["content"][:5000]})
    messages.append({"role": "user", "content": prompt})
    payload = json.dumps({
        "model": model, "messages": messages, "stream": False,
        "options": {"temperature": 0.72}
    }).encode("utf-8")
    req = urllib.request.Request(
        host + "/api/chat", data=payload,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as response:
            result = json.loads(response.read().decode("utf-8"))
        return result.get("message", {}).get("content", "").strip() or "The signal returned an empty whisper."
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            f"Cannot reach Ollama at {host}. Start Ollama and pull '{model}'. "
            f"No cloud fallback was attempted. Detail: {exc}"
        ) from exc

def ollama_status() -> tuple[bool, str]:
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    try:
        req = urllib.request.Request(host + "/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode("utf-8"))
        models = [m.get("name", "") for m in data.get("models", [])]
        selected = os.getenv("GHOSTLINE_MODEL", "qwen3:8b")
        match = any(name == selected or name.startswith(selected + ":") for name in models)
        return True, f"Ollama online · {selected} " + ("available" if match else "not pulled")
    except Exception:
        return False, f"Ollama unreachable at {host}"
