"""
survey.py — post-session survey for user-testing mode (RUN_MODE=human).

Usage: python3 survey.py <output_folder>
Reads survey_questions.json, asks each question in the terminal, writes survey.json.
"""
import datetime
import json
import os
import sys

OUTPUT_DIR = sys.argv[1] if len(sys.argv) > 1 else "/output"
TASK_DIR = os.path.dirname(os.path.abspath(__file__))


def ask(prompt):
    try:
        return input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        return ""


def main():
    with open(os.path.join(TASK_DIR, "survey_questions.json")) as f:
        q = json.load(f)

    print("\n=== Post-session survey ===")
    print(f"Rate each statement: {q['likert_scale']}\n")
    likert = {}
    for item in q["likert"]:
        while True:
            a = ask(f"{item['text']}\n  [1-7]> ")
            if a.isdigit() and 1 <= int(a) <= 7:
                likert[item["id"]] = int(a)
                break
            if a == "":
                likert[item["id"]] = None  # skipped
                break
            print("  Please enter a number from 1 to 7 (or press Enter to skip).")

    open_answers = {}
    for item in q["open"]:
        open_answers[item["id"]] = ask(f"\n{item['text']}\n  > ")

    out = {
        "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
        "participant_id": os.environ.get("PARTICIPANT_ID", ""),
        "likert": likert,
        "open": open_answers,
    }
    with open(os.path.join(OUTPUT_DIR, "survey.json"), "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nSurvey saved to {os.path.join(OUTPUT_DIR, 'survey.json')}. Thank you!")


if __name__ == "__main__":
    main()
