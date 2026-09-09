---
description: "Builder le projet <slug> depuis son spec validé (rôle Builder)"
---

$ARGUMENTS est le slug du projet à builder.

Charge la skill `td-builder` et déroule son workflow sur ce projet. Porte d'entrée : `python scripts/validate_spec.py <slug>` doit sortir 0, le spec doit avoir été validé par un humain, la session Envoy doit répondre, un `.toe` de départ doit exister. Sinon stop.

Puis : lecture du spec et de la lib, baseline fps, construction étage par étage avec capture après chacun, les quatre portes, externalisation (`scripts/`, `glsl/`, `network/*.tdxn`, `project.toe`), `build-report.md`, capitalisation dans `lib/` et `knowledge/lessons.yaml`.

Tu es le Builder : tu ne modifies jamais le spec. Un obstacle de spec ou de budget se remonte à l'humain.
