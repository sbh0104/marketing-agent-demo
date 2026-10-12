# Smoke log

_The bucket for fixes that need no judgment. Made by
`plans/interview-cycle-friction.md#phase-f8`; emptied by the short route
(`.adw/workflow-smoke.yml`, Phase F9). Nothing else empties it._

## Rules — read this block before writing an entry

- rules version: F9 2026-09-05 · S2 2026-09-21 · T9 2026-09-22 · F8′ 2026-09-26 · F26-D 2026-10-04 — everything **above** `## Entries` is the template's:
  `install.sh --force` refreshes this block on every install, so the rules can never drift
  behind the skills that point at them. Everything **below** `## Entries` is the project's
  and no installer ever touches it. One file, two owners, and the line between them is that
  heading.
- **Append only.** A new item is one `### S-###` section added at the **end of this file**.
  Nothing above the last section is ever rewritten, except an existing item's own
  `- status:` and `- attempts:` lines, and a header the numbering hand settles (next rule).
- **Ids are `S-###`, three digits, monotonic, never reused.** The next id is one greater
  than the highest `S-###` that has ever appeared below `## Entries`, closed items included.
  The shape below is `S-000`, so the first real item is `S-001`.
  **Numbers are issued under the registry lock, from the home tree** — several lanes write
  this file at once (S4), so a lane's own copy never decides a number. A step inside a cycle
  (ship-check) writes a placeholder header `### S-NEW-<n>`, n one above the
  highest `S-NEW-` already here; the hand that carries the lane's copy home (`lane.py`, at
  the red verdict's immediate send, at landing, and `smoke-file` inside its own lock hold)
  gives **each placeholder header** the home tree's highest plus one and writes the number
  back into the lane's copy, so a second send appends nothing. A number that turns out to be
  taken by a different item (a different `- source:` line — in the home tree or twice in one
  copy) is never dropped: the newcomer is renumbered, and the step's result line opens with
  a `⚠` line saying so.
- **The entry criterion is judgment, not size.** An item belongs here only if its fix
  touches **none** of: a tracker decision · a public contract (verdict token · gate
  protocol · file format · CLI argument) · a sensitive area · a rule file
  (`constitution.md` · `CLAUDE.md` · `workflow*.yml` · `.claude/skills/**` ·
  `.claude/agents/**`). A mechanical 200-line rename belongs here; a one-line change to a
  gate protocol does not. **This list is defined here and nowhere else** — the skills that
  write into this file point at this block instead of restating it, because a second copy
  is a copy that drifts.
- **`- touches:` is the criterion's evidence, and it is what makes the criterion
  falsifiable.** It names every path the fix changes, so any later reader — the sweep, the
  next ship-check, a human — can re-run the criterion against the real diff instead of
  taking the writer's word for it. An item whose `- touches:` names a rule file or a
  sensitive area was never eligible: it is a finding to route, not a fix to sweep.
- **Status is one of `open` · `in-sweep` · `resolved` · `reverted` · `escalated`.** It is
  the **first token** after `- status: `; anything after a `→` is provenance, not status.
  `escalated` is an item that broke twice: it is
  **excluded from every blocking calculation** and leaves through `smoke-triage` as a
  phase-sized backlog item, so one stubborn item can never hold the whole roadmap.
  `resolved` is excluded too.
- **The blocking calculation is the driver's, not this file's.** `smoke_block` in
  `cycle_driver.py` reads the statuses written here. With lanes off, `open` and `reverted`
  **block** — the short route runs ahead of every tracker phase until the bucket clears. With
  lanes on (the default since S4) the bucket blocks nothing: a sweep runs in its own lane,
  started by the hub automatically only when `lane.max` is 2 or more, otherwise from the hub's
  🧪 button. `escalated` and `resolved` never count. This file says what a status *means*; the
  driver says what it *costs*. Nothing else gates work on these statuses.
- **`in-sweep` is written by no automated hand.** The short route leaves a swept item `open`
  until `smoke-close` gives it a final status, so a round that dies mid-sweep re-blocks on the
  next pick instead of leaking its items past the block. The status is here for a human
  marking a sweep they are running by hand; after an automated round it is a sign that
  something wrote what it shouldn't have.
- **`- attempts:` is incremented by `smoke-close` and by the short route's red end, nothing
  else.** It counts breaks, not tries: `smoke-close` raises it when it reverts the item's own
  commit, and the driver raises it when a sweep ends red with the item's commits kept on its
  sweep branch (ship `BLOCKED`, F8′). Each writes the reason on the same line
  (`last failure:`), and the next sweep reads it before writing its checks.
  **Two breaks and the item becomes `escalated`** — it leaves the
  blocking calculation and goes to a human, because an item that broke twice was never the
  small thing it claimed to be.
- **A sweep files side findings one generation deep (F8′).** An item a sweep's own
  ship-check filed carries a `- source:` line starting `sweep <cycle id>` — the driver stamps
  it right after that step. A sweep whose batch holds such an item files nothing more; its
  findings stay in its report. So a sweep can add one more sweep, never a chain of them.
- **One item never lives in two files.** An item that came from the debt ledger carries a
  `- cross-ref: S-### ← D-###` line here, and its ledger entry carries
  `- status: routed → S-###` there. While the item is here, **this file owns its status**
  and the ledger keeps only the pointer.
- **A red cycle files here instead of rewinding (S2, 2026-09-21).** `smoke-file` turns a
  verify-run `FAIL` or a ship-check `BLOCKED` into items carrying `- base: <that phase
  branch>` and `- phase: <tracker ref>`. The sweep starts its branch from `base:` (not from
  main), and when it ships, the phase ships with it and the `phase:` backlog line closes.
  Items without `base:` sweep from main as before. A batch never mixes bases.
- **A red verdict the bucket cannot carry is held, not filed (F26-D, 2026-10-04).** A BLOCKED
  or FAIL whose touches are unknown, or that the ship-report's `## Smoke candidates` section did
  not offer as a candidate (the section is there and lists none), is never written here:
  `smoke-file` names it in `.adw/smoke-filed.json` `held` with a `why` (`unknown-touches` ·
  `report-declined` · `rule-path` for a rule file) and the red end goes to a 🎤 interview.
- **A stale `- direction:` is revised, never erased (F14).** When the prescription turned out
  wrong (a later phase changed the shape of the fix), strike the old sentence and append the
  new one on the same line: `- direction: ~~old~~ (revised YYYY-MM-DD: new)`. The history
  stays readable and the sweep reads the last clause.

Entry shape — copy every line, in this order:

```text
### S-000 — <one-line title>
- source: cycle <cycle id> · tracker <tracker path>#phase-<n> · deferred by <step>
- evidence: <file:line>
- direction: <the shape of the fix, one line>
- touches: <every path the fix changes, comma-separated>
- base: <phase branch the fix must start from — omit for main>
- phase: <tracker path>#phase-<n> — the backlog line that closes when this ships; omit if none
- status: open
- attempts: 0 · last failure: —
- first seen: YYYY-MM-DD · last seen: YYYY-MM-DD
- cross-ref: S-000 ← D-000
```

The `- cross-ref:` line is written **only** when the item came from `.adw/debt.md`; every
other line is required on every item.

## Entries

<!-- New items are appended below, one `### S-###` section each, newest last. The bucket
     ships empty on purpose: the short route's invariant is "empty bucket → next phase". -->
