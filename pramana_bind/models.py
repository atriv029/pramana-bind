"""Model access. One adapter: headless Claude Code (`claude -p`), which is the
model access configured in the sprint environment. Every call is appended,
raw, to a JSONL log with usage, latency and cost as the CLI reports them.

Generation settings: the CLI exposes no temperature/top-p control, so sampling
is the provider default. The system prompt is replaced with one neutral line
and tools are disabled; a small residual harness preamble (~1.4k tokens, seen
as cache-creation tokens) remains and is the same for every system compared.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Optional

SYSTEM = "You are a careful analyst. Follow the user's instructions exactly."
_lock = threading.Lock()


class ClaudeCLI:
    provider = "anthropic (first-party, via Claude Code CLI headless mode)"

    def __init__(self, model: str, log_path: Path, *, retries: int = 2, timeout: int = 180):
        self.model, self.log_path = model, Path(log_path)
        self.retries, self.timeout = retries, timeout
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def config(self) -> dict[str, Any]:
        return {"provider": self.provider, "model": self.model, "system_prompt": SYSTEM,
                "tools": "disabled", "temperature": "provider default (not settable through this interface)",
                "max_output_tokens": "provider default", "response_format": "free text; JSON object parsed by caller",
                "retries": self.retries, "timeout_s": self.timeout}

    def call(self, prompt: str, tag: Optional[dict] = None) -> dict[str, Any]:
        """One request (with retries on transport/CLI errors only; a malformed
        answer is NOT retried -- it is kept and counted). Returns the log record."""
        rec: dict[str, Any] = {"tag": tag or {}, "model": self.model,
                               "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(), "attempts": 0}
        for attempt in range(self.retries + 1):
            rec["attempts"] = attempt + 1
            t0 = time.time()
            try:
                p = subprocess.run(
                    ["claude", "-p", "--model", self.model, "--output-format", "json",
                     "--system-prompt", SYSTEM, "--tools", ""],
                    input=prompt, capture_output=True, text=True, timeout=self.timeout, cwd="/tmp")
                o = json.loads(p.stdout)
                if o.get("is_error"):
                    raise RuntimeError(str(o.get("result"))[:300])
                u = o.get("usage", {})
                rec.update(ok=True, text=o.get("result", ""), latency_s=round(time.time() - t0, 3),
                           api_ms=o.get("duration_api_ms"), cost_usd=o.get("total_cost_usd"),
                           input_tokens=(u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
                                         + u.get("cache_read_input_tokens", 0)),
                           output_tokens=u.get("output_tokens", 0), stop_reason=o.get("stop_reason"),
                           served_model=next(iter(o.get("modelUsage", {})), None))
                break
            except Exception as e:  # noqa: BLE001 - recorded, then retried or surfaced as a failed call
                rec.update(ok=False, text="", error=f"{type(e).__name__}: {e}"[:300],
                           latency_s=round(time.time() - t0, 3))
                time.sleep(2 * (attempt + 1))
        with _lock, self.log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return rec

    def ask(self, prompt: str) -> str:
        return self.call(prompt)["text"]
