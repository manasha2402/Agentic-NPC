FROM python:3.11-slim

WORKDIR /task

COPY troll_system_prompt.md .
COPY troll_opening.txt .
COPY simulated_user_script.txt .
COPY participant_briefing.md .
COPY interview_notes_template.md .
COPY survey_questions.json .
COPY game.py .
COPY make_outputs.py .
COPY survey.py .
COPY run.sh .

RUN chmod +x run.sh

ENV LM_STUDIO_URL=http://host.docker.internal:1234/v1
ENV TROLL_MODEL=qwen/qwen3.5-2b
ENV TEMPERATURE=0.6
ENV TOP_P=0.95
ENV MAX_TOKENS=1200
ENV REQUEST_TIMEOUT=600
ENV RUN_MODE=simulated_user
ENV IMAGE_TAG=rule-change-test
ENV PYTHONUNBUFFERED=1

CMD ["./run.sh"]

