# {{TITLE}}

Généré par TD Factory. Le contrat est dans `spec.yaml`, le compte rendu d'exécution dans `build-report.md`.

## Ouvrir

```
open project.toe
```

Envoy démarre avec le projet. `.mcp.json` est déjà écrit à la racine du dépôt.

## Structure

- `spec.yaml` : le contrat de build. Source de vérité de l'intention.
- `network/` : export TDXN, lisible et diffable. Source de vérité de la structure.
- `scripts/` : Python externalisé, édité directement par l'agent.
- `glsl/` : shaders externalisés.
- `captures/` : preuves visuelles horodatées de chaque build.
- `project.toe` : binaire, régénérable depuis le TDXN.

## Reconstruire

```
/build-td-project {{SLUG}}
```

Le Builder détecte un réseau existant et ne construit que ce qui manque.
