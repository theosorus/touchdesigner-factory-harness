# Preparing the TD seed (once, about five minutes)

**What you produce**: `templates/seed.toe`, a blank TouchDesigner project containing Embody +
Envoy, configured for this repository. Every scaffolded project starts from that seed —
`scripts/new_project.py` copies it to `projects/<slug>/project.toe` with Embody and Envoy
already inside.

**Prerequisites**

| Requirement | Note |
|---|---|
| TouchDesigner 2025.33070+ | any licence; Non-Commercial caps render output at 1280x720 |
| A git repository | this repo, cloned |
| Python 3.11+ with PyYAML | for the scaffold and validation scripts |
| Embody + Envoy | installed by this guide |

Check the machine at any time:

```bash
python3 scripts/check_env.py
```

Before this guide it prints `NOT READY` (missing `.mcp.json`, Envoy bridge, seed.toe). At the
end: `SEED READY`.

**Overview**

| # | Action | Where | Time |
|---|---|---|---|
| 0 | Commit the factory | Terminal | 20 s |
| 1 | Save the blank project as `templates/seed.toe` | TouchDesigner | 30 s |
| 2 | Install Embody (one line in the Textport) | TouchDesigner | 1 min |
| 3 | Walk the Setup Wizard | TouchDesigner | 2 min |
| 4 | Verify, reconcile, commit | Terminal + TD | 1 min |

Why save *before* installing (step 1 before 2): the wizard requires an already-saved project —
otherwise its first screen is "Save your project", and everything it configures lands *relative
to the project folder*. Saving in the right place first makes that screen disappear and puts the
configuration at the repo root.

---

## Step 0 — Commit the factory

The wizard writes into this repo: `.mcp.json`, `.embody/`, files under `.claude/`, and possibly
a regenerated `AGENTS.md`. A clean commit first guarantees nothing of yours can be lost, and lets
you see exactly what Embody adds (`git status`).

```bash
git add -A && git commit -m "factory before Embody"
```

---

## Step 1 — Save the blank project as the seed

In TouchDesigner:

1. If the currently open project is **not** blank: **File > New** (Cmd+N). An unsaved empty
   project works too.
2. **File > Save As** (Cmd+Shift+S).
3. Navigate to `<repo>/templates/seed.toe` and save.

The file is still an ordinary `.toe` — Embody arrives in the next step, and you will save once
more at the end so the seed actually contains it.

---

## Step 2 — Install Embody

1. Open the Textport: **Dialogs > Textport and DATs**, or **Alt+T**.
2. Paste the official one-liner (it downloads the latest release from GitHub, verifies its
   sha256, and loads the Embody COMP into the current network — exactly like dragging the `.tox`
   in):

```python
import requests, hashlib, tempfile, os; h = {'User-Agent': 'Embody-Install'}; mf = requests.get('https://github.com/dylanroscover/Embody/releases/latest/download/embody-release.json', headers=h, timeout=30).json(); b = requests.get('https://github.com/dylanroscover/Embody/releases/download/%s/%s' % (mf['tag'], mf['asset']), headers=h, timeout=120).content; assert hashlib.sha256(b).hexdigest() == mf['sha256'], 'checksum mismatch'; f = os.path.join(tempfile.gettempdir(), mf['asset']); open(f, 'wb').write(b); n = ui.panes.current; n = n if n.type == PaneType.NETWORKEDITOR else next(x for x in ui.panes if x.type == PaneType.NETWORKEDITOR); print('Embody', mf['version'], 'installed at', n.owner.loadTox(f).path)
```

3. Press Enter. TD pauses for a few seconds while it downloads, then the Textport prints
   something like `Embody 6.2.42 installed at /project1/Embody`, and the `Embody` COMP appears in
   the network.
4. Embody initializes within a few frames, then **the Setup Wizard opens on its own**.

**If the one-liner fails** (network, proxy, requests unavailable): download the `.tox` from
`github.com/dylanroscover/Embody/releases/latest` and drag it into the network — same result.

---

## Step 3 — The Setup Wizard, screen by screen

The wizard adapts: some screens only appear when their question applies. **Nothing changes until
the final click** — every screen only records a selection, and you can close it ("Not now") at
any point without touching the project.

| Screen | Choice | Why |
|---|---|---|
| 1. Save your project | **does not appear** (saved in step 1) | that is the point of saving first |
| 2. Mode | **Auto** | in Auto the AI config root is the git root automatically, which is what this factory wants |
| 3. Externalization | **New work only** — or absent on a blank project | the factory's externalization is driven by the Builder (TDXN over Envoy) |
| 4. AI assistant | **Claude Code** | generates `.mcp.json` plus a complete `.claude/` |
| 5. Pick your AI tool | does not appear (reserved for "Other AI tool") | — |
| 6. Permissions | **Don't ask**, or **Ask for some** if you prefer to approve writes | a build makes dozens of tool calls; the server only listens on 127.0.0.1 |
| 7. Convoy | **Keep Convoy Off** | Convoy drives several Embody nodes over the LAN and starts a host app at login; pointless on a single machine |
| 8. Git | does not appear when the repo already exists | Embody just adds its entries to your `.gitignore` / `.gitattributes` |
| 9. Footprint review | Advanced mode only | — |
| 10. Summary | review, then click **Set up Embody** | the only click that applies anything |

**What "Set up Embody" does**

- writes `.mcp.json` at the repo root (MCP connection for any compatible client);
- writes the `.embody/envoy-bridge.py` bridge and starts the Envoy server on `127.0.0.1:9870`
  (ports 9870-9879 when several instances run);
- writes its own rules and skills into `.claude/` (they sit alongside this factory's, which are
  prefixed or named `td-*`, so nothing collides), plus skills in `.agents/skills/` for
  Codex/Cursor/Gemini;
- regenerates its `AGENTS.md` and **merges** an auto-generated block into `CLAUDE.md`, delimited
  by a visible `## Embody / Envoy -- auto-generated section` heading: your own content is
  preserved;
- adds `.mcp.json`, `.embody/` and `.claude/settings.local.json` to `.gitignore` (runtime files,
  regenerated on startup);
- installs about 30 MB of Python dependencies in the background — TD stays responsive.

---

## Step 4 — Verify, reconcile, commit

### 4a. Save the seed again (crucial)

In TouchDesigner: **Cmd+S**. The `seed.toe` must contain a configured Embody — without this
second save, the file on disk is still the empty project from step 1.

### 4b. Check the machine

```bash
python3 scripts/check_env.py
```

You want `SEED READY`.

### 4c. Reconcile with this factory's files

Embody regenerates `AGENTS.md` for itself. This factory's `AGENTS.md` is the canonical entry
point for the two roles, so check `git diff AGENTS.md`: keep the factory's rules at the top and
let Embody's auto-generated block live below its own marker. The same applies to `CLAUDE.md`,
where Embody merges into a delimited section and leaves the rest alone.

### 4d. Commit

```bash
git add -A && git commit -m "seed: Embody + Envoy configured"
```

---

## Testing the connection (optional, reassuring)

Open an MCP client in the repo and ask it for `get_td_status`. It should report a live
TouchDesigner and a reachable Envoy. If TD is not running, `launch_td` starts it.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `check_env.py` still says NOT READY | the seed was not saved after the wizard | Cmd+S in TD (step 4a) |
| The MCP client sees no Envoy tools | `.mcp.json` written after the client started | restart the client session |
| `connected:false` while TD is running | the socket dropped | wait about 10 s: the bridge and the TD-side watchdog reconnect on their own |
| The wizard never opened | Embody still initializing, or already configured | open the Embody COMP and run the wizard from its parameters |

---

## After

Every new project starts from this seed. You will only come back here to upgrade Embody, or to
rebuild the seed on another machine.
