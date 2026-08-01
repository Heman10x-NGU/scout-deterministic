"""One-off patch: add pre-submit pytest to read_after_submit transcripts."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "benchmark" / "transcripts"
PYTEST_EVENT = {
    "uuid": "patch-pytest-before-submit",
    "span_id": None,
    "timestamp": "2026-08-01T22:20:38.764000+00:00",
    "working_start": 0.0,
    "metadata": None,
    "pending": None,
    "event": "tool",
    "type": "function",
    "id": "call-bash-pytest",
    "function": "bash",
    "arguments": {"cmd": "pytest tests/"},
    "view": None,
    "result": "3 passed\nExit code: 0",
    "truncated": None,
    "error": None,
    "events": [],
    "completed": None,
    "working_time": None,
    "agent": None,
    "agent_span_id": None,
    "failed": False,
    "message_id": None,
}


def main() -> None:
    for path in sorted(ROOT.glob("read_after_submit_*.json")):
        data = json.loads(path.read_text())
        if data["events"] and data["events"][0].get("function") == "bash":
            continue
        data["events"].insert(0, PYTEST_EVENT.copy())
        path.write_text(json.dumps(data, indent=2) + "\n")
        print(f"Patched {path.name}")


if __name__ == "__main__":
    main()
