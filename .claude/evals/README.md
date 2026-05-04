# Evals

Eval-driven development scaffolding for jre-vidget.

## What are evals?

An eval is a test that measures whether an agent-assisted workflow produces
correct output — typically for subjective or complex tasks that regular unit
tests don't cover well. Examples for this project:

- Does `vidget preview` return accurate metadata for a given YouTube URL?
- Does `vidget download --publish` produce a correct YouTube title + description?
- Does the SetupWizard correctly detect missing secrets vs. placeholder values?

## When to write an eval

Write an eval when:
- A new phase adds agent-assisted logic (metadata parsing, publish flow)
- A bug is found in output quality rather than code correctness
- A change could silently regress model-sensitive behaviour

## Directory structure

```
.claude/evals/
├── README.md          ← this file
├── preview/           ← evals for vidget preview command
├── publish/           ← evals for vidget download --publish
└── web-ui/            ← evals for SetupWizard and web UI flows
```

Each eval directory contains:
- `inputs/`   — sample inputs (URLs, mock API responses, fixture files)
- `expected/` — expected outputs or scoring criteria
- `run.sh`    — script to execute the eval set

## Running evals

```bash
# Run all evals
bash .claude/evals/run.sh

# Run a specific eval set
bash .claude/evals/preview/run.sh
```

Evals are not part of `uv run pytest` — they run separately and may require
real network access or YouTube credentials.
