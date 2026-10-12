# Voice — how the human-facing prose reads

Register: plain

> Change the line above — or tap **🗣 Voice** in the hub's project panel, which cycles
> `plain → standard → technical` — and every artifact written from then on follows it.
> Committed like `constitution.md` and `backlog.md`: it is this project's config, and
> `install.sh` never overwrites it.

## What this governs

Everything the ADW writes **in the user's conversation language**, and nothing else:

- interview documents (`/project-interview`, `/deep-interview`), their remote question
  pages and their kickoff pages
- the plan explainer page, and the ship explainer page
- reports — `ship-report.md`, `verify-report.md`, `debt-audit`,
  `refactor-scope`, the board memo and its page
- the chat summaries those skills print at the end

It governs **register, not content**. Nothing here licenses omitting a risk, softening a
verdict, rounding a number, or dropping evidence. A `plain` page and a `technical` page
must support the same decision; if switching register would change what the reader
decides, the register was not the problem — the writing was.

It never touches: code, comments, commit messages, tracker decisions, ADRs, `notes.md`,
`plan.md`'s step list, or anything else the repo keeps in English. Identifiers, file
paths, commands, and verdict tokens (`PASS`, `BLOCKED`, `READY WITH RISKS`, `ADVISORY`)
stay verbatim in every register — they are names, and renaming them for readability
breaks the machine that reads them next.

## Registers

### `plain` (default)

Write for someone smart who does not have the code in their head right now — which,
three weeks later, includes the person who wrote it, and on a shared page includes
someone meeting this project for the first time. Assume intelligence, assume nothing else:
no memory of last cycle, no knowledge of this repo's vocabulary, no open editor.

**`plain` is already the "explain it more simply" version.** If the reader has to answer a
page with "I don't follow — spell it out", that page failed this register; the spelled-out
page is the one that should have been published first. So the shape below is not a style
to reach for when a topic feels hard. It is the shape of every plain document — an
interview question, a plan page, a ship page, a report section — and the writer walks the
list before publishing.

#### The shape — seven parts, in this order

1. **The thing, before the question.** Name what is under discussion in everyday words,
   with one concrete picture ("the experience ledger is a notebook the retro writes one
   line in after every cycle"), and show **one real sample** of it — an actual line from
   the file, an actual file name, an actual command output — before stating any rule
   about it.
2. **The rule, and the reason as a consequence.** One sentence for how it works today
   ("the next number is the last one in the notebook plus one"), one for why that matters
   in the reader's terms ("so two facts never share a name, because other documents point
   at facts by that number").
3. **The failure or the change as a clock story.** Named actors, timestamps, one line per
   beat, the bad moment marked so the eye lands on it:
   `09:00 room A writes E-042 · 09:03 room B, not having seen A's, writes E-042 too ·
   10:00 the two are merged → two different facts called E-042`. A mechanism the reader
   can replay in their head is one they can decide about; a paragraph that only names the
   mechanism is not.
4. **What is special here** — this repo, this phase, this branch — told *after* the
   general story, never mixed into it, with the evidence in parentheses (`.gitignore:21`).
5. **Is it on fire today, and what opens the door.** "Today the rule is one cycle at a
   time, so nothing breaks; W9b-3 is the phase that lifts that rule" turns a vague worry
   into a dated debt the reader can schedule — or into an emergency they must act on now.
6. **The scale the decision is made against** — how much work is already in this phase,
   how big the file is, how often this path runs — with a comparison the reader can feel
   ("a phase is capped at one working day; the last one over the cap ran 36 hours and
   called a person six times").
7. **Every choice as three labeled lines, in this order: flow → buys → costs**
   (Korean pages: `흐름:` · `산다:` · `치릅니다:`; localize the labels, keep the order).
   *Flow* is what happens step by step if this is picked, written as a sequence; *buys*
   and *costs* are one or two sentences of consequence each. The recommendation is marked
   and the do-nothing option is one of the choices. The question itself is restated in
   everyday words ("this number clash — when, and who fixes it?"). A gate page's
   approve / reject / ask and a report's ship / hold / revert are choices too and get the
   same three lines.

Thin pages (an auto-approved gate, a one-screen report) keep all seven parts and shorten
each; they never drop 1, 3 or 7. Fewer sections is thin; a denser voice is not.

#### Word rules that hold throughout

- **Everyday word first, term of art in parentheses on its first use** — "two folders
  (worktrees)", "a lock on the notebook (a file lock)" — and the everyday word from there
  on. Never the reverse order, and never the bare term.
- **Headings are numbered steps or questions**, not topic labels: a reader who reads only
  the headings should still be able to follow the argument.
- **Short sentences carrying one idea each.** Active voice, a named actor: "`universe()`
  refuses the table", not "the table is refused".
- **Say the consequence, not just the mechanism.** "So a backtest would earn money that
  never existed" is the sentence the reader needs; "the column is computed from a future
  bar" is the one they can already see in the diff.
- **Numbers get a scale.** "1864 lines — about the size of the whole ingest package."
- **One metaphor per section**, dropped once it has done its work; a metaphor stretched
  too far starts teaching things that are not true.
- Identifiers, file paths, commands and verdict tokens stay verbatim, as the section above
  says — `plain` renames nothing the machine reads.

### `standard`

Ordinary technical prose for a reader fluent in this project. Terms of art used freely,
defined only when genuinely obscure; metaphor only where it earns its place. This is the
register these documents used before `voice.md` existed.

### `technical`

Maximum density for a reader who wants the mechanism and nothing else. Domain vocabulary
verbatim with no glossing, no metaphor, no scene-setting. Shortest form that stays
unambiguous. Choose this when the reader is reviewing rather than learning.
