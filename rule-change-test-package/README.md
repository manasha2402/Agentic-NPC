# Rule-change bridge-troll test package

This folder is the portable, runnable test-case repository. It contains the environment, fixed task and prompts, simulated-user persona/script, human-user protocol and survey, and the required outputs from five baseline runs. The model itself is not bundled.

## Requirements

- Windows 10/11
- Python 3.11 or newer on `PATH` (the harness uses only the standard library)
- LM Studio with its `lms` command available
- About 2 GB free for `Qwen3.5-2B-Q4_K_M`
- Docker Desktop is optional; the native PowerShell path does not require it

No API key is used or included.

## Fast handoff procedure

After extracting the ZIP, open PowerShell in this folder. Install and open LM Studio, then run:

```powershell
.\setup_lmstudio.ps1
.\verify_setup.ps1
.\run_reproduction_local.ps1
```

The setup script downloads and loads the exact model, starts the local API, and uses the stable identifier expected by the harness. The reproduction launcher creates a new timestamped folder without modifying the five included baseline runs.

To demonstrate human-user mode afterward:

```powershell
.\run_human_local.ps1 -ParticipantId P01
```

Use a new participant ID for every human session.

## Manual LM Studio setup

The automatic setup above is recommended. These are the equivalent manual commands:

```powershell
lms get qwen/qwen3.5-2b@q4_k_m --gguf --yes
lms server start --port 1234 --bind 127.0.0.1
lms load qwen/qwen3.5-2b --context-length 8192 --gpu max --identifier qwen/qwen3.5-2b --yes
```

Verify that `qwen/qwen3.5-2b` appears:

```powershell
lms ps
```

If `lms` is not recognized, enable the LM Studio CLI from its application or run LM Studio's CLI bootstrap procedure, then open a new terminal.

Thinking is intentionally enabled for every request and cannot be switched off by a run option. The fixed inference settings are temperature `0.6`, top-p `0.95`, maximum completion tokens `1200`, and context length `8192`.

## Run the simulated-user baseline

The included `runs/run-01` through `runs/run-05` are the submitted baseline outputs. To reproduce and replace them:

```powershell
Set-Location path\to\rule-change-test-package
.\run_all_local.ps1 -Force
```

Omit `-Force` if you want the script to protect the included outputs. Every episode starts in a fresh Python process with the same system prompt, scripted opening, and empty conversation history.

For an independent demonstration that preserves the submitted outputs, run:

```powershell
.\run_reproduction_local.ps1
```

Each run produces at least the assignment-required files:

- `trajectory.json`: timestamped messages and model usage
- `reward.json`: named objective metrics
- `config.json`: mode, model, quantization, and inference settings

It also produces recovery and audit files when the test is rerun.

## Run human-user mode

Use a unique identifier that contains only letters, numbers, underscores, or hyphens:

```powershell
.\run_human_local.ps1 -ParticipantId P01
```

The participant receives the same environment and task, chats through the `Knight>` prompt, and then completes the terminal survey. Type `/quit` to end before the 15-turn maximum. The run is saved under `runs/user-P01` with survey answers and a copy of the interview-notes template.

## Optional Docker path

Docker files and launchers are included because the assignment recommends a resettable container. LM Studio remains an external local service; it is not placed in the image.

For Docker Desktop, enable LM Studio's local-network serving so the container can reach `host.docker.internal:1234`, then use:

```powershell
.\setup_lmstudio.ps1 -DockerAccess
```

After setup, run:

```powershell
.\run_all.ps1 -Force
.\run_human.ps1 -ParticipantId P01
```

On Bash-capable systems, the equivalents are `./run_all.sh --force` and `./run_human.sh P01`.

## Test definition

- `troll_system_prompt.md`: authoritative NPC rules and fixed riddle
- `troll_opening.txt`: fixed assistant opening placed before the first player turn
- `simulated_user_script.txt`: seven-message role-reversal attack
- `game.py`: common simulated and human environment
- `make_outputs.py`: deterministic objective scoring and output generation
- `participant_briefing.md`: human-user task protocol
- `survey_questions.json`, `survey.py`, and `interview_notes_template.md`: subjective-metric probes

The proposed watchdog agent can be compared directly by replacing or wrapping `ask_troll()` in `game.py` while leaving the task, user script, initial state, and scorer unchanged.

## External and mocked systems

LM Studio and the downloaded Qwen model are the only external systems. The bridge, movement, roles, duel, and passage outcome are represented locally in the prompt and transcript. No real external action occurs, and player claims are deliberately unverified because accepting them is the control breakdown under test.

## Submission items not in this folder

The assignment also requires items that are not runnable environment files and still need to be completed separately:

- the final written report/document, including rejected variants and the team's shared metrics
- the independent teammate's setup-and-run video
- the final note naming the creator and independent tester

Those deliverables should link to or accompany this repository; they should not replace it.
