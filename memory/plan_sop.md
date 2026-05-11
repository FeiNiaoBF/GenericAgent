# Official Plan Mode SOP

**Trigger**: `/plan <goal>` starts planning-only mode.
**Purpose**: explore, clarify, and produce an implementation-ready plan. Do not execute the plan.

## Core Rules
1. Plan mode is read-only. Do not modify files, run formatters, run migrations, or perform irreversible actions.
2. Ground in the local environment first using read-only inspection.
3. Ask the user only for high-impact decisions that cannot be discovered from the repo.
4. Final output must contain exactly one `<proposed_plan>` block.
5. The plan must be decision-complete enough for another engineer or agent to implement immediately.

## Allowed During Planning
- `file_read` for source/config/docs inspection.
- `web_scan` for read-only page inspection.
- `code_run` only for non-mutating checks or static probes.
- `ask_user` for product decisions, constraints, or ambiguous tradeoffs.
- `update_working_checkpoint` for long planning context.

## Blocked During Planning
- `file_patch`
- `file_write`
- `web_execute_js`
- `start_long_term_update`
- Any command whose purpose is implementation rather than planning.

## Final Plan Shape
```markdown
<proposed_plan>
# Title

## Summary
...

## Key Changes
...

## Public Interfaces
...

## Test Plan
...

## Assumptions
...
</proposed_plan>
```

## Commands
- `/plan <goal>`: start planning-only mode.
- `/plan status`: show current scope state.
- `/plan show`: show latest proposed plan.
- `/plan exit`: exit current scope planning state.
