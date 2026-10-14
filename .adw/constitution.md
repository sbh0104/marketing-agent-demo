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
   A caught line that says where text from outside — YouTube, jev, Claude, or a
   file a person edits — ends up (only here · never there) is a **flow promise**.
   Its paired test marks the boundary, not a list: every text field the fakes of
   those services return carries a marker, fields the sentence never names
   included. A field the code accepts only in a fixed shape (a video id) gets a
   marker in that shape (`MRK…`); only a field the code turns into a number, date
   or boolean goes unmarked, named with that reason.
   - **plan** — every such line `.adw/plan.md` writes is paired in `## Test plan`:
     `Promise: "<first words>" → tests/<file>::<test>` or
     `Promise: "<first words>" → not a promise: <why>`. The test lives in the
     suite, never only in `.adw/verify.sh`. The step that writes the line says:
     "paired test red while the code matches this plan → plan-miss: narrow the
     sentence to what the code does".
     A flow promise's pair line ends with its tag:
     `[boundary: <fakes> — unmarked: <field> <number|date|boolean> · …]`.
   - **implement** — such a red is a `plan-miss`: narrow the sentence through
     `.adw/plan-repairs.md`. Never change code to make a sentence true.
   - **verify-plan** — sweep the diff's added or changed contract lines for the
     four words; each caught line gets one `## Checks` line:
     `Promise: L<n> — test <name>` · `Promise: L<n> — V<m>` ·
     `Promise: L<n> — not a promise: <why>`. A `V<m>` row ends
     `— red: narrow the sentence to the measured behavior (constitution 9), not
     drift`, so verify-run, which does not read this file, takes it as a bounded fix.
     A caught flow promise whose pair line has no tag, or whose test leaves a text
     field of its fakes unmarked, gets `Promise: L<n> — V<m>`, where `V<m>` runs the
     code with every text field those fakes return marked; it ends the same way.
   - **ship-check** — each narrowed sentence (a plan-repairs entry or a verify-run
     fix) goes under `## Risks` with its original wording, not `## Human checks`.
     Widening a promise — changing code so a broader sentence holds — is a
     decision and stays with a person.
10. **Work handed to a later phase travels through `.adw/human-checks.md`, and the
    receiving phase pulls it.** An entry whose `status:` is `open` and whose
    `### H-###` title names `Phase N` as a word (no digit or letter right after it, so
    `Phase 1` never matches `Phase 1A`) is inherited by Phase N. Phase cycles only;
    smoke sweeps are exempt. Entry statuses stay a person's edit (the ledger's rules).
   - **understand** — copy every inherited entry into `.adw/notes.md` under
     `## Inherited`, one line `H-### — <title>`, or write `## Inherited: none`.
   - **plan** — `## Out of scope` closes every inherited entry with one line:
     `- Inherited H-###: step <n>` (done here) ·
     `- Inherited H-###: settled — <tracker or contract cite>` (already decided, or a
     person's check that is not this cycle's work) ·
     `- Inherited H-###: → Phase M — <why>` · `- Inherited H-###: → human — <why>`.
     A plan never accepts an inherited risk on its own. Work this plan hands to a
     later phase is `- Handed to Phase M: <what>`; when the contract already assigns
     it, `- Handed to Phase M (contract: <section title>): <what>`.
   - **ship-check** — count: every `## Inherited` line in notes.md has its
     `Inherited H-###` line in plan.md. Into `## Human checks`, one line each: every
     `→ Phase M` and every `Handed to Phase M:` line without `(contract: …)` — the
     todo names `Phase M` by number, never "the next phase"; every `→ human` and
     every uncounted entry — the todo asks the person to accept it or name an owner.
     A `(contract: …)` line is checked: the titled section names `Phase M`, else it
     is carried like a bare line. A hand-off ship-check finds on its own also names
     its receiving phase by number. Never write a Human checks line only to close an
     entry — landing turns every line into a new entry.
11. **An accepted ship-check risk is written as a site, an input class and a
    consequence; the inputs that reproduced it are examples, never its boundary.**
    Until the upstream harness carries this rule (ADWS backlog line
    `marketing-agent-demo E-021 이관`), it lives here.
   - **deep-interview** (and any session writing a tracker `Trade-offs accepted` line
     for a ship-check finding) — the line names the code site (`file:function` and the
     handling line, e.g. `src/agent/youtube.py:245` `except`), the input class ("a
     broken or tampered Google response") and the consequence ("the cycle ends without
     its `ERROR` line"), then `examples: …` for the reproduced inputs. A line a later
     finding re-opens is rewritten into this shape, never extended input by input;
     older lines stay as they are until then.
   - **ship-check** — a finding that matches an accepted line on all three (same site,
     same input class, same consequence) is that line's new example: list it under
     `## Risks` citing the line, never `## Human checks`; it blocks nothing. Same site
     or same input class with a different consequence is a new risk, and so is a
     finding whose consequence is unclear to be the same.
12. **A list judge is tried with the near-miss shapes outside its list; every sample's
    color comes from a tracker line, never from the writer's own judgment.** Until the
    upstream harness carries this rule (ADWS backlog line
    `marketing-agent-demo E-022 이관`), it lives here.
    A **list judge** is code a phase adds or changes that accepts or rejects text a
    person or the outside wrote (a web address, a config value, a document another lane
    wrote) by matching it against an enumerated set of shapes — a regex, a list of
    names, characters or paths, a Unicode category or name set. Allow-lists count, and
    so do judges inside `tests/`. Comparisons between values this code produced, and
    `except` tuples (article 11), do not. Code no phase edits is out of scope until one
    does. A **near-miss sample** is an input one edit away from a listed shape — case,
    spacing or leading whitespace, punctuation dropped or swapped, a look-alike or
    full-width character, a sibling the list left out (another browser channel's
    folder) — and, for an allow-list, a normal input it might wrongly refuse. Each
    sample gets one color and one cite:
    `red — <tracker line>` when a decision's reason names the mistake this shape makes
    (it must be refused, or the test must fail) · `green — <tracker line>` when a
    decision or a `Trade-offs accepted` line names this shape as passing ·
    `undecided — <why>` when neither does.
   - **plan** — for every list judge `.adw/plan.md` writes, `## Test plan` carries one
     line per sample: `Near-miss: <file>::<judge> — "<sample>" → red — <cite>`,
     `→ green — <cite>` or `→ undecided — <why>`, at least one sample for each edit
     kind above that applies. Red and green samples are suite tests, never only
     `.adw/verify.sh`. The step that writes the judge says: "a red sample that passes
     is a code miss in this step".
   - **implement** — write the red and green samples as suite tests before the judge;
     a red sample that passes is fixed in code, except in a sensitive area, where the
     step stops as it does today.
   - **verify-plan** — sweep the diff for list judges the plan did not sample; each
     gets its samples as `## Checks` lines in the same shape, and every red line ends
     `— red sample passes: code miss — bounded fix with a failing suite test first;
     sensitive area: stop (constitution 12)`, since verify-run does not read this
     file. Property-based is never `N/A` for a diff that holds a list judge; it
     cites these lines.
   - **ship-check** — count: every list judge in the diff has samples (plan or
     verify-plan); a judge with none is a `## Risks` line. Check that each cite
     carries the color it is given; one that does not is a `## Risks` line. Every
     `undecided` sample goes into `## Human checks`, one line per judge listing its
     samples, asking the person for the colors — the answer is a tracker decision.

## Never

- Refactors or file moves that were not requested
- Outward-facing actions without approval (deploy, push, external sends). Under
  this project's autonomy setting (`gates: auto`), finalize's push/PR after an
  auto-approved `gate-ship` carries approval the human placed in advance; any
  outward action without such an approval record is still never.
- Reporting "done" while skipping verification
