# CLAUDE.md

TD Factory: a two agent pipeline that turns a prompt into a working TouchDesigner project.

The canonical instruction set for every agent (Claude included) is `AGENTS.md` at the repo
root. Read it and follow it. Quick map: roles and hard rules in `AGENTS.md`, conventions in
`.claude/rules/00-studio-conventions.md` (always in force), workflows in `.claude/skills/`
(`td-architect`, `td-builder`, `td-auto-improve`), error memory in `knowledge/lessons.yaml`,
slash commands `/new-td-project` and `/build-td-project`.
