# TD Factory

Une phrase en entrée, un projet TouchDesigner qui tourne en sortie. Deux agents, un contrat écrit entre les deux.

## Installation

```bash
git clone <ton-repo> td-factory && cd td-factory
pip install pyyaml
```

Puis suis `templates/SEED-SETUP.md` : installer Embody dans un TouchDesigner 2025.33070+ vierge (collage d'une ligne dans le Textport), passer le Setup Wizard (assistant Claude Code, racine du projet AI = la racine git de ce dépôt), et sauvegarder le résultat en `templates/seed.toe`. Cinq minutes, une seule fois : chaque nouveau projet repartira de ce seed, Embody et Envoy déjà installés.

Vérification :

```bash
python scripts/check_env.py
```

`SEED READY` en sortie, et l'usine peut produire.

## Utilisation

```
/new-td-project un cerveau en nuage de points qui réagit à un signal EEG
```

L'Architecte scaffolde le dossier, lit la bibliothèque, pose au plus trois questions, écrit `projects/<slug>/spec.yaml`, le valide et s'arrête.

Tu relis le spec. C'est le seul moment où tu dois vraiment réfléchir.

```
/build-td-project brain-eeg-cloud
```

Le Builder lance TD, mesure une baseline de perf, construit étage par étage avec une capture après chacun, passe les critères d'acceptation, externalise, exporte le TDXN et écrit son rapport.

## Le fichier qui compte

`projects/<slug>/spec.yaml`. Tout le reste est de la plomberie. Lis `ARCHITECTURE.md` pour comprendre pourquoi le contrat est séparé de l'exécution, et `templates/spec.template.yaml` pour la forme exacte.

`projects/brain-eeg-cloud/spec.yaml` est un exemple complet et valide, à lire avant d'en écrire un.

## Le gate

```bash
python scripts/validate_spec.py <slug>
```

Il refuse un spec avec des placeholders, un graphe d'étages incohérent, des budgets qui ne s'additionnent pas, un paramètre sans texte d'aide, moins de trois critères d'acceptation, un critère non vérifiable par une machine ("looks good"), ou une section risques vide. Sortie 0 égale build autorisé.

## La bibliothèque

`lib/index.yaml`. Chaque composant générique qui a marché y est indexé avec son coût GPU et ses pièges. Le Builder le lit avant de construire. C'est ce qui fait qu'au dixième projet il assemble au lieu de repartir de zéro.

## La mémoire des erreurs

`knowledge/lessons.yaml`. Chaque erreur dont la cause est identifiée et le fix vérifié y devient une leçon, greppable par tag et par message d'erreur exact. Les agents la lisent avant de construire et à chaque erreur ; ils y écrivent dès qu'ils tiennent une solution vérifiée. Trois occurrences d'un même pattern et la leçon est proposée en promotion dans les conventions. Le protocole est dans `.claude/skills/td-auto-improve/SKILL.md`.

## Multi-agents

Le dépôt n'est pas lié à Claude. `AGENTS.md` est le point d'entrée canonique pour n'importe quel agent (Codex, Cursor, opencode, ...) : mêmes rôles, mêmes règles, mêmes fichiers. Envoy est un serveur MCP standard, donc pilotable par tout client MCP. La bibliothèque et la mémoire des erreurs sont des fichiers bruts, partagés par tous les harnesses.

## Cohabitation avec Embody

Embody génère ses propres `.claude/rules/` et `.claude/skills/`. Les fichiers de cette usine ne rentrent pas en collision : préfixe `00-` pour les règles, noms `td-architect` et `td-builder` pour les skills. Embody garde une empreinte de ce qu'il génère et ne réécrit jamais un fichier que tu as modifié.
