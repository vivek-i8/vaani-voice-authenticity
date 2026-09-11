# VAANI V2 Agent Instructions

## Project identity

VAANI is a voice authenticity analysis service on the `main` branch. Two independent signals (a project-trained fusion head and the published Spectra-AASIST3 model) are combined by a deterministic rule table. Explanations are deterministic. No generative LLM is involved anywhere in V2.

## Repository map

- `app/` FastAPI backend: `app/api/` endpoints, `app/ml/` inference and training pipeline, `app/explainability/` deterministic explanation engine
- `frontend/` React 19 + TypeScript + Vite client
- `models/vaani_model/` tracked model artifacts: fusion head weights, scaler, metadata, evaluation report, reference index
- `data/splits/` committed speaker-disjoint dataset split
- `datasets/README.md` dataset download, licensing, and preparation
- `tests/` pytest suite

## Source of truth

Use this order for implementation decisions:

1. `AGENTS.md` (this file)
2. `README.md`
3. Actual repository behavior

When a document conflicts with the code, inspect the code and decide which source is stale. Do not invent a third architecture. For conflicts in scope, model selection, dataset, evaluation, or licensing, stop and flag before deciding.

## Implementation behavior

- Match the project's existing conventions. Verify a library is already used before employing it.
- Prefer editing existing files over creating new ones. Make the fewest changes that address the request.
- Verify non-trivial changes by running the project's typecheck and relevant tests.
- Keep responses short and concise for terminal display.
- Do not run destructive or hard-to-undo commands unless the user explicitly asks.

## Git safety rules

Before touching code: inspect `git status`, the current branch, and existing uncommitted changes. Preserve unrelated user work. Do not reset, rebase, or rewrite history. Do not delete user work without explicit justification. Do not commit or push unless explicitly asked.

`main` is V2. `v1-legacy` preserves the retired V1 implementation and must stay untouched.

## Scope control

- Change only what the current task requires.
- Preserve working code unless the task explicitly replaces it.
- Do not rewrite unrelated files and do not perform cosmetic refactors during unrelated work.
- Remove dead code created by your change.
- Do not add speculative abstractions, unnecessary classes, frameworks, services, configurability, or premature performance infrastructure.

## Non-negotiables

- No generative LLM is part of V2, remote or local, for inference or explanation.
- Multi-signal analysis: VAANI signal plus an independent second signal. Never reduce to a single model.
- Evidence is comparable reference, not proof. This applies everywhere: code, schemas, UI, docs, comments.
- Never tune on test data. Never leak speakers across the split. Never mix reference speakers into test.
- Never fabricate reliability numbers. Report only metrics from the evaluation pipeline, including unfavorable ones.
- Never log raw user audio. Log feature values (numbers), not waveforms.
- Never commit credentials.
- Licensing: the project code is Apache-2.0. The In-the-Wild dataset is CC-BY-SA-4.0 and keeps its own license. Third-party models are Apache-2.0 and keep their own attribution. Do not restate third-party assets as project-licensed.

## Escalation

Stop and report instead of deciding when a change would: alter what V2 is or does (product scope), raise a legal, privacy, or security concern, or change evaluation methodology in a way that affects reliability claims.
