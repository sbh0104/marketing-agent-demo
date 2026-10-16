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
     Like every other row it also carries article 13's tail, so the measurement
     lands in the suite instead of leaving with `.adw/verify.sh`.
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
13. **A check that measures shipped code outlives the cycle.** Until the upstream
    harness carries this rule (ADWS backlog line `marketing-agent-demo E-057 이관`),
    it lives here. `.adw/verify.sh` is untracked and gone when the cycle ends, and
    ship-check's mutation spot-check runs only the suite, so a behavior only a `V<n>`
    row measured ships unlocked and returns as a "move it to the suite" smoke item
    (1C S-058 · 6E S-091 · 7 S-098 · 7C S-119). Every cycle, smoke sweeps included.
   - **verify-plan** — every `## Checks` row but V1 (the suite) ends with exactly one
     tail: `— green: port to tests/<file> (<what the test asserts>)` or
     `— probe only: <reason>`, the reason one of `base commit` · `other interpreter` ·
     `real process` · `real network` · `real Chrome` · `this diff` · `harness tool`.
     A row that drives the project's code through fakes, or reads a tracked file the
     suite can read, is a port; article 9's `Promise: L<n> — V<m>` row included.
     A row that only runs mutants registered in `tests/mutants.py`
     (`python3 -m tests.mutants <name>`) ends `— kept: tests/mutants.py (<names>)`
     instead: the registry is tracked, so the check already outlives the cycle
     (article 14); a row that measures anything else as well cannot use it.
     verify-run does not read this file, so `## Checks` opens with this paragraph,
     verbatim:
     `Port rule (constitution 13): after a "green: port to" row is green, write its
     assertions as a suite test in the named file and commit it alone (test files
     only). A port is not a fix and spends no cap. Port red → fix the test only,
     once; still red, or the suite cannot hold it → revert that commit and write
     "not ported: V<n> — <why>" under the report's checks; the verdict follows the
     probe. After the last port, run V1 again on the final tree and record it.`
   - **verify-run** — follows the port rule as `## Checks` states it.
   - **ship-check** — count: every row but V1 has one tail with a listed reason, or a
     `kept:` tail whose names are all in the committed `tests/mutants.py`; a missing
     tail, an unlisted reason or an unregistered name is a `## Test integrity`
     finding. Every port row has its test in the diff or a `not ported:` line in
     verify-report; each
     `not ported:` line becomes one `### S-NEW-<n>` smoke item under the usual
     deferral conditions. The mutation spot-check aims one mutant at what each ported
     test claims to hold; a ported test that stays green under it is a
     `## Test integrity` finding.
14. **A guard's boundary is moved one step each way, and both moves turn the suite
    red.** Until the upstream harness carries this rule (ADWS backlog line
    `marketing-agent-demo E-041 이관`), it lives here. Plans registered one mutant per
    comparison, so the other side shipped unmeasured and came back as a smoke item:
    6C `2 * grade_errors > graded` (`>=` caught, `> graded + 1` green) · 6C
    `self.popular < …popular_drafts_min` (`<=` green) · 6D `raised > 1` (`>= 1.5`
    caught, `>= 1` green) · 6E `range(found, found + len(word))` (both ends green) —
    S-077 · S-087 · S-088.
    A **boundary** is a size comparison (`<` · `<=` · `>` · `>=`) or a range or slice
    end (`range(a, b)` · `x[a:b]`) on a line the diff adds or changes, inside a judge
    the `Guard reach` row of `.claude/skills/verify-plan/references/test-taxonomy.md`
    applies to — cite its applies-clause, never restate it; judges inside `tests/`
    count. Comparisons outside such a judge are out of scope (ship-check's spot-check
    still samples them). Phase cycles and smoke sweeps alike.
    Each boundary gets two mutants: the **flip** (`>`↔`>=`, `<`↔`<=`) and the
    **shift**, the compared value moved one unit `u` the other way (`x >= k` →
    `x > k` · `x >= k - u`; `x > k` → `x >= k` · `x > k + u`); a range or slice end
    gets one move inward and one outward by 1. `u` is the smallest step the value
    takes — 1 for counts and positions, 0.01 for probabilities and scores, the
    config's own unit for durations — and is written beside the boundary. A float
    shift is run once against its sample before it counts (`1 − 0.9` is
    `0.0999…98`, `src/agent/writer.py:145`).
    A mutant that cannot serve is skipped with one of two reasons, never another:
    `no mutant: hangs — <the loop>` (the move makes a loop never end:
    `while found >= 0` → `>= -1`) ·
    `no mutant: same result — <why no input reaches the moved side>`.
    The boundary's other mutant is still registered.
   - **plan** — `## Test plan` carries one line per boundary:
     `Boundary: <file>::<judge> "<comparison>" (u <unit>) → <flip name> · <shift name>`,
     a skipped mutant written as its `no mutant:` reason in place of its name; the
     guard matrix's mutation row names the same mutants. The step that writes the
     judge says: "both boundary mutants are registered in tests/mutants.py and caught
     by a sample at the boundary and one unit past it, in this step".
   - **implement** — register both mutants and write their samples as suite tests in
     the judge's step. A boundary mutant that stays green is a missing sample in that
     step: add the test, never change code to kill it. A sample that shows the code
     contradicting a tracker decision is a code miss, except in a sensitive area,
     where the step stops as it does today.
   - **verify-plan** — match the diff's boundaries against the plan's `Boundary:`
     lines. Each boundary with neither two registered mutants nor a listed reason
     gets one `## Checks` row naming its two mutants (anchor → replacement), ending
     `— kept: tests/mutants.py (<names>)` (article 13). verify-run does not read this
     file, so when such a row exists `## Checks` opens with this paragraph, verbatim:
     `Boundary rule (constitution 14): for a row that names boundary mutants, register
     each in tests/mutants.py and run it. A mutant that stays green gets a suite test
     at the boundary and one unit past it; commit the registry entry and the test
     alone (test files only). This is not a fix and spends no cap. Still green after
     one more test-only try → revert that commit and write "not locked: <mutant> —
     <why>" under the report's checks. After the last such commit, run V1 again on the
     final tree and record it.`
   - **verify-run** — follows the boundary rule as `## Checks` states it.
   - **ship-check** — count: every boundary in the diff has two mutants in the
     committed `tests/mutants.py`, or one and a listed `no mutant:` reason; a missing
     mutant or an unlisted reason is a `## Test integrity` finding. Each
     `not locked:` line becomes one `### S-NEW-<n>` smoke item under the usual
     deferral conditions. When the diff has a `same result` reason, the mutation
     spot-check plants one such mutant; one that turns a test red or changes an
     output is a `## Test integrity` finding.

## Never

- Refactors or file moves that were not requested
- Outward-facing actions without approval (deploy, push, external sends). Under
  this project's autonomy setting (`gates: auto`), finalize's push/PR after an
  auto-approved `gate-ship` carries approval the human placed in advance; any
  outward action without such an approval record is still never.
- Reporting "done" while skipping verification
