---
name: td-auto-improve
description: The error memory of TD Factory Harness. Load when an agent identifies and verifies the fix for a TD, Envoy or build error, and to read or update knowledge/lessons.yaml. Works for any agent, any harness, not just Claude.
---

# TD Auto Improve

An error that is solved but not recorded will be solved a second time by the next agent, with a
different bug. `knowledge/lessons.yaml` is the factory's shared memory: a plain YAML file any
agent can read and write, whatever its harness. Same status as `lib/index.yaml`.

## Reading

- Before a build: grep on the tags and operator families of your stages.
- On hitting an error: grep on the exact error message. Messages are stored verbatim so grep
  matches.
- A lesson that no longer applies (API changed, different version): say so in its `fix` field,
  do not delete it silently.

## Recording

Record when all three conditions hold:

1. an error or unexpected behaviour occurred;
2. the root cause is identified, not just a workaround that happens to work;
3. the fix is verified (capture, measurement, empty `get_op_errors`).

Do not record: an unverified fix, a hypothesis, or a machine-specific problem (unless you tag it
`env` and state the scope).

### Protocol

1. **Dedupe first.** Grep `knowledge/lessons.yaml` for keywords from the symptom and the cause.
   If an entry exists, update it (`fix` extended, `hits +1`, today's `date`) rather than adding a
   duplicate.
2. **Write the entry** in the file's format, without breaking the YAML:

```yaml
- id: pop-attribute-copy-cook
  date: 2026-09-08
  hits: 1
  context: brain-eeg-cloud, fx_displace stage
  symptom: >
    exact error text or observable behaviour, verbatim
  cause: >
    identified root cause
  fix: >
    what fixed it, and how it was verified
  prevention: what to do next time so you never meet it
  tags: [pop, attribute, cook]
  source: claude-code
```

3. **Style**: short sentences, error messages verbatim, no storytelling. Error messages are never
   translated.
4. **Record the moment you hold the solution**, not at the end of the session. A lesson written
   after the fact is a distorted lesson.
5. **Promotion.** Three `hits`, or three lessons of the same pattern: merge them and propose
   promoting them into a rule in `.claude/rules/00-studio-conventions.md`, with human agreement.
   The memory does not replace the conventions, it feeds them.

## Multi-agent scope

This registry belongs to no harness. Any agent (Claude Code, Codex, Cursor, opencode, ...) reads
and writes the same `knowledge/lessons.yaml`. The repo's universal entry point is `AGENTS.md`. If
your harness auto-loads `.claude/` skills, this one loads itself; otherwise read this file as an
ordinary workflow document and apply it.
