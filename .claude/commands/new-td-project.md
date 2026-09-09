---
description: "Nouveau projet TD : scaffold + spec (rôle Architecte)"
---

$ARGUMENTS est le prompt humain décrivant le projet.

Charge la skill `td-architect` et déroule son workflow sur ce prompt : clarifier (au plus trois questions groupées si un point coûteux est ambigu), lire `lib/index.yaml`, scaffolder avec `python scripts/new_project.py <slug> --title "..."`, remplir `projects/<slug>/spec.yaml` depuis `templates/spec.template.yaml` avec `projects/brain-eeg-cloud/spec.yaml` comme référence, valider avec `python scripts/validate_spec.py <slug>` jusqu'à sortie 0, puis présenter le spec à l'humain.

Tu es l'Architecte : aucun outil MCP, aucun build. La session s'arrête à la validation humaine du spec.
