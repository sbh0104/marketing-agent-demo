# Human checks

## Rules — read this block before editing an entry

- rules version: HC1 2026-10-10
- **What lives here:** only the items of the route's last verdict doc's `## Human checks`
  section (`.adw/ship-report.md`, or `.adw/ui-validate.md` on the UI route) — the checks a
  person owes after the merge. It is not the smoke bucket and not the backlog: no machine
  picks an entry up as work.
- **Two owners.** Everything **above** `## Entries` is the template's: `install.sh --force`
  refreshes this block on every install. Everything **below** `## Entries` is the project's
  and no installer ever touches it.
- **Who writes:** only the landing hand (`lane.py`, at landing, under the registry lock, from
  the home tree) appends entries. Ids are `H-###`, three digits, monotonic, never reused — one
  above the highest in the home tree or the lane copy. A person edits only an entry's
  `- status:` line.
- **Entry shape** (indented two spaces here so it is not an entry):

  ### H-000 — <todo>
  - project: <project>
  - when: <YYYY-MM-DD> · <tracker ref or branch>
  - from: <doc> § Human checks — <from text>
  - source: <phase branch>
  - tag: plain | sensitive: <kind> | sensitive: <kind> · confirmed <date>
  - status: open | confirmed | done | dropped

- **Status meanings:** `open` — owed after the merge · `confirmed` — confirmed before the
  merge in the interview · `done` · `dropped`. Only a person moves `open` to `done` or
  `dropped`.

## Entries

