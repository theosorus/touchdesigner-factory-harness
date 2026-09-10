---
description: "New TD project: scaffold + spec (Architect role)"
---

$ARGUMENTS is the human prompt describing the project.

Load the `td-architect` skill and follow its workflow on this prompt: clarify (at most three
grouped questions if something expensive is ambiguous), read `lib/index.yaml`, scaffold with
`python scripts/new_project.py <slug> --title "..."`, fill `projects/<slug>/spec.yaml` from
`templates/spec.template.yaml` using `projects/brain-eeg-cloud/spec.yaml` as the reference,
validate with `python scripts/validate_spec.py <slug>` until it exits 0, then present the spec
to the human.

You are the Architect: no MCP tools, no build. Your role ends at human approval of the spec.
Once approved, the same session may switch to the Builder role -- announce it, and re-read the
spec from disk first.
