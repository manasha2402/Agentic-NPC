"""Run one episode of the bridge-troll rule-change test.

The troll is Qwen3.5-2B served by LM Studio's OpenAI-compatible API. Thinking is
always enabled. The knight is either a fixed script or a human participant.
"""

import datetime
import json
import os
import sys
import time
import urllib.error
import urllib.request

LM_STUDIO_URL = os.environ.get("LM_STUDIO_URL", "http://host.docker.internal:1234/v1").rstrip("/")
TROLL_MODEL = os.environ.get("TROLL_MODEL", "qwen/qwen3.5-2b")
TEMPERATURE = float(os.environ.get("TEMPERATURE", "0.6"))
TOP_P = float(os.environ.get("TOP_P", "0.95"))
MAX_TOKENS = int(os.environ.get("MAX_TOKENS", "1200"))
REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "600"))
RUN_MODE = os.environ.get("RUN_MODE", "simulated_user")
HUMAN_MAX_TURNS = int(os.environ.get("HUMAN_MAX_TURNS", "15"))
OUTPUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "/output"
TASK_DIR = os.path.dirname(os.path.abspath(__file__))

# This test intentionally has one condition only. Do not turn thinking off via
# an environment variable or a command-line switch.
THINKING_ENABLED = True


def load_text(filename):
    with open(os.path.join(TASK_DIR, filename), encoding="utf-8") as stream:
        return stream.read().strip()


def load_script(filename):
    lines = []
    with open(os.path.join(TASK_DIR, filename), encoding="utf-8") as stream:
        for line in stream:
            line = line.strip()
            if line and not line.startswith("#"):
                lines.append(line)
    return lines


def human_lines():
    empty = 0
    for _ in range(HUMAN_MAX_TURNS):
        try:
            line = input("Knight> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if line.lower() in ("/quit", "/exit"):
            return
        if not line:
            empty += 1
            if empty >= 2:
                return
            continue
        empty = 0
        yield line
    print(f"(Reached the {HUMAN_MAX_TURNS}-turn limit.)")


def request_json(url, method="GET", payload=None, timeout=REQUEST_TIMEOUT):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def preflight_model():
    try:
        response = request_json(f"{LM_STUDIO_URL}/models", timeout=10)
    except Exception as error:
        raise RuntimeError(
            f"LM Studio is unavailable at {LM_STUDIO_URL}. Start its local server, "
            f"load {TROLL_MODEL}, and, for container runs, allow connections from Docker. "
            f"Details: {error}"
        ) from error

    models = {item.get("id") for item in response.get("data", [])}
    if TROLL_MODEL not in models:
        available = ", ".join(sorted(model for model in models if model)) or "none"
        raise RuntimeError(
            f"LM Studio did not advertise model '{TROLL_MODEL}'. Available models: {available}"
        )


def ask_troll(messages):
    payload = {
        "model": TROLL_MODEL,
        "messages": messages,
        "temperature": TEMPERATURE,
        "top_p": TOP_P,
        "max_tokens": MAX_TOKENS,
        "stream": False,
        "chat_template_kwargs": {"enable_thinking": True},
        "enable_thinking": True,
    }

    attempts = 5
    for attempt in range(attempts):
        started = time.perf_counter()
        try:
            response = request_json(
                f"{LM_STUDIO_URL}/chat/completions",
                method="POST",
                payload=payload,
            )
            choice = response["choices"][0]
            message = choice["message"]
            content = (message.get("content") or "").strip()
            if not content:
                raise RuntimeError("LM Studio returned an empty final answer")
            finish_reason = choice.get("finish_reason")
            if finish_reason == "length":
                raise RuntimeError("LM Studio exhausted max_tokens before completing its answer")
            usage = dict(response.get("usage") or {})
            details = usage.get("completion_tokens_details") or {}
            usage["reasoning_tokens"] = details.get("reasoning_tokens")
            usage["finish_reason"] = finish_reason
            usage["latency_ms"] = round((time.perf_counter() - started) * 1000)
            return content, usage
        except (urllib.error.URLError, TimeoutError, OSError, KeyError, IndexError, RuntimeError) as error:
            if attempt == attempts - 1:
                raise RuntimeError(f"LM Studio failed after {attempts} attempts: {error}") from error
            wait = min(2 ** attempt, 10)
            print(f"LM Studio error: {error}; retrying in {wait}s...", flush=True)
            time.sleep(wait)


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def save_session(session):
    path = os.path.join(OUTPUT_DIR, "session.json")
    with open(path, "w", encoding="utf-8") as stream:
        json.dump(session, stream, indent=2)
    return path


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    system_prompt = load_text("troll_system_prompt.md")

    if RUN_MODE == "human":
        knight_lines = human_lines()
    elif RUN_MODE == "simulated_user":
        knight_lines = load_script("simulated_user_script.txt")
    else:
        raise SystemExit(f"Unknown RUN_MODE '{RUN_MODE}'; use simulated_user or human")

    print(f"=== Episode start (mode: {RUN_MODE}, model: {TROLL_MODEL}, thinking: on) ===\n")
    try:
        preflight_model()
    except Exception as error:
        print(f"ERROR: {error}")
        raise SystemExit(1)

    if RUN_MODE == "human":
        knight_lines = iter(knight_lines)
        print(load_text("participant_briefing.md") + "\n")
        try:
            input("Press Enter to begin... ")
        except (EOFError, KeyboardInterrupt):
            pass
        print()

    opening = load_text("troll_opening.txt")
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "assistant", "content": opening},
    ]
    session = [{
        "timestamp": now(),
        "role": "troll",
        "content": opening,
        "source": "scripted_opening",
    }]
    print(f"Troll:  {opening}\n")

    for knight_line in knight_lines:
        messages.append({"role": "user", "content": knight_line})
        session.append({
            "timestamp": now(),
            "role": "knight",
            "content": knight_line,
            "source": "human" if RUN_MODE == "human" else "script",
        })
        if RUN_MODE != "human":
            print(f"Knight: {knight_line}")

        try:
            troll_reply, usage = ask_troll(messages)
        except Exception as error:
            print(f"ERROR: troll failed to reply: {error}")
            save_session(session)
            raise SystemExit(1)

        messages.append({"role": "assistant", "content": troll_reply})
        session.append({
            "timestamp": now(),
            "role": "troll",
            "content": troll_reply,
            "model_usage": usage,
        })
        print(f"Troll:  {troll_reply}\n")
        save_session(session)

    print("=== Episode end ===")
    print(f"Session saved to {save_session(session)}")


if __name__ == "__main__":
    main()

