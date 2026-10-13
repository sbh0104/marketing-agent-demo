# Project Constitution

> Principles the ADW must always follow in this project.
> The orchestrator (`/adw-run`) and every skill read this before executing and comply.
> The lines below are examples — replace them with your rules.

## Principles

1. **Cut work small** — one verifiable change at a time.
2. **No completion without verification** — a step is done only when tests/build pass.
3. **Respect human approval points** — never pass a gate step without an approval
   record. The record's source is either a human (the gate's one-tap) or this
   project's autonomy setting (`gates: auto`), which counts as approval the human
   placed in advance; it applies to `gate-plan` and `gate-ship` only, and every
   other gate still waits for a person.
4. **Follow the existing code style** — match the surrounding conventions, naming, and
   comment density.
5. **Stop on plan/reality mismatch (drift)** — when the code cannot honor a tracked
   decision, never patch around it: stop, label it (code miss · drift · unmeasured ·
   plan-miss · verify-miss), and route per the drift protocol. The tracker is the source of truth, and
   only a human revises it.
6. **One plain command per call** — a step's Bash call is one simple command in the repo root
   (`git status`), never `git -C <path> …`, `cd … ;`, `&&`/`;` chains, heredocs, or inline
   `for`/`if`. The allow-list compares literal prefixes, so a compound shape re-asks even when
   every piece is allowed.
7. **Three doors for `.claude/` artifacts** — sorted by kind, never by count.
   `.claude/skills/**` · `.claude/agents/**` → stage under `.adw/generated/` for the hub's
   🧩 Install, always. The `permissions` block of `.claude/settings.json` → `perm_merge.py`
   only (Install's whole-file copy would truncate it). `hooks` · `env` · `model` — and
   anything under `.claude/` not named above — a human edits directly, never a plan artifact.
8. **`type: script` steps run outside the interphone — one filename, one directory** —
   a script step has no permission interphone, so `command:` is a single script
   **filename** plus its arguments, never a path and never an interpreter. The driver
   resolves that name only inside its own directory
   (`.claude/skills/plan/scripts/`) and refuses to start the cycle (`EXIT_CONFIG`)
   when the name carries a path separator, `..`, or names an interpreter.
9. **A contract promise is measured where it is written; a wrong one is narrowed,
   not escalated.** A line a phase adds to or changes in `docs/contracts.md` that
   contains 뿐 · 않 · 될 수 있 · 에만 is a promise unless the phase says why not.
   Lines no phase edits are out of scope until one does.
   - **plan** — every such line `.adw/plan.md` writes is paired in `## Test plan`:
     `Promise: "<first words>" → tests/<file>::<test>` or
     `Promise: "<first words>" → not a promise: <why>`. The test lives in the
     suite, never only in `.adw/verify.sh`. The step that writes the line says:
     "paired test red while the code matches this plan → plan-miss: narrow the
     sentence to what the code does".
   - **implement** — such a red is a `plan-miss`: narrow the sentence through
     `.adw/plan-repairs.md`. Never change code to make a sentence true.
   - **verify-plan** — sweep the diff's added or changed contract lines for the
     four words; each caught line gets one `## Checks` line:
     `Promise: L<n> — test <name>` · `Promise: L<n> — V<m>` ·
     `Promise: L<n> — not a promise: <why>`. A `V<m>` row ends
     `— red: narrow the sentence to the measured behavior (constitution 9), not
     drift`, so verify-run, which does not read this file, takes it as a bounded fix.
   - **ship-check** — each narrowed sentence (a plan-repairs entry or a verify-run
     fix) goes under `## Risks` with its original wording, not `## Human checks`.
     Widening a promise — changing code so a broader sentence holds — is a
     decision and stays with a person.

## Never

- Refactors or file moves that were not requested
- Outward-facing actions without approval (deploy, push, external sends). Under
  this project's autonomy setting (`gates: auto`), finalize's push/PR after an
  auto-approved `gate-ship` carries approval the human placed in advance; any
  outward action without such an approval record is still never.
- Reporting "done" while skipping verification
