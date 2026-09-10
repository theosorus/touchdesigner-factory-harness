# Build Report: brain-eeg-cloud

Date: 2026-09-09 to 2026-09-10
TD build: 2025.33070
Role: Builder
Spec validation: `python scripts/validate_spec.py brain-eeg-cloud` exits `OK`
Human approval: explicit, before the build

## Result

The spec's six stages are built in `/project1`, verified live, and persisted. A surface
point-cloud brain breathes, lights up in a moving focal point and can be rotated with the
mouse, driven by a simulated EEG signal, over a bounded animated background, with comet
trails, glow and an ACES tone map.

Persisted deliverables:

- `network/brain-eeg-cloud.tdxn` (the readable structure)
- `project1/fx_pulse/glsl_pulse_compute.glsl` (the shader)
- `project1/render/mouse_orbit.py` (mouse rotation)
- `scripts/glb_to_ply.py` (glTF to surface point cloud converter)
- `captures/` (timestamped evidence for every pass)

The `.toe` and the mesh are deliberately not versioned: see this project's README.

## Pipeline as built

| Stage | Implementation | Ops (budget) |
|---|---|---|
| `ctrl_signal` | `noiseCHOP` -> `mathCHOP` (0-1) -> `lagCHOP` -> `mathCHOP` -> `switchCHOP` -> `limitCHOP` -> `outCHOP`, with an OSC branch `oscinCHOP` + `constantCHOP` -> `replaceCHOP` | 10 (10) |
| `src_cloud` | `pointfileinPOP` -> `randomPOP` -> `deletePOP` -> `transformPOP` -> `outPOP` | 5 (10) |
| `bg_aurora` | 2x `noiseTOP` simplex4D -> `compositeTOP` add -> `levelTOP` -> `lookupTOP` over a `rampTOP` -> multiply by a soft `circleTOP` | 10 (10) |
| `fx_pulse` | `inPOP` + `inCHOP` -> `glslPOP` (externalized compute) -> `outPOP` | 6 (12) |
| `render` | `geometryCOMP` (POP chain + `nullPOP` display/render) + `pointspriteMAT` + sprite `rampTOP` + camera + `renderTOP` 16-bit float + mouse orbit (`constantCHOP` + `executeDAT`) | 16 (14) |
| `composite` | `blurTOP` on the background -> brain composited `over` -> trails (`lib/feedback_trails`) added as light -> `bloomTOP` -> `tonemapTOP` ACES -> `outTOP` | 14 (14) |

Plus `ui_control`, a control panel outside the pipeline (see below).

Total: **73 operators** against a `max_ops_total` ceiling of 85. Root: 12 build operators
(+ Embody and its table) against `max_ops_root` 20.

## Measurements

| Measurement | Value |
|---|---|
| Empty seed baseline | 59-60 fps, 6.72 ms/frame, GPU 208 MB |
| Full pipeline, continuously demanded | **60-61 fps**, 6.5-11.1 ms/frame |
| GPU cook `/project1` | **6.0 ms** (spec ceiling: 10 ms) |
| GPU memory | 606 MB of 12,713 MB |
| Dropped frames | flat across the session |
| Effective resolution | 1280x720 (Non-Commercial licence ceiling) |

## Acceptance criteria

| Criterion | Result | Evidence |
|---|---|---|
| `renders` | **PASS** | `out_final` capture: `Quality: OK`, neither black nor flat |
| `no_errors` | **PASS** | recursive `get_op_errors` on `/project1`: 0 errors, 0 warnings across the six stages |
| `perf` | **PASS** | 60 fps with the mock active, floor 54 |
| `gpu_budget` | **PASS** | 6.5 ms/frame, ceiling 16 ms; GPU cook 6.0 ms, spec ceiling 10 ms |
| `params_respond` | **PASS** | every custom parameter swept min/mid/max, no black or flat frame, `get_op_errors` empty, defaults restored |
| `cloud_loaded` | **PASS**, with a deviation | `Density` 1.0 gives 215,591 surface points with `P`, `Seed` and `N`. The spec expected 262,254 points from the original solid cloud; the source changed mid-build |
| `upright` | **PASS** | `out_render` capture at Orbitspeed 0: non-black bounding box 646x687 px, taller than wide |
| `signal_drives_image` | **PASS** | Excitation 0 vs 1: **3.2%** mean absolute RGB difference over the full frame (threshold 3%), 7.1% over the brain region alone |
| `trails_persist` | **PASS** | Persistence 0 vs 0.9: 9.0% difference (threshold 2%); at 0.95 the image stays non-flat (std 0.183) |
| `background_animated` | **PASS** | two background probes differ by 12.7% over 14.8 s (threshold 1% over 3 s) |
| `background_recedes` | **PASS** | background mean 0.039 against 0.162 for the brain's core; after the bounding fix the background's brightest pixel stays 6.8x below the brain's mean |
| `no_white_clip` | **PASS** | at Excitation 1 and Glow 1: max_lum 0.88, **0%** clipped pixels |
| `osc_ready` | **PASS** | `Source` = osc: three channels in 0-1 cooking, `get_op_errors` empty, no hardware attached |
| `stability` | **PARTIAL** | see below |

## Stability: what was actually measured

The spec asks for fps after 10 minutes of continuous run, within 5% of the initial reading.
Honestly:

- across the whole session, every reading gave **60 or 61 fps**, and `droppedFrames` never moved
  from the value reached at TouchDesigner's launch, before anything was built;
- **caveat**: the chain only cooks while a pane displays `out_final`. When the TD window goes to
  the background, `cookedLastFrame` drops to false and the pipeline idles. So there is no
  guaranteed 10-minute window *under continuous load*. To validate it properly, open the Perform
  window on `out_final` and let it run — which is also an installation's real configuration.

## Deviations from the spec

1. **`render` does not consume `src_cloud` directly.** The spec declares
   `consumes: [src_cloud, fx_pulse]`. `fx_pulse` already carries the whole cloud (displaced
   position, `Seed`, `N`, `Color`); a second wire would have duplicated geometry for nothing.
2. **The shader is not under `glsl/`.** The spec lists `glsl/fx_pulse_compute.glsl`; Embody owns
   externalized file management (hard rule: never touch `file`/`syncfile` by hand) and writes it
   to `project1/fx_pulse/glsl_pulse_compute.glsl`, mirroring the network path. Conflict between
   the studio convention and Embody: **Embody wins**, because its rule is mechanical and tooled.
3. **`scripts/` holds a converter, not runtime code.** No runtime Python was needed for the
   pipeline itself: the logic lives in parameter expressions and the shader.
4. **Parameters beyond the spec**, added during the feedback passes: `Activity` and `Zonesize`
   for the activity focus, plus a redefinition of `Warmth` (violet share) and `Depthfade` (depth
   cues rather than fog). The spec declares 14 parameters, the project exposes 16.
5. **The source asset changed mid-build**: from a solid 262,254-point cloud to a 215,601-point
   surface cloud with normals. That is what made the shape readable at all; see
   `SURFACE-CLOUD-HOWTO.md`.
6. **`render` overflows its budget**: 16 operators against 14, caused by the three operators of
   the mouse orbit, which the spec did not anticipate.

Deviations 4, 5 and 6 all point the same way: **the contract no longer describes what exists**
and deserves an Architect pass before the next build.

## Human feedback passes

Four rounds after the first delivery, each starting from a stated problem:

| Reported problem | Cause found | Fix |
|---|---|---|
| The background competes with the brain | it was **added** on top of the brain, so it repainted it; the measured mean colour was near-grey | composite `over` so the brain occludes, blur on the background, soft centre darkening |
| No pink, everything blue | the camera fog, tinted deep navy, repainted every point: without it the mean went from (0.20/0.22/0.33) to (0.44/0.35/0.20) | fog removed, saturated pink/violet palette; brain saturation went from **0.22 to 0.61** |
| Poor quality, milky | soft heavily-overlapping sprites, plus a bloom threshold at 0.01 spilling over everything | crisp sprites, halved per-point brightness, bloom threshold raised to 0.48 |
| No visible brain activity | there was none: the signal only drove breathing, dispersion and global hue | **activity focus** in the shader: one moving centre with its own rhythm, lighting nearby points amber |
| The background still wins | not a level problem: a narrow input window over a drifting noise field meant the whole frame brightened whenever the noise rose (peak 0.08 to 0.30 depending on the moment) | widened input window and above all a **hard output ceiling**; the peak now stays between 0.027 and 0.037 at every phase |
| The rotation direction is ambiguous | kinetic depth ambiguity, not the wagon-wheel effect (no periodic pattern to alias) | three depth cues: back face **removed** (43.6% of points drawn), brightness decreasing with camera distance, lighting that rotates with the object |

## Incidents

**TouchDesigner froze during a TDXN export.** `export_network` on `/project1` with DAT content
wrote a 6.6 MB file — it descended into the whole interior of the Embody COMP — then blocked the
main thread: every Envoy tool timing out, no logs, no crash dump, process alive at 50-110% CPU
for 15 minutes. The `.toe` had not been saved yet, but the TDXN written just before the freeze
held the entire build. After the human's decision: `kill -9`, relaunch on the seed, then
`importNetworkFromFile` of the TDXN trimmed to the six stages — **78 operators rebuilt, zero
errors**, identical render. Cause and cure are in `knowledge/lessons.yaml`
(`tdxn-export-including-embody-freezes-td`): tag `op.Embody` with `tdxn_exclude` before any root
export. The same export then returns 13 operators, 25 KB, instantly.

**A second crash** hit while editing the shader, right after a save. Nothing was lost: the
`.toe` had been saved 30 seconds earlier and the externalized files were on disk.

## Control panel

`ui_control` is a Container COMP whose background is `out_final`, with a column anchored top
right by expression. It stacks six **Parameter COMPs**, one per stage, each scoped to its COMP's
Custom page. Consequence: adding a parameter to a stage makes it appear in the panel untouched,
with its range, default and help text. The Perform window points at `ui_control`.

Two traps: the anchor origins placed the panel at x = -330, y = -600, entirely off-frame; and
the parent's `verttb` alignment prevented children from rendering. Note also that the OP Viewer
TOP does not render nested Parameter COMP content, so a capture cannot prove the assembled
panel — only the real window can.

## Capitalization

Two generic components exported to `lib/` and indexed: `signal_mock_osc` (normalized 0-1 signal
source, mock or OSC, switchable without rewiring) and `aurora_backdrop` (animated backdrop with
an editable palette and a bounded output). `feedback_trails` was reused from `lib/` as the spec
required.

Eight verified lessons were added to `knowledge/lessons.yaml` during this build, bringing it to
twelve.

## What is left

- Connect the real headset: set `Source` to osc and point `ctrl_signal/oscin_eeg`'s port at the
  device. The OSC addresses must produce channels named `alpha`, `beta`, `theta`; the constant
  guarantees three channels even with no stream.
- 1920x1080 output requires a licence other than Non-Commercial.
- The contract needs an Architect pass to absorb the six deviations above.
