# VAANI V2 — Agent Instructions

## Project Identity

VAANI V2 is a transparent, evidence-grounded voice authenticity analysis system. It uses multi-signal analysis (VAANI fusion head + independent anti-spoofing signal), deterministic ensemble logic, reference evidence retrieval, and a deterministic explanation engine. No generative LLM is involved.

Repository: `vaani-voice-authenticity/`

## V2 Objective

Replace the V1 single-model, single-score, LLM-dependent prototype with a materially stronger multi-signal system that runs at ₹0/$0 ongoing cost on Oracle Always Free Ampere A1 (backend) + Cloudflare Pages (frontend).

## Source-of-Truth Hierarchy

Use these in order for implementation decisions:

1. `AGENTS.md` (this file)
2. `README.md` — current architecture, setup, and deployment
3. Actual repository behavior (inspect code before assuming)
4. General engineering judgment

When documents conflict with the repository:
- Inspect the repository
- Determine whether the document or the code is stale
- Do not invent a third architecture
- For genuine conflicts in scope, model selection, dataset, evaluation, licensing, deployment, or architecture: **STOP and flag before deciding**

## Implementation Behavior

- Match the project's existing conventions. Verify a library is already used in the project before employing it.
- Prefer editing existing files over creating new ones. Make the fewest changes that address the request.
- Verify non-trivial changes by running the project's typecheck and relevant tests.
- Use `write_todos` to plan and track multi-step tasks.
- Keep responses short and concise for terminal display.
- Don't run destructive or hard-to-undo commands unless the user explicitly asks.

## Skill-Selection Workflow

Before every non-trivial task:

1. Read this file (AGENTS.md).
2. Identify which installed skills are relevant to the task.
3. Read the corresponding skill instructions before using those skills.
4. Use the selected skills when they materially improve the task.
5. Do not use skills merely to claim that a skill was used.
6. Verify the result before declaring the task complete.

## Verification Requirements

Every phase must have:
- Objective
- Implementation
- Verification (actual commands/checks run)
- Definition of done

A phase is NOT complete because files changed. A phase is complete only when:
- The intended behavior works
- Relevant tests/checks were actually run
- Failures are resolved or explicitly documented
- The result matches the source of truth

## Git Safety Rules

Before touching code:
- Inspect `git status`
- Inspect current branch
- Inspect existing uncommitted changes
- Preserve unrelated user work
- Do not reset, hard reset, or rewrite history
- Do not delete user work without explicit project justification
- Do not commit unless explicitly asked
- Keep V2 implementation focused

## Scope-Control Rules

- Change only what the current phase requires.
- Preserve working code unless V2 explicitly replaces it.
- Do not rewrite unrelated files.
- Do not perform cosmetic refactors during unrelated work.
- Remove dead code created by your change.
- Keep the diff understandable.
- Do not add speculative abstractions, unnecessary classes, frameworks, services, configurability, or premature performance infrastructure.

## Uncertainty/Escalation Rules

| Type | Meaning | Action |
|---|---|---|
| **A — Implementation detail** | Variable names, file layout within approved folders | Decide independently |
| **B — Missing documentation** | Answer exists at authoritative source but wasn't confirmed | Research the source before writing code |
| **C — Technical incompatibility** | Two sources conflict, or approved choice doesn't work | Investigate empirically, document resolution |
| **D — Product/scope decision** | Would change what V2 is or does | **STOP and report** |
| **E — Licensing/privacy/security** | Real legal, privacy, or safety concern | **STOP and report** |
| **F — Evaluation methodology** | Would change VAANI's reliability claims | **STOP and report** |

## Coding Quality Rules (Karpathy-Style Default)

### Think Before Coding
- Understand the code path before modifying it.
- Trace dependencies rather than guessing.
- Prefer evidence over intuition.
- Push back on unnecessary complexity.

### Simplicity First
- Smallest correct solution
- Straightforward control flow
- Minimal dependencies
- Explicit interfaces
- Readable code over clever code

### Surgical Changes
- Only change what the current phase requires.
- Remove dead code created by your change.
- Keep diffs focused and understandable.

## Global Non-Negotiables

- **No generative LLM** is part of V2. No remote or local LLM for inference or explanation.
- **₹0/$0 ongoing cost** for low-volume public deployment. No paid APIs, databases, vector stores, or inference services.
- **Multi-signal analysis** — VAANI signal + independent second signal. Never reduce to a single model.
- **Evidence is comparable reference, NOT proof.** This applies everywhere: code, schemas, UI, docs, comments.
- **Never tune on test data.** Never leak speakers. Never mix reference speakers into test.
- **Never fabricate reliability numbers.** Honest metrics only, from the evaluation pipeline.
- **Never log raw user audio.** Log feature values (numbers), not waveforms.
- **Never commit credentials.** No vendor cloud keys, no paid-API credentials.
