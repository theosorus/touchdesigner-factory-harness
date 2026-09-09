# TD Factory : architecture

Une usine à projets TouchDesigner pilotée par deux agents. Tu écris une phrase, tu récupères un `.toe` qui tourne, versionné et vérifié.

## Le principe

Le problème d'un agent qui construit du TouchDesigner tout seul, c'est qu'il n'a pas de contrat. Il improvise, il empile des opérateurs, et au bout de 40 tours tu as un réseau que personne ne peut relire. La solution est de couper en deux, avec un artefact écrit entre les deux.

```
prompt humain
    |
    v
[Agent 1 : Architecte]  ------> projects/<slug>/spec.yaml   (contrat, relu par toi)
    |                                    |
   pas de MCP,                           |
   pas de TD ouvert                      v
                            [Agent 2 : Builder] -----> session TD vivante via Envoy
                                         |                     |
                                         v                     v
                              build-report.md          project.toe + .tdxn + captures
```

L'artefact `spec.yaml` est le point de contrôle. Tant qu'il n'est pas validé, rien n'est construit. Et une fois validé, il survit à la session : un autre agent, un sub-agent, ou toi trois semaines plus tard peut le rejouer.

## Pourquoi deux agents et pas un

| | Architecte | Builder |
|---|---|---|
| Entrée | une phrase floue | un spec.yaml validé |
| Sortie | un spec.yaml | un projet TD qui tourne |
| Outils | fichiers, web search, lecture de `lib/` | MCP Envoy, fichiers |
| TD ouvert | non | oui |
| Contexte | large, exploratoire | étroit, exécutif |
| Mode | plan mode | exécution |
| Coût si raté | tu relis 60 lignes de YAML | tu jettes 40 minutes de build |

Séparer, c'est déplacer le coût de l'erreur du build vers la relecture. Un spec faux se corrige en 30 secondes.

## Les sept couches

**1. Le contrat (`templates/spec.template.yaml`)**
Le schéma que l'Architecte remplit. Il force les décisions qui coûtent cher à changer après coup : résolution, fps cible, budget d'opérateurs, entrées, paramètres exposés, découpage en étages, critères d'acceptation.

**2. Les conventions (`.claude/rules/`)**
Chargées dans chaque conversation. Nommage, layout, structure de containers, règles Python TD. C'est ce qui rend deux projets générés à trois mois d'écart lisibles de la même façon.

**3. Les skills (`.claude/skills/`)**
`td-architect` et `td-builder`, chargées à la demande. Elles contiennent les workflows, pas les conventions.

**4. La bibliothèque (`lib/`)**
Le vrai levier de long terme. Chaque composant qui marche est exporté en TDXN et indexé. Au projet 10, le Builder assemble plus qu'il ne construit. C'est ce qui fait qu'une usine devient rentable.

**5. Les projets (`projects/<slug>/`)**
Un dossier par projet, autonome, avec son spec, son `.toe`, son code externalisé, ses captures et son rapport de build.

**6. La vérification**
Aucun build n'est "fini" sans : capture avec verdict qualité `pass`, `get_op_errors` vide sur toute la hiérarchie, fps dans la tolérance de la baseline mesurée avant build, et chaque paramètre custom testé sur ses bornes.

**7. La mémoire des erreurs (`knowledge/lessons.yaml`)**
Chaque erreur résolue avec cause identifiée et fix vérifié devient une leçon greppable, partagée par tous les agents et tous les harnesses. Trois occurrences d'un même pattern, et la leçon est promue en convention. C'est ce qui fait qu'une usine ne refait pas deux fois la même erreur.

## Structure du dépôt

```
td-factory/
├── AGENTS.md                   # point d'entrée canonique pour tout agent, pas seulement Claude
├── CLAUDE.md                   # contexte global, lu à chaque session Claude
├── ARCHITECTURE.md              # ce fichier
├── .claude/
│   ├── rules/
│   │   └── 00-studio-conventions.md
│   ├── skills/
│   │   ├── td-architect/SKILL.md
│   │   ├── td-builder/SKILL.md
│   │   └── td-auto-improve/SKILL.md
│   └── commands/
│       ├── new-td-project.md    # /new-td-project <prompt>
│       └── build-td-project.md  # /build-td-project <slug>
├── templates/
│   ├── spec.template.yaml
│   └── project-README.md
├── scripts/
│   ├── new_project.py           # scaffold d'un dossier projet
│   └── validate_spec.py         # gate : le spec est-il exécutable
├── lib/
│   └── index.yaml               # registre des composants TDXN réutilisables
├── knowledge/
│   └── lessons.yaml             # mémoire des erreurs, partagée entre agents
└── projects/
    └── <slug>/
        ├── spec.yaml            # le contrat
        ├── project.toe          # binaire, non diffable
        ├── network/             # exports TDXN, source de vérité lisible
        ├── scripts/             # python externalisé
        ├── glsl/                # shaders externalisés
        ├── assets/
        ├── captures/            # preuves visuelles horodatées
        ├── build-report.md      # ce que le Builder a fait et vérifié
        └── README.md
```

## Ce que l'agent doit avoir sous la main pour bosser
Résumé de la question posée. Un agent qui construit du TD a besoin de sept choses, et il en manque toujours au moins trois quand ça se passe mal :


1. **Un contrat écrit** de ce qu'il doit produire, avec des critères vérifiables. Sinon il déclare victoire trop tôt.
2. **L'introspection de l'API** : les vrais noms de paramètres, pas ceux qu'il devine. Envoy fournit `get_docs`, `get_td_class_details`, `get_parameter`.
3. **Un feedback visuel** avec un verdict machine. Une capture qu'il peut regarder, plus un `is_black` / `is_flat` / `pass` qu'il peut lire sans regarder.
4. **L'état réel du réseau** en peu de tokens. `read_tdxn` plutôt que 200 appels `get_op`.
5. **Un budget** : nombre d'opérateurs, temps de cook GPU, fps plancher. Sans budget, il construit jusqu'à ce que ça rame.
6. **Une bibliothèque** de ce qui a déjà marché. Sinon il réinvente le même feedback loop à chaque projet, avec un bug différent à chaque fois.
7. **Une mémoire des erreurs** : ce qui a déjà coûté du temps et comment ça s'est résolu. Sinon chaque agent refait la même erreur, avec un bug différent lui aussi.

## Prérequis

- TouchDesigner 2025.33070 ou plus
- Embody + Envoy installés dans le `.toe` seed (le Setup Wizard écrit `.mcp.json`, `.claude/rules/` et `.claude/skills/` d'Embody)
- Un agent MCP capable : Claude Code, ou tout autre qui lit `AGENTS.md` (point d'entrée canonique, indépendant du harness)
- Python 3.11+ pour les scripts de scaffold

Note de cohabitation : Embody génère ses propres fichiers dans `.claude/`. Les fichiers de cette usine sont préfixés (`00-studio-conventions.md`) ou portent des noms qui n'entrent pas en collision (`td-architect`, `td-builder`). Embody garde une empreinte de ce qu'il génère et ne réécrit pas un fichier que tu as modifié, mais ne renomme jamais un de ses fichiers pour autant.
