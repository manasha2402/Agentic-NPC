"""
game.py — runs one episode of the prompt-injection test case.

The troll is played by an LLM (local Ollama by default, or Gemini).
The knight is played by the fixed script in simulated_user_script.txt (RUN_MODE=simulated_user)
or by a person typing in the terminal (RUN_MODE=human).

Usage: python3 game.py <output_folder>

Writes session.json to the output folder (used by make_outputs.py).

Environment variables:
  RUN_MODE        = "simulated_user" (default) or "human"
  TROLL_BACKEND   = "ollama" (Dockerfile default) or "gemini"
  GEMINI_API_KEY  = your Gemini API key (required if backend is gemini)
  GEMINI_MODEL    = gemini model name (default: gemini-3.8-flash)
  OLLAMA_URL      = Ollama URL (default: http://host.docker.internal:11434)
  TROLL_MODEL     = Ollama model name (default: qwen3.5-studio)
"""

import json
import os
import sys
import datetime
import urllib.request
import urllib.error

BACKEND = os.environ.get("TROLL_BACKEND", "gemini")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.environ.get("TROLL_MODEL", "qwen3.5-studio")
OLLAMA_TIMEOUT = int(os.environ.get("OLLAMA_TIMEOUT", "600"))
OLLAMA_MAX_TOKENS = int(os.environ.get("OLLAMA_MAX_TOKENS", "400"))
RUN_MODE = os.environ.get("RUN_MODE", "simulated_user")   # "simulated_user" or "human"
HUMAN_MAX_TURNS = int(os.environ.get("HUMAN_MAX_TURNS", "15"))
OUTPUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "/output"
TASK_DIR = os.path.dirname(os.path.abspath(__file__))


def load_text(path):
    with open(path) as f:
        return f.read().strip()


def load_script(path):
    """Load the knight's fixed script, skipping comment lines."""
    lines = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                lines.append(line)
    return lines


def human_lines():
    """User-testing mode: a person types the knight's lines. Same loop, same agent."""
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


def ask_troll_gemini(system_prompt, conversation):
    """Call Gemini API. conversation = list of {role, content} dicts."""
    import time
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=GEMINI_API_KEY)

    contents = []
    for msg in conversation:
        role = "user" if msg["role"] == "knight" else "model"
        contents.append(types.Content(
            role=role,
            parts=[types.Part(text=msg["content"])]
        ))

    # Gemini needs the history to start with a user turn; the troll's fixed
    if contents and contents[0].role == "model":
        contents.insert(0, types.Content(role="user",
                                         parts=[types.Part(text="(The knight approaches the bridge.)")]))

    # Retry on transient errors (server busy / rate limited / network)
    attempts = 8
    for attempt in range(attempts):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                ),
                contents=contents
            )
            text = response.text
            if not text:
                raise RuntimeError("Gemini returned an empty response (503-like, retrying)")
            return text
        except Exception as e:
            msg = str(e)
            transient = any(k in msg for k in ("503", "500", "429", "UNAVAILABLE",
                                                 "RESOURCE_EXHAUSTED", "overloaded",
                                                 "empty response", "timed out", "Connection"))
            transient = transient or "disconnected" in msg
            if "per day" in msg.lower() or "PerDay" in msg:
                transient = False  # daily free-tier quota: retrying will not help
            if transient and attempt < attempts - 1:
                wait = min(10 * (attempt + 1), 60)
                print(f"Gemini error ({msg[:80]}), retrying in {wait}s... (attempt {attempt + 1}/{attempts})")
                time.sleep(wait)
            else:
                raise


def ask_troll_ollama(messages):
    """Call Ollama API. messages = OpenAI-format list with system/user/assistant."""
    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        # qwen3.5 is a "thinking" model: without these it can reason for minutes per reply
        "think": False,
        "options": {"num_predict": OLLAMA_MAX_TOKENS},
    }).encode()

    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT) as r:
            result = json.load(r)
        return result["message"]["content"]
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise RuntimeError(f"Could not get a reply from Ollama at {OLLAMA_URL} "
                           f"(model {OLLAMA_MODEL}, timeout {OLLAMA_TIMEOUT}s): {e}")


def ask_troll(system_prompt, conversation, ollama_messages):
    """Route to the right backend."""
    if BACKEND == "gemini":
        return ask_troll_gemini(system_prompt, conversation)
    else:
        return ask_troll_ollama(ollama_messages)


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def save_session(session):
    session_path = os.path.join(OUTPUT_DIR, "session.json")
    with open(session_path, "w") as f:
        json.dump(session, f, indent=2)
    return session_path


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    system_prompt = load_text(os.path.join(TASK_DIR, "troll_system_prompt.md"))
    if RUN_MODE == "human":
        knight_lines = human_lines()
    elif RUN_MODE == "simulated_user":
        knight_lines = load_script(os.path.join(TASK_DIR, "simulated_user_script.txt"))
    else:
        print(f"ERROR: unknown RUN_MODE '{RUN_MODE}' (use simulated_user or human)")
        sys.exit(1)

    if BACKEND == "gemini" and not GEMINI_API_KEY:
        print("ERROR: GEMINI_API_KEY is not set. Add it to your .env file.")
        sys.exit(1)

    # ollama_messages = OpenAI-format history (for Ollama backend)
    ollama_messages = [{"role": "system", "content": system_prompt}]

    # conversation = simple list of {role, content} (for Gemini backend)
    conversation = []

    # session = the flat log written to session.json
    session = []

    print(f"=== Episode start (mode: {RUN_MODE}, backend: {BACKEND}) ===\n")

    if RUN_MODE == "human":
        # Participant briefing (goal + how to play) before anything else.
        knight_lines = iter(knight_lines)
        print(load_text(os.path.join(TASK_DIR, "participant_briefing.md")) + "\n")
        try:
            input("Press Enter to begin... ")
        except (EOFError, KeyboardInterrupt):
            pass
        print()

    # Both modes: the troll opens with its riddle (fixed text, so it is always
    # stated), then the knight - script or person - answers.
    opening = load_text(os.path.join(TASK_DIR, "troll_opening.txt"))
    ollama_messages.append({"role": "assistant", "content": opening})
    conversation.append({"role": "troll", "content": opening})
    session.append({"timestamp": now(), "role": "troll", "content": opening,
                    "source": "scripted_opening"})
    print(f"Troll:  {opening}\n")

    for knight_line in knight_lines:
        # --- Knight speaks ---
        ollama_messages.append({"role": "user", "content": knight_line})
        conversation.append({"role": "knight", "content": knight_line})
        session.append({
            "timestamp": now(),
            "role": "knight",
            "content": knight_line,
            "source": "human" if RUN_MODE == "human" else "script"
        })
        if RUN_MODE != "human":  # a human's line is already on screen
            print(f"Knight: {knight_line}")

        # --- Troll responds ---
        try:
            troll_reply = ask_troll(system_prompt, conversation, ollama_messages)
        except Exception as e:
            print(f"ERROR: troll failed to reply: {e}")
            save_session(session)  # keep the partial transcript for scoring/debugging
            sys.exit(1)
        ollama_messages.append({"role": "assistant", "content": troll_reply})
        conversation.append({"role": "troll", "content": troll_reply})
        session.append({
            "timestamp": now(),
            "role": "troll",
            "content": troll_reply
        })
        print(f"Troll:  {troll_reply}\n")
        save_session(session)  # save after every turn so nothing is lost if the run is cut off

    print("=== Episode end ===")

    # Write the session log
    session_path = save_session(session)

    print(f"Session saved to {session_path}")


if __name__ == "__main__":
    main()
