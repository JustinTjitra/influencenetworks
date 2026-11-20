# How work is split and run

The project is cut into small tasks so that a fault can be traced to one task and one
commit. Each task has a brief in this folder. `BOARD.md` is the single record of status.

## The board

`BOARD.md` holds one markdown table with exactly these columns:

| column | meaning |
|---|---|
| `id` | `T` or `U` plus two digits. `T` tasks are for the loop; `U` items are for the owner. |
| `title` | short imperative title |
| `tier` | `haiku`, `sonnet` (cheaper coding models), `planner` (the session's own model) or `owner` (`U` rows) |
| `depends` | ids that must be `done` first, separated by spaces, or `-` |
| `status` | `todo`, `doing`, `done`, `failed`, or `blocked:<who or what>` |

Every `T` row has a brief named `<id>-<slug>.md` in this folder. `U` rows have none; they
are explained in `docs/PROJECT_PLAN.md`. The next task is the first `todo` row, in table
order, whose dependencies are all `done`.

## A brief

Each brief has these sections, in this order: **Goal**, **Read first**, **Files you may
create or edit**, **Specification**, **Acceptance**, **Out of scope**. A coder gets
nothing but `CLAUDE.md` and the brief, so the brief must be complete on its own.

## One run of the loop

1. `git pull --ff-only origin main`, then `pytest -q`. If tests fail on a clean checkout,
   stop: write what failed in today's log, push the log, and do nothing else.
2. `python tools/taskboard.py next`. If it prints nothing, go to step 8.
3. Set the task to `doing` (`python tools/taskboard.py set <id> doing`).
4. **Delegate.** Start one coder with the Agent tool, `model` set to the brief's tier
   (`haiku` or `sonnet`). Its prompt: read `CLAUDE.md` and the brief at its path, do
   exactly that task, edit only the files the brief allows, run the acceptance command,
   and report what changed and the command's output. For a `planner` task, do it yourself.
5. **Verify independently.** Run the brief's acceptance command, `pytest -q`,
   `python tools/taskboard.py validate` and `python tools/guard.py` yourself. Read the
   diff: only allowed files, nothing judgemental, no price data, no secrets.
6. **Pass:** set the task `done`, commit everything for the task in one commit
   (`<id>: <title>`), push.
   **Fail:** send the coder the failure once and re-verify. If it fails again, either fix
   it yourself if the fix is small, or discard the changes (`git checkout -- . && git
   clean -fd` limited to the task's files), set the task `failed`, and record why in the
   log so the owner or a later planner can rewrite the brief.
7. Repeat from step 2, at most **three tasks per run**.
8. Append to `tasks/log/<YYYY-MM-DD>.md`: tasks done or failed, commits, anything the
   owner must decide. Commit and push the log.
9. If no `todo` task is unblocked, pause the schedule (the scheduled task's own
   `update_trigger` with `enabled=false`) and say in the log what would unblock it.

## Rules for the loop

- Never touch a path in `tasks/PROTECTED.txt`. Proposed changes to those go under
  `proposals/` as files for the owner to review.
- Never download or look at prices (see `CLAUDE.md`).
- Never mark a task `done` on the coder's word. Only on your own run of the checks.
- New work the planner discovers becomes a new row and a new brief, small enough for one
  commit. Splitting a task that turned out too big is the planner's job.
- Web research: plan searches before spending them; record sources and what could not be
  verified. Snippet-level evidence is labelled as such.
