---
name: docit
description: Write or rewrite SEMGIA documentation so a human can follow it step by step - chronological, logically structured, precise, as short as possible, technically exact. Use when the user types /docit <file or topic>, or asks to document something (README parts, PROTOCOL.md, DECISIONS.md, QUALITY-REPORT.md, how-tos, folder docs).
argument-hint: "<file or topic to document>"
---

# /docit: documentation a human can follow

Credo: **as much as necessary, as little as possible.** Every sentence must help the reader do or understand
something. Technically exact, never vague.

## Before writing
1. Find the reader and the job: teammate running a command? professor checking Report 1? outsider repeating the
   recording? One doc = one reader + one job.
2. Get the facts from the source, not from memory: the code (`semgia/config.py` for every number), the data,
   `MEMORY.md`, `docs/course/requirements.md`. Never invent a number, a result or a decision. Unknown → write
   `TODO(owner): …` and list it at the end of your reply.
3. Course deliverables: follow the required names/parts in `docs/course/report1_assignment.md` and the style of
   `docs/course/example_repo.md`, but **never copy its wording or values** (that gets the report returned).

## Structure
- Title, then one sentence: what this is and who it's for.
- Order = the order the reader acts or thinks: **why → what you need → steps in time order → result / check → if it fails**.
- Numbered steps for actions, one action per step, with the exact command in a code block and what you should see.
- Tables for facts that compare (settings, columns, files, owners). Lists only for real lists.
- One idea per paragraph, max ~3 lines. Headings that say what's inside ("Clean the skin", not "Preparation stuff").
- Link instead of repeating: one fact lives in one place.

## Language
- Plain English, short sentences, active voice, present tense. Define each technical term once, at first use.
- **Numbers, not adjectives:** "8 s", "24 000 rows", "20–450 Hz, 4th-order Butterworth", not "short", "many", "standard".
- Units always. Names of files, columns, functions in `code`.
- No marketing words, no filler ("simply", "just", "robust solution"), no emojis.
- Course files: "Evidence:" line at the end of each README part; DECISIONS.md parts as Chose / Reason / Not understood yet / Source.
- Privacy: codes only (P001, E01, M01), never names or faces.

## Personal course texts
`rationale/Mxx.md` and "the reason, in our own words" must be the member's **own** words (course rule). For those: ask
the member for their points, then only structure and tighten them. Don't write their opinion for them.

## Finish
Re-read as the reader: can they follow it top to bottom without asking anyone? Cut every sentence that fails
that test. Check that every number matches the source. Report what you wrote and the open TODOs.
