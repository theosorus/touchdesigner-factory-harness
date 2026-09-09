# Préparer le seed TD — tutoriel détaillé (une seule fois, ~5 minutes)

**Ce que tu produis** : `templates/seed.toe`, un projet TouchDesigner vierge contenant Embody + Envoy, configurés pour ce dépôt. Chaque nouveau projet scaffoldé repartira de ce seed : `scripts/new_project.py` le copie en `projects/<slug>/project.toe`, Embody et Envoy déjà dedans.

**État de la machine, vérifié** :

| Prérequis | État |
|---|---|
| TouchDesigner 2025.33070+ | OK — 2025.33070 dans `/Applications/TouchDesigner.app`, instance en cours d'exécution |
| Dépôt git | OK — `experimental_mcp_td`, branche `main`, rien commité pour l'instant |
| Python 3.11+ / pyyaml | OK — 3.13.9 / 6.0.3 |
| Embody + Envoy | Absents — c'est ce que ce tuto installe |

Diagnostic machine à tout moment :

```bash
python3 scripts/check_env.py
```

Actuellement : `NOT READY: 3 items missing` (`.mcp.json`, bridge Envoy, seed.toe). À la fin de ce tuto : `SEED READY`.

**Vue d'ensemble** :

| # | Action | Où | Durée |
|---|---|---|---|
| 0 | Committer l'usine | Terminal | 20 s |
| 1 | Sauvegarder le projet vierge en `templates/seed.toe` | TouchDesigner | 30 s |
| 2 | Installer Embody (une ligne dans le Textport) | TouchDesigner | 1 min |
| 3 | Passer le Setup Wizard écran par écran | TouchDesigner | 2 min |
| 4 | Vérifier, réconcilier avec nos fichiers, committer | Terminal + TD | 1 min |

Pourquoi sauvegarder *avant* d'installer (étape 1 avant 2) : le wizard exige un projet déjà sauvegardé — sinon son premier écran est "Save your project", et tout ce qu'il configure atterrit *relatif au dossier du projet*. En sauvegardant d'abord au bon endroit, cet écran disparaît et la config atterrit à la racine du dépôt.

---

## Étape 0 — Committer l'usine

Le wizard va écrire dans ce dépôt : `.mcp.json`, `.embody/`, des fichiers dans `.claude/`, et potentiellement réécrire `AGENTS.md`. Un commit propre avant garantit que rien de ce que nous avons écrit ne peut être perdu, et permet de voir exactement ce qu'Embody ajoute (`git status`).

```bash
cd /Users/tcastillo/Documents/experimental_mcp_td
git add -A
git commit -m "TD Factory: init"
```

Sortie attendue : un commit avec ~25 fichiers (`.claude/`, `AGENTS.md`, `ARCHITECTURE.md`, `scripts/`, `templates/`, `knowledge/`, `lib/`, `projects/`, `README.md`, `.gitignore`).

---

## Étape 1 — Sauvegarder le projet vierge en seed

Dans TouchDesigner (l'instance déjà ouverte) :

1. Si le projet actuellement ouvert n'est **pas** vierge : **File > New** (Cmd+N) pour repartir d'un projet vide. Un projet non sauvegardé et vide convient aussi.
2. **File > Save As** (Cmd+Shift+S).
3. Navigue jusqu'à :

```
/Users/tcastillo/Documents/experimental_mcp_td/templates/seed.toe
```

4. Enregistre. Le fichier est encore un `.toe` ordinaire — Embody arrive à l'étape suivante. On le re-sauvegardera une dernière fois à la fin pour qu'il contienne Embody configuré.

---

## Étape 2 — Installer Embody

1. Ouvre le Textport : **Dialogs > Textport and DATs**, ou **Alt+T**.
2. Colle cette ligne officielle (elle télécharge la dernière release depuis GitHub, vérifie son checksum sha256, et charge le COMP Embody dans le réseau courant — exactement comme un drag & drop du `.tox`) :

```python
import requests, hashlib, tempfile, os; h = {'User-Agent': 'Embody-Install'}; mf = requests.get('https://github.com/dylanroscover/Embody/releases/latest/download/embody-release.json', headers=h, timeout=30).json(); b = requests.get('https://github.com/dylanroscover/Embody/releases/download/%s/%s' % (mf['tag'], mf['asset']), headers=h, timeout=120).content; assert hashlib.sha256(b).hexdigest() == mf['sha256'], 'checksum mismatch'; f = os.path.join(tempfile.gettempdir(), mf['asset']); open(f, 'wb').write(b); n = ui.panes.current; n = n if n.type == PaneType.NETWORKEDITOR else next(x for x in ui.panes if x.type == PaneType.NETWORKEDITOR); print('Embody', mf['version'], 'installed at', n.owner.loadTox(f).path)
```

3. Entrée. TD pause quelques secondes pendant le téléchargement (~quelques Mo), puis le Textport affiche :

```
Embody 6.2.42 installed at /project1/Embody
```

(le numéro de version peut être plus récent). Le COMP `Embody` apparaît dans le réseau.

4. Embody s'initialise en quelques frames, puis **le Setup Wizard s'ouvre tout seul**.

**Si la ligne échoue** (réseau, proxy, requests indisponible) : télécharge le `.tox` sur `github.com/dylanroscover/Embody/releases/latest` et glisse-le dans le réseau — même résultat.

---

## Étape 3 — Le Setup Wizard, écran par écran

Le wizard s'adapte : certains écrans n'apparaissent que si leur question se pose. **Rien ne change avant le clic final** — chaque écran ne fait qu'enregistrer une sélection ; tu peux fermer ("Not now") à tout moment sans toucher au projet.

Écrans dans l'ordre, avec le choix à faire pour cette usine :

| Écran | Choix | Pourquoi |
|---|---|---|
| 1. Save your project | **N'apparaît pas** (projet sauvé à l'étape 1) | C'est l'intérêt d'avoir sauvegardé d'abord |
| 2. Mode | **Auto** (recommandé) | En Auto, la racine de config AI est la racine git automatiquement — exactement ce qu'on veut. Advanced affiche le choix explicitement (Git root / Project folder / Custom) plus un écran "footprint", inutile ici |
| 3. Externalization | **New work only** (recommandé) — ou absent si le projet est vierge | L'externalisation des projets de l'usine est gérée par le Builder (TDXN via Envoy) |
| 4. AI assistant | **Claude Code** (recommandé) | Génère `.mcp.json` + `.claude/` complet — le chemin auto-configuré |
| 5. Pick your AI tool | N'apparaît pas (réservé à "Other AI tool") | — |
| 6. Permissions (Claude Code) | **Don't ask** (recommandé) — ou **Ask for some** si tu préfère valider les écritures | Un build fait des dizaines d'appels d'outils ; "Don't ask" les pré-approuve tous (le serveur n'écoute que sur 127.0.0.1). "Ask for some" auto-approuve la lecture seulement |
| 7. Convoy | **Keep Convoy Off** | Convoy = contrôle de plusieurs nodes Embody sur le LAN, et active une app hôte au login. Machine unique : inutile |
| 8. Git | **N'apparaît pas** (le dépôt existe déjà) | Embody ajoute juste ses entrées à nos `.gitignore` / `.gitattributes` existants |
| 9. Footprint review | Uniquement en mode Advanced | — |
| 10. Summary | Relis, puis clique **Set up Embody** | C'est le seul clic qui applique quoi que ce soit |

**Ce que fait le clic "Set up Embody"** :

- écrit `.mcp.json` à la racine du dépôt (connexion MCP pour tout client compatible) ;
- écrit le bridge `.embody/envoy-bridge.py` et démarre le serveur Envoy sur `127.0.0.1:9870` (ports 9870–9879 si plusieurs instances) ;
- écrit ses propres rules et skills dans `.claude/` (elles s'ajoutent aux nôtres, pas de collision : les nôtres sont préfixées `td-`), et des skills dans `.agents/skills/` pour Codex/Cursor/Gemini ;
- régénère `AGENTS.md` (le sien — voir l'étape 4) et **fusionne** un bloc auto-généré dans notre `CLAUDE.md`, délimité par un titre visible `## Embody / Envoy -- auto-generated section` : notre contenu est préservé tel quel ;
- ajoute `.mcp.json`, `.embody/`, `.claude/settings.local.json` au `.gitignore` (fichiers runtime, régénérés au démarrage) ;
- installe ~30 Mo de dépendances Python en tâche de fond — TD reste réactif.

---

## Étape 4 — Vérifier, réconcilier, committer

### 4a. Re-sauvegarder le seed (crucial)

Dans TouchDesigner : **Cmd+S**. Le `seed.toe` doit contenir Embody configuré — sans ce re-save, le seed sur disque est encore le projet vide de l'étape 1.

### 4b. Vérifier la machine

```bash
python3 scripts/check_env.py
```

Sortie attendue :

```
OK   python  (3.13.9)
OK   pyyaml
OK   touchdesigner  (2025.33070 at /Applications/TouchDesigner.app)
OK   git repo  (/Users/tcastillo/Documents/experimental_mcp_td)
OK   .mcp.json  (servers: ...)
OK   envoy bridge  (.embody/envoy-bridge.py)
OK   seed.toe  (templates/seed.toe)
OK   td running  (pids: ...)
OK   envoy listening  (127.0.0.1:9870)

SEED READY: the factory can produce .toe projects.
```

### 4c. Réconcilier avec nos fichiers

```bash
git status
git diff AGENTS.md CLAUDE.md .gitignore
```

Point par point :

- **`CLAUDE.md`** : Embody y a ajouté son bloc délimité entre ton contenu et le sien. C'est voulu, garde-le. Si un jour tu désinstalles Embody, le bloc part seul.
- **`AGENTS.md`** : Embody régénère le sien (le fichier est "always written"). Si le nôtre a été remplacé — le titre `TD Factory: a two agent pipeline` a disparu — restaure-le :

```bash
git checkout -- AGENTS.md
```

  Puis réouvre le projet une ou deux fois pour vérifier si Embody le réécrit à chaque démarrage. Si c'est le cas, deux options : réécrire le fichier à chaque fois (un `git checkout -- AGENTS.md`), ou déplacer le contenu de l'usine dans un fichier que Embody ne touche pas (ex. `FACTORY.md`) référencé depuis `CLAUDE.md` et son bloc Embody. À décider quand tu l'auras observé.
- **`.gitignore`** : Embody y a ajouté `.mcp.json`, `.embody/`, `.claude/settings.local.json` — normal, ce sont des fichiers runtime régénérés. Vérifie par contre que `*.toe` **n'y figure pas** : cette usine versionne les `.toe` (elle n'ignore que les backups TD, `*.[0-9].toe`). Si Embody a ajouté une ligne `*.toe`, supprime-la.
- **`.claude/skills/`** : les ~14 skills Embody (`create-operator`, `mcp-tools-reference`, `td-api-reference`, `visual-aesthetics`, `pop-networks`, ...) s'ajoutent aux nôtres (`td-architect`, `td-builder`, `td-auto-improve`). C'est un plus direct pour le Builder : conventions TD détaillées chargées à la demande.

### 4d. Committer

```bash
git add -A
git commit -m "seed: Embody + Envoy configures"
```

---

## Tester la connexion (optionnel, rassurant)

1. Dans TD, clique sur le COMP `Embody` > page **Envoy** : le bouton **Launch AI Client** ouvre Claude Code déjà pointé sur la racine du dépôt.
2. Ou dans un terminal, depuis la racine du dépôt : `claude`.
3. Demande : *"list all operators in the project"*. Si la liste revient, la chaîne complète fonctionne.

**Pour opencode** (l'agent de cette session) : page **Envoy** du COMP, paramètre **Configure For** > ajouter **OpenCode**. La génération est additive : elle ajoute `opencode.json` et les skills partagés sans toucher à la config Claude Code. Tout autre client MCP (Codex, Cursor, Gemini) se configure pareil.

---

## Dépannage

| Symptôme | Remède |
|---|---|
| La ligne du Textport échoue (réseau/checksum) | `.tox` manuel depuis `github.com/dylanroscover/Embody/releases/latest`, drag & drop dans le réseau |
| Le wizard ne s'ouvre pas | Pulse **Setup Wizard** sur la page de paramètres du COMP Embody (il s'y rouvre, préréglé sur tes choix actuels) |
| `check_env.py` : `envoy listening -> no localhost listener` | Vérifie **Envoy Enable** sur la page Envoy du COMP ; le serveur démarre au premier enable |
| Port 9870 occupé | Normal si plusieurs instances TD avec Envoy : chaque instance prend 9870–9879, pas d'action |
| `.mcp.json` écrit au mauvais endroit | Paramètre **AI Project Root** sur la page Envoy : remets `gitroot`, puis `op.Embody.InitEnvoy()` dans le Textport pour régénérer |
| AGENTS.md réécrit à chaque démarrage TD | Voir 4c — `git checkout -- AGENTS.md`, et si ça persiste, déplacer le canon de l'usine hors d'`AGENTS.md` |

Toute erreur dont tu identifies la cause et vérifies le fix : leçon dans `knowledge/lessons.yaml` (skill `td-auto-improve`). Le seed fait partie de l'usine, ses erreurs aussi.

---

## Après

- **Mise à jour d'Embody** : re-sauvegarde simplement `templates/seed.toe` après l'update.
- **Régénérer la config MCP sans wizard** : `op.Embody.InitEnvoy()` dans le Textport.
- **Changer un choix du wizard** : chaque écran correspond à un paramètre du COMP Embody (Mode, Configure For, Tool Permissions, AI Project Root, Envoy Enable...) — pas besoin de le repasser.
- Une fois `SEED READY` : `/new-td-project <ta phrase>` dans une session Architecte, et le premier build peut partir.
