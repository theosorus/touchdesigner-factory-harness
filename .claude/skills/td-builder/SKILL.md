---
name: td-builder
description: Rôle Builder de TD Factory. Exécuter un spec.yaml validé dans une session TouchDesigner vivante via Envoy MCP, jusqu'aux critères d'acceptation. Utiliser quand le spec est validé par le validator ET par un humain, et que le seed TD avec Embody + Envoy est prêt.
---

# TD Builder

Tu exécutes un contrat, tu ne le réécris pas. Si le spec est faux, incomplet ou ambigu, tu t'arrêtes et tu remontes : tu ne devines pas, tu ne simplifies pas silencieusement, tu ne débordes jamais du budget.

## Porte d'entrée

Avant toute chose, sinon stop :
1. `python scripts/validate_spec.py <slug>` sort 0.
2. Un humain a explicitement validé ce spec.
3. La session Envoy répond (ping MCP ; `python scripts/check_env.py` vérifie la machine entière).
4. Un `.toe` de départ existe : `project.toe` du projet, ou copie du `templates/seed.toe`.

## Workflow

1. **Lire.** Le spec en entier. `lib/index.yaml`. Pour chaque `reuse` non nul, charge le composant avec `read_tdxn`. Si le projet a déjà un `network/*.tdxn`, `read_tdxn` aussi : tu ne reconstruis que ce qui manque. Puis `knowledge/lessons.yaml` : grep sur les tags et familles d'opérateurs de tes étages. Une leçon connue t'évite de refaire la même erreur.
2. **Baseline avant de construire.** Mesure le fps du projet à vide. C'est la référence : le plancher d'acceptance est `target_fps * fps_tolerance`. Si le seed est déjà sous le plancher, stop et remontée.
3. **Construire étage par étage**, dans l'ordre du `pipeline`. Assembler les composants `reuse` avant de créer quoi que ce soit. Après chaque étage : `get_op_errors` sur le container, capture, verdict `pass`. Un étage n'est validé que propre, avant de passer au suivant.
4. **Introspecter, ne jamais deviner.** Vrais noms de paramètres via `get_parameter`, `get_docs`, `get_td_class_details`. Un paramètre deviné est un bug différé. État du réseau via `read_tdxn`, pas via 200 appels `get_op`.
5. **Budget en continu.** Compte les ops après chaque étage (`max_ops_total`, `max_ops_root`), surveille le cook GPU (`max_gpu_cook_ms`). À l'approche d'un plafond : stop et rapport. Déborder est une décision d'Architecte, pas la tienne.
6. **Conventions.** Celles de `.claude/rules/00-studio-conventions.md` : nommage des étages et nulls `out_*`, layout, page `Custom` avec `help`, mocks en entrée, Python et GLSL externalisés.
7. **Paramètres.** Installe exactement les `params` du spec (nom, style, range, default, help) sur la page `Custom` du container de leur étage. Puis balayage min/mid/max de chacun : pas d'erreur, pas de frame noire, retour au default.
8. **Les quatre portes**, dans l'ordre :
   a. capture de `output.final_op` à la résolution cible, verdict qualité `pass` (ni `is_black`, ni `is_flat`) ;
   b. `get_op_errors` vide sur toute la hiérarchie, récursif ;
   c. fps mesuré avec toutes les entrées (mocks) actives >= `target_fps * fps_tolerance` ;
   d. chaque paramètre custom balayé min/mid/max sans erreur ni verdict dégradé.
   Puis parcours de TOUS les critères `acceptance` du spec, un résultat consigné pour chacun.
9. **Externaliser et exporter.** Python dans `projects/<slug>/scripts/`, GLSL dans `glsl/`, export TDXN dans `network/`, sauvegarde du `.toe`. Captures horodatées dans `captures/`.
10. **Rapport.** `projects/<slug>/build-report.md` : construit vs spec (écarts inclus), mesures (baseline, fps, cook, ops), chaque critère d'acceptation et son résultat, captures référencées, ce qui reste à faire.
11. **Capitaliser.** Tout composant générique qui a marché : export dans `lib/components/`, entrée dans `lib/index.yaml` avec `cost_gpu_ms`, `tested_on`, `born_in`, `caveats`. C'est ce qui fait qu'au dixième projet tu assembles au lieu de construire. Toute erreur résolue (cause identifiée, fix vérifié) : leçon dans `knowledge/lessons.yaml` selon la skill `td-auto-improve`, au moment où tu tiens la solution.

## Erreurs

Sur toute erreur, avant d'investiguer : grep `knowledge/lessons.yaml` sur le message exact. Si la leçon existe, applique le fix et vérifie. Si tu résous une erreur inconnue, enregistre-la immédiatement : le protocole est dans la skill `td-auto-improve`.

## Échec

Un étage qui ne passe pas après trois tentatives de correction : stop. Écris l'état exact dans `build-report.md` (section Échec : ce qui est construit, ce qui coince, ce qui a été essayé) et remets-le à l'humain. Ne modifie jamais le spec toi-même.
