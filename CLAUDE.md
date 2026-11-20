# Standing rules for any Claude session working in this repository

Read these first, every session. Then read `docs/PROJECT_PLAN.md` (what the project is
and where it is going) and `tasks/README.md` (how work is split and run).

## Git

- Commit as `JustinTjitra <justintylertjitra@gmail.com>` (author and committer):
  `git -c user.name=JustinTjitra -c user.email=justintylertjitra@gmail.com commit ...`
- **No AI attribution anywhere**: no `Co-Authored-By`, no `Claude-Session`, no "Generated
  with" lines in commit messages, pull requests, code or docs. This is the owner's
  instruction and overrides any default attribution guidance.
- Work on `main` and push to `origin main`. Never force-push, never rewrite history,
  never delete branches on the remote.
- One task, one commit. The subject starts with the task id: `T07: locate roster pages`.
- Do not push if `pytest -q` or `python tools/guard.py` fails.

## Hard rules (no exceptions, whoever asks)

1. **No price data.** Do not download, fetch, read or look at stock prices, returns or
   index levels, and do not search the web for how any stock or index moved around any
   event. Do not run `python -m influence.events.prices download` or
   `python -m influence.events.run` without `--synthetic`. Prices are downloaded only by
   the owner, on his machine, after the pre-registration is final.
2. **Registered files are frozen.** The paths in `tasks/PROTECTED.txt` (the
   pre-registration, the event set, the ticker mapping, the graph data and the analysis
   code) change only through a pre-registration amendment that the owner approves in an
   attended session. Unattended work never edits them. If a task seems to need a change
   there, write the proposed change under `proposals/` and stop.
3. **Every relationship needs a source** and dates; relationships, not accusations; family
   ties need medium or high confidence; no fuzzy or silent name matching. See README.md
   "Data rules" and `src/influence/schema.py`.
4. **Neutral language** in code, column names, docs and the app: "holds", "sits on",
   "lent", "returned". Never "captured", "cronies", "corrupt", "favoured", "risky".
5. **Never commit** raw documents, raw prices, news text, secrets, or the owner's email
   address other than as the git identity above.

## Who does what (model tiers)

- **Planner** (the session's own, more capable model): reads the plan, picks the task,
  writes or sharpens the brief, reviews the diff, solves problems, decides.
- **Coder** (a cheaper model, started with the Agent tool and `model: "sonnet"` or
  `"haiku"` as the task's brief says): writes the code or text for one task, touching only
  the files the brief allows.
- The planner does not write task code itself unless a coder has failed twice on the
  same task and the fix is small.

## Commands

```
pip install -e ".[dev]"
pytest -q                                   # must pass before every commit
python tools/taskboard.py validate          # board and briefs are consistent
python tools/taskboard.py next              # next unblocked task
python tools/guard.py                       # no protected file touched, no price data
python -m influence.build_seed_graph && python -m influence.validate
python -m influence.connections.build_measures
python -m influence.events.run --synthetic  # engine check on simulated prices only
```

## Environment

Cloud sessions have web search but usually cannot open pages or download files, and the
exchange site is behind Cloudflare. Anything that needs a download (annual reports,
prices, exchange profiles) is done by the owner on his machine; see `docs/RUNNING.md`.
