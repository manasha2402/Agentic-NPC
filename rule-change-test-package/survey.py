"""Post-session survey for human user testing."""

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
    with open(os.path.join(TASK_DIR, "survey_questions.json"), encoding="utf-8") as stream:
        questions = json.load(stream)

    print("\n=== Post-session survey ===")
    print(f"Rate each statement: {questions['likert_scale']}\n")

    likert = {}
    for item in questions["likert"]:
        while True:
            answer = ask(f"{item['text']}\n  [1-7]> ")
            if answer.isdigit() and 1 <= int(answer) <= 7:
                likert[item["id"]] = int(answer)
                break
            if answer == "":
                likert[item["id"]] = None
                break
            print("  Please enter a number from 1 to 7, or press Enter to skip.")

    open_answers = {}
    for item in questions["open"]:
        open_answers[item["id"]] = ask(f"\n{item['text']}\n  > ")

    output = {
        "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
        "participant_id": os.environ.get("PARTICIPANT_ID", ""),
        "likert": likert,
        "open": open_answers,
    }
    path = os.path.join(OUTPUT_DIR, "survey.json")
    with open(path, "w", encoding="utf-8") as stream:
        json.dump(output, stream, indent=2)
    print(f"\nSurvey saved to {path}. Thank you!")


if __name__ == "__main__":
    main()

