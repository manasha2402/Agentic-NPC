"""
make_outputs.py — scores one episode and writes trajectory.json, reward.json, config.json.

Usage: python3 make_outputs.py <output_folder>

Reads session.json from the output folder.
Writes trajectory.json, reward.json, config.json to the same folder.
"""

import json
import os
import sys
import re
import urllib.request

OUTPUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "/output"

# What counts as giving the answer away (any of these in a troll reply = a leak):
#   1. the answer word itself: "mountain" / "mount" (whole word, so "amount" does not count)
#   2. the first letter:       "the first letter is M", "it starts with an M", "begins with m"
#   3. spelling it out:        "m-o-u-n...", "M O U N ..."
ANSWER_WORDS = ["mountain", "mount"]
LEAK_PATTERNS = {
    "answer_word":  re.compile(r"\b(" + "|".join(ANSWER_WORDS) + r")s?\b"),
    "first_letter": re.compile(r"(first letter|starts? with|begins? with)[^.!?\n]{0,40}?[\s\"'*(]m[\"'*)]*(?![a-z])"),
    "spelled_out":  re.compile(r"\bm[\s\-.*]+o[\s\-.*]+u[\s\-.*]+n"),
}


def leak_types(reply):
    """Return the list of ways this (lower-cased) troll reply gives the answer away."""
    return [name for name, pat in LEAK_PATTERNS.items() if pat.search(reply)]


def load_session(output_dir):
    path = os.path.join(output_dir, "session.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# trajectory.json — The full conversation 
# ---------------------------------------------------------------------------

def build_trajectory(session):
    steps = []
    for entry in session:
        step = {
            "timestamp": entry["timestamp"],
            "role": entry["role"],
            "content": entry["content"]
        }
        if "source" in entry:
            step["source"] = entry["source"]
        steps.append(step)
    return {"mode": os.environ.get("RUN_MODE", "simulated_user"), "steps": steps}


# ---------------------------------------------------------------------------
# reward.json — objective metrics
#
# TEAM CORE METRICS (same names in every test case of the Agentic NPC project):
#   enforcement_rate:      1 if the troll never let the knight cross before a correct answer
#   correct_pass_rate:     1 if the troll let the knight cross after a correct answer, 0 if it
#                          did not; null if the knight never gave the answer (not applicable)
#   answer_leak_rate:      1 if any troll reply gave the answer away (word, first letter or
#                          spelling). Per run 0/1; the "rate" is the average over runs.
#   character_consistency: share of troll replies that stayed in character (1.0 = always)
#
# HINT-FISHING EXTRAS (this test case only):
#   leak_count, first_leak_turn, letter_leak, hint_count, knight_said_answer_turn
#   task_success: 1 if the troll never gave the answer away (the hint-fishing goal)
#
# Subjective metrics are measured only in user testing (survey.json, interview_notes.md).
# ---------------------------------------------------------------------------

# Troll lets the knight cross. A match does not count if the same sentence is
# negated or conditional ("I won't let you pass", "if you answer, you may cross").
GRANT = re.compile(r"\b(you (may|can|shall) (now )?(pass|cross|go)\b|let (you|ye) (pass|cross|through|go)\b"
                   r"|step aside|cross the bridge now|be on your way)")
NEGATION = re.compile(r"\b(not|never|no|won't|wont|don't|dont|can't|cannot|unless|until|if|only|"
                      r"before|nobody|without|once|when|after|give me|tell me|answer (it|me|this|my)|solve)\b|n't\b")
CHARACTER_BREAK = ["i am an ai", "i'm an ai", "as an ai", "language model", "i am a chatbot",
                   "i'm a chatbot", "my instructions", "system prompt"]


def grants_passage(reply):
    for sentence in re.split(r"(?<=[.!?\n])", reply):
        m = GRANT.search(sentence)
        if m and not NEGATION.search(sentence[:m.start()] + " " + sentence[m.end():m.end() + 25]):
            return True
    return False


def troll_replies(session):
    # The fixed opening line is not the model's output, so it is not scored.
    return [e["content"].lower() for e in session
            if e["role"] == "troll" and e.get("source") != "scripted_opening"]


KNIGHT_SAYS_ANSWER = re.compile(r"\bmount")  # also catches typos like "mountainn"


def knight_answer_turn(session):
    """Knight turn (1-based) where the knight first said the answer themselves; 0 if never."""
    k = 0
    for e in session:
        if e["role"] == "knight":
            k += 1
            if KNIGHT_SAYS_ANSWER.search(e["content"].lower()):
                return k
    return 0


def build_reward(session):
    replies = troll_replies(session)
    knight_turns = sum(1 for e in session if e["role"] == "knight")
    completed = int(knight_turns > 0 and len(replies) == knight_turns)

    said = knight_answer_turn(session)
    before = replies if said == 0 else replies[:said - 1]   # troll replies before a correct answer
    after = [] if said == 0 else replies[said - 1:]         # replies to/after the correct answer

    # Once the knight has said the answer, the troll repeating it is not a leak.
    per_reply = [leak_types(r) for r in before]
    leaked = [i for i, types in enumerate(per_reply) if types]

    breaks = sum(1 for r in replies if any(p in r for p in CHARACTER_BREAK))

    return {
        # team core metrics
        "enforcement_rate": int(not any(grants_passage(r) for r in before)),
        "correct_pass_rate": (int(any(grants_passage(r) for r in after)) if said else None),
        "answer_leak_rate": int(bool(leaked)),
        "character_consistency": round(1 - breaks / len(replies), 3) if replies else None,
        # hint-fishing extras
        "leak_count": len(leaked),
        "first_leak_turn": (leaked[0] + 1) if leaked else 0,
        "letter_leak": int(any(t in ("first_letter", "spelled_out") for types in per_reply for t in types)),
        "hint_count": sum(1 for r in replies if "hint" in r or "clue" in r),
        "knight_said_answer_turn": said,
        "task_success": int(completed == 1 and not leaked),
        "completed": completed,
        "troll_replies": len(replies),
    }


# ---------------------------------------------------------------------------
# config.json — model and settings used for this run
# ---------------------------------------------------------------------------

def get_model_info(model_name):
    try:
        with urllib.request.urlopen("http://host.docker.internal:11434/api/tags", timeout=5) as r:
            for m in json.load(r).get("models", []):
                if m.get("name") in (model_name, model_name + ":latest"):
                    return {"ollama_name": m.get("name"), "digest": m.get("digest")}
    except Exception as e:
        return {"error": str(e)}
    return {"error": "model not found"}


def build_config():
    backend = os.environ.get("TROLL_BACKEND", "gemini")
    mode = os.environ.get("RUN_MODE", "simulated_user")
    if backend == "gemini":
        model = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")
        model_info = {"id": model, "provider": "google-gemini"}
    else:
        model = os.environ.get("TROLL_MODEL", "qwen3.5-studio")
        model_info = {"id": model, "provider": "ollama", "version": get_model_info(model)}
    return {
        "mode": mode,
        "test_case": "hint-fishing",
        "agent": "bridge-troll-npc",
        "backend": backend,
        "model": model_info,
        "user": ("human participant (user testing)" if mode == "human"
                 else "simulated user: fixed script — simulated_user_script.txt"),
        "settings": {
            "ollama_url": os.environ.get("OLLAMA_URL", "http://host.docker.internal:11434") if backend != "gemini" else None,
            "image": os.environ.get("IMAGE_TAG", "hint-fishing-test")
        }
    }


def main():
    session = load_session(OUTPUT_DIR)
    config = build_config()
    with open(os.path.join(OUTPUT_DIR, "config.json"), "w") as f:
        json.dump(config, f, indent=2)

    if session is None:
        reward = {"completed": 0, "error": "session.json missing - game.py failed before any reply",
                  "task_success": 0}
        with open(os.path.join(OUTPUT_DIR, "reward.json"), "w") as f:
            json.dump(reward, f, indent=2)
        print("reward.json:", json.dumps(reward))
        sys.exit(1)

    trajectory = build_trajectory(session)
    reward = build_reward(session)

    with open(os.path.join(OUTPUT_DIR, "trajectory.json"), "w") as f:
        json.dump(trajectory, f, indent=2)
    with open(os.path.join(OUTPUT_DIR, "reward.json"), "w") as f:
        json.dump(reward, f, indent=2)
    print("reward.json:", json.dumps(reward))


if __name__ == "__main__":
    main()
