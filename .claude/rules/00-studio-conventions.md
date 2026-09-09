# Conventions studio TD Factory

Chargées dans chaque session. Elles rendent deux projets produits à trois mois d'écart lisibles de la même façon. Un build qui les viole n'est pas fini.

## Étages et nommage

- Un étage du `pipeline` du spec = un `base` COMP au root, nommé exactement comme l'id de l'étage : `src_cloud`, `fx_displace`, `render`.
- Chaque étage se termine sur un Null nommé `out_<id_etage>` : `out_src_cloud`, `out_final`. C'est le contrat de câblage entre étages, vérifié par le validator.
- `consumes` ne référence que des étages situés avant dans la liste. Le graphe est un DAG, jamais de cycle.
- Au root : uniquement les containers d'étages, leurs nulls de sortie, l'op final `out_final`, et au besoin un null d'entrée. Rien d'autre. `budget.max_ops_root` est un plafond, pas une suggestion.
- Opérateurs internes : préfixés par la fonction, pas par le type. `SrcSpectrum1`, `FbDecay1`, `ClampSignal1`. Jamais de nom par défaut type `moviefilein1`.

## Layout

- Flux de gauche à droite, dans l'ordre du pipeline. Un container, une colonne.
- Positions alignées sur une grille de 200 unités, au moins une largeur de node entre containers.
- Aucun fil ne traverse un node. Un câblage illisible est un bug de layout, pas une question de style.
- Chaque container d'étage porte une annotation d'une ligne : sa responsabilité, recopiée du spec.

## Paramètres custom

- Les paramètres exposés vivent sur la page `Custom` du container de leur étage, définis dans le spec : `name`, `style`, `range`, `default`, `help`.
- Le `help` est obligatoire et décrit l'effet visible, pas le mécanisme. Un paramètre sans `help` ne passe pas la validation.
- Les valeurs du spec sont la référence : le `default` installé doit être exactement celui du spec.
- Pas de valeur magique en dur dans le réseau quand un paramètre existe : binder, pas dupliquer.

## Entrées

- Chaque entrée du spec déclare son `mock` (noise, file, constant). Le pipeline est construit et vérifié sur le mock : jamais sur "il faut brancher le vrai signal pour voir quelque chose".
- Normalisation et clamp aux bornes déclarées (`range`) se font à l'entrée, dans l'étage de contrôle, jamais en aval. Le reste du réseau ne voit que du 0-1 propre.

## Python TD

- TD Python est mono-thread. Jamais de manipulation d'objet TD depuis un thread worker.
- Tout script de plus de quelques lignes est externalisé dans `projects/<slug>/scripts/` et référencé par chemin relatif. Jamais de chemin absolu, jamais de gros `execute` inline dans un DAT.
- Python tiers via le venv du projet géré par TDPyEnvManager, déclaré dans `TDPyEnvManagerContext.yaml`. Un package non déclaré est un package qui n'existe pas.
- Pas de `try/except` silencieux : une erreur avalée est une capture noire dans dix minutes.
- Accès réseau par chemins relatifs (`me.parent()`, `op('./...')`), pas de `op('/project1/...')` en dur.

## GLSL

- Un shader, un fichier, dans `projects/<slug>/glsl/`. Jamais de GLSL inline dans un paramètre.

## Vérité et versioning

- Le `.toe` est un binaire non diffable. À chaque build réussi : export TDXN dans `network/`, code dans `scripts/` et `glsl/`. Le spec est la source de vérité de l'intention, le TDXN celle de la structure.
- Les captures de vérification vont dans `captures/`, nommées `YYYYMMDD-HHMMSS-<contexte>.png`.
- `build-report.md` est écrit par le Builder à chaque build. Jamais à la main.

## Vérification

Aucun build n'est fini sans les quatre portes : capture avec verdict qualité `pass` (ni `is_black`, ni `is_flat`), `get_op_errors` vide sur toute la hiérarchie, fps au-dessus du plancher (`target_fps * fps_tolerance`) avec toutes les entrées actives, et chaque paramètre custom balayé min/mid/max sans erreur ni frame noire. Ensuite et seulement ensuite : export, rapport, capitalisation dans `lib/`.
