# AGENTS.md

TD Factory: a two agent pipeline that turns a prompt into a working TouchDesigner project.
This is the canonical instruction set for **any** coding agent (Claude Code, Codex, Cursor,
opencode, ...), not just Claude. Read `ARCHITECTURE.md` for the full model and the reasoning
behind it.

## Roles

- **Architect** writes `projects/<slug>/spec.yaml`. Never touches TouchDesigner, never calls MCP tools. Follow `.claude/skills/td-architect/SKILL.md`.
- **Builder** executes an approved `spec.yaml` against a live TD session through Envoy MCP. Follow `.claude/skills/td-builder/SKILL.md`.

Never do both roles in one session. If a session starts building without an approved spec, stop and say so.

The `.claude/` files are plain markdown. Whatever your harness, read them as documents:
`.claude/rules/00-studio-conventions.md` (always in force) and the skills `td-architect`,
`td-builder`, `td-auto-improve`. Claude Code additionally gets `/new-td-project` and
`/build-td-project` as slash commands; other agents follow the same skills directly.

## Hard rules

1. No build starts without `projects/<slug>/spec.yaml` and a passing `python scripts/validate_spec.py <slug>`.
2. Read `lib/index.yaml` before creating anything. Reuse a listed component instead of rebuilding it.
3. Never guess a parameter name. Look it up with `get_docs` or `get_parameter` first.
4. Every visual change is followed by a capture. A capture with a non `pass` quality verdict is a failure, not a step.
5. The operator budget in the spec is a hard ceiling. If a stage cannot fit, stop and report instead of overflowing.
6. `.toe` files are binary. The readable source of truth is `network/*.tdxn` plus `scripts/` and `glsl/`.
7. Any component that works and is generic gets exported to `lib/` and indexed.
8. Any error whose root cause is identified and whose fix is verified becomes a lesson in `knowledge/lessons.yaml`. Grep it before building and on every error. Protocol: `.claude/skills/td-auto-improve/SKILL.md`.

## Environment

- TouchDesigner 2025.33070+, Embody and Envoy installed in the seed project (`templates/seed.toe`).
- Envoy is a standard MCP server: any MCP capable agent can drive it, not just Claude.
- TD Python is single threaded. Never touch a TD object from a worker thread.
- Third party Python goes in the project venv managed by TDPyEnvManager, declared in `TDPyEnvManagerContext.yaml`. Do not assume a package is available without checking.
- Scaffold scripts need Python 3.11+ with PyYAML.

## Entry points

| Task | Where |
|---|---|
| Canonical rules (this file) | `AGENTS.md` |
| New project, Architect role | `.claude/skills/td-architect/SKILL.md` |
| Build, Builder role | `.claude/skills/td-builder/SKILL.md` |
| Error memory, read and write | `knowledge/lessons.yaml` + `.claude/skills/td-auto-improve/SKILL.md` |
| Conventions, always in force | `.claude/rules/00-studio-conventions.md` |
| Reusable components | `lib/index.yaml` |
| Seed setup, environment check | `templates/SEED-SETUP.md`, `scripts/check_env.py` |
| Full architecture | `ARCHITECTURE.md` |
