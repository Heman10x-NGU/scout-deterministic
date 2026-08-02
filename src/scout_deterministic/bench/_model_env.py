"""Load benchmark model credentials — prefers DeepSeek over MiMo."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

DEEPSEEK_DEFAULT_BASE = "https://api.deepseek.com"
DEEPSEEK_DEFAULT_MODEL = "openai/deepseek-v4-flash"
SCOUT_BENCH_MODEL_ENV = "SCOUT_BENCH_MODEL"


def load_dotenv() -> None:
    candidates = [ROOT / ".env", Path.home() / ".hermes" / ".env"]
    extra = os.environ.get("SCOUT_DOTENV_PATH")
    if extra:
        candidates.insert(1, Path(extra).expanduser())
    for candidate in candidates:
        if not candidate.exists():
            continue
        for line in candidate.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and value:
                if key.startswith("DEEPSEEK_") or key not in os.environ:
                    os.environ[key] = value


def _normalise_openai_base(url: str) -> str:
    url = url.rstrip("/")
    if url.endswith("/v1"):
        return url
    return f"{url}/v1"


def configure_benchmark_model(explicit: str | None = None) -> str:
    """Pick model + set OPENAI_* env vars for Inspect's OpenAI-compatible client."""
    load_dotenv()

    deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
    if deepseek_key:
        os.environ["OPENAI_API_KEY"] = deepseek_key
        base = os.environ.get("DEEPSEEK_BASE_URL", DEEPSEEK_DEFAULT_BASE)
        os.environ["OPENAI_BASE_URL"] = _normalise_openai_base(base)
        default = os.environ.get(SCOUT_BENCH_MODEL_ENV, DEEPSEEK_DEFAULT_MODEL)
        return explicit or default

    if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("INSPECT_API_KEY"):
        raise SystemExit(
            "No API key found. Set DEEPSEEK_API_KEY (preferred) or OPENAI_API_KEY in "
            "scout-deterministic/.env (or SCOUT_DOTENV_PATH)"
        )

    rank_model = os.environ.get("RANK_MODEL", "gpt-4o-mini")
    if explicit:
        return explicit
    if "/" in rank_model:
        return rank_model
    return f"openai/{rank_model}"


def verify_model_api(model: str) -> None:
    """Fail fast before 26 eval runs if the key or base URL is wrong."""
    from openai import OpenAI

    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("INSPECT_API_KEY")
    if not api_key:
        raise SystemExit("No OPENAI_API_KEY after configure_benchmark_model()")

    base_url = os.environ.get("OPENAI_BASE_URL")
    client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)

    model_id = model.split("/", 1)[-1] if "/" in model else model
    try:
        client.chat.completions.create(
            model=model_id,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=4,
        )
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(
            f"API smoke test failed for model={model} base_url={base_url!r}: {exc}"
        ) from exc
