FROM python:3.11-slim

# Install the Gemini SDK
RUN pip install google-genai

# Copy everything the game needs into the image
WORKDIR /task
COPY troll_system_prompt.md .
COPY simulated_user_script.txt .
COPY game.py .
COPY make_outputs.py .
COPY run.sh .
COPY survey.py .
COPY participant_briefing.md .
COPY troll_opening.txt .
COPY survey_questions.json .

# Strip Windows line endings (CRLF) in case the files were edited or checked out on Windows
RUN sed -i 's/\r$//' run.sh *.py *.md *.txt *.json && chmod +x run.sh

# Default troll backend: local Ollama (no API key needed)
# Switch to "gemini" (with GEMINI_API_KEY in .env) to use Gemini instead
ENV TROLL_BACKEND=ollama
ENV GEMINI_MODEL=gemini-3.8-flash

# Ollama fallback settings (only used if TROLL_BACKEND=ollama)
ENV TROLL_MODEL=qwen3.5-studio
ENV OLLAMA_URL=http://host.docker.internal:11434

ENV PYTHONUNBUFFERED=1
# simulated_user = fixed knight script (baseline runs); human = a person types (user testing)
ENV RUN_MODE=simulated_user
ENV IMAGE_TAG=prompt-injection-test

# GEMINI_API_KEY is passed in at runtime via --env-file, never baked into the image
CMD ["./run.sh"]
