---
name: td-auto-improve
description: Mémoire d'erreurs de TD Factory. Charger quand un agent identifie et vérifie la solution d'une erreur TD, Envoy ou build, et pour consulter ou mettre à jour knowledge/lessons.yaml. Fonctionne pour tout agent, tout harness, pas seulement Claude.
---

# TD Auto Improve

Une erreur résolue mais non enregistrée sera résolue une seconde fois par le prochain agent, avec un bug différent. `knowledge/lessons.yaml` est la mémoire partagée de l'usine : un fichier YAML brut, lisible et écrivable par n'importe quel agent, quel que soit son harness. Même statut que `lib/index.yaml`.

## Lire

- Avant un build : grep sur les tags et familles d'opérateurs de tes étages.
- En rencontrant une erreur : grep sur le message d'erreur exact. Les messages sont stockés verbatim pour que grep matche.
- Une leçon qui ne s'applique plus (API changée, version différente) : le dire dans son champ `fix`, ne pas la supprimer silencieusement.

## Enregistrer

Enregistre quand les trois conditions sont réunies :

1. une erreur ou un comportement inattendu est survenu ;
2. la cause racine est identifiée, pas juste un contournement qui marche sans explication ;
3. le fix est vérifié (capture, mesure, `get_op_errors` vide).

N'enregistre pas : un fix non vérifié, une hypothèse, un problème propre à une machine (sauf si tu le tagues `env` en précisant le périmètre).

### Protocole

1. **Dédup d'abord.** Grep `knowledge/lessons.yaml` sur les mots-clés du symptôme et de la cause. Si une entrée existe, mets-la à jour (`fix` complété, `hits +1`, `date` du jour) au lieu d'en créer une doublonne.
2. **Écris l'entrée** au format du fichier, sans casser le YAML :

```yaml
- id: pop-attribute-copy-cook
  date: 2026-09-08
  hits: 1
  context: brain-eeg-cloud, étage fx_displace
  symptom: >
    texte d'erreur exact ou comportement observable, verbatim
  cause: >
    cause racine identifiée
  fix: >
    ce qui a corrigé, et comment ça a été vérifié
  prevention: ce qu'il faut faire la prochaine fois pour ne pas la rencontrer
  tags: [pop, attribute, cook]
  source: claude-code
```

3. **Style** : phrases courtes, messages d'erreur verbatim, aucun récit. Français ou anglais, peu importe ; les messages d'erreur ne se traduisent pas.
4. **Enregistre au moment où tu tiens la solution**, pas à la fin de la session. Une leçon écrite après coup est une leçon déformée.
5. **Promotion.** Trois `hits` ou trois leçons du même pattern : fusionne-les et propose leur promotion en règle dans `.claude/rules/00-studio-conventions.md`, avec accord humain. La mémoire ne remplace pas les conventions, elle les alimente.

## Portée multi-agents

Ce registre n'appartient à aucun harness. Tout agent (Claude Code, Codex, Cursor, opencode, ...) lit et écrit le même `knowledge/lessons.yaml`. Le point d'entrée universel du dépôt est `AGENTS.md`. Si ton harness charge automatiquement les skills `.claude/`, cette skill se charge seule ; sinon, lis ce fichier comme un document de workflow ordinaire et applique-le.
