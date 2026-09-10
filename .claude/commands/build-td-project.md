---
description: "Build project <slug> from its approved spec (Builder role)"
---

$ARGUMENTS is the slug of the project to build.

Load the `td-builder` skill and follow its workflow on this project. Entry gate:
`python scripts/validate_spec.py <slug>` must exit 0, the spec must have been approved by a
human, the Envoy session must respond, and a starting `.toe` must exist. Otherwise, stop.

Then: read the spec and the library, measure an fps baseline, build stage by stage with a
capture after each one, the four gates, externalization (`scripts/`, `glsl/`,
`network/*.tdxn`, `project.toe`), `build-report.md`, and capitalization into `lib/` and
`knowledge/lessons.yaml`.

You are the Builder: you never modify the spec. A spec or budget obstacle goes back to the
human.
