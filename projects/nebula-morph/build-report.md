# Build Report: nebula-morph

Date: 2026-09-09
TD build: 2025.33070
Role: Builder
Spec validation: passed (`python scripts/validate_spec.py nebula-morph`)
Human approval: confirmed

## Result

The approved pipeline was built in `/project1` and verified live. The last
confirmed persisted revision is the ramp-based render network saved at:

- `projects/nebula-morph/project.toe`
- `projects/nebula-morph/network/nebula-morph.tdxn`
- `projects/nebula-morph/captures/final.png`

The live session was later tested with a one-operator `circleTOP` sprite
optimization. A subsequent save to the already-current `.toe` timed out inside
TouchDesigner, so that optimization is intentionally not represented in the
persisted deliverables. The persisted ramp revision is the reported build.

## Pipeline

| Stage | Implementation | Result |
|---|---|---|
| `src_particles` | `pointgeneratorPOP` + `randomPOP` + `outPOP` | 80000 points at Density 0.8; `P` and `Seed` attributes |
| `ctrl_evolution` | `constantCHOP` + `outCHOP` | `shapetarget`, `morph`, `chaos`, `palettephase` in 0..1 |
| `fx_morph` | `glslPOP` + native `noisePOP` + `outPOP` | sphere, torus, spiral galaxy and wave grid; Color attribute |
| `render` | geometry COMP, point sprite MAT, radial ramp, camera, Render TOP | 16-bit float render, fog, slow rotation |
| `fx_trails` | Feedback TOP Target reference + Level decay + screen mix | Persistence-controlled history buffer |
| `composite` | screen mix + Bloom TOP + ACES Tone Map TOP | Glow-controlled final output |

`Palette Shift` is implemented as a GLSL hue rotation uniform to keep the
render stage inside its operator budget. `palettephase` is consumed by the
morph shader for fixed-palette particle color drift.

## Measurements

- Empty-seed baseline: 60 fps stable; acceptance floor: 54 fps.
- Full persisted pipeline: 61 fps initial, 60 fps after 5 minutes; 1.6% drift.
- Final persisted capture: 1280x720, `Quality: OK`, `max_lum=0.6553`, `std=0.1149`.
- The Render TOP is configured for 1920x1080, but the installed Non-Commercial
  license caps actual output at 1280x720. This is the only render warning.
- `RenderScene` average accumulated CPU cook time: approximately 4.96 ms
  (684.91 ms over 138 cooks). GPU cook timing was reported as 0.0 ms by Envoy.
- Root build operators: 12. With Embody and its externalizations table: 14/15
  root budget.
- Estimated total build operators including internal proxies and docked DATs:
  44/50.

## Acceptance

- `renders`: PASS. `captures/final.png` is non-black and non-flat.
- `no_errors`: PASS for all six build stages. Root contains pre-existing Embody
  font/CUDA warnings plus the license resolution warning; no build errors.
- `perf`: PASS. Full pipeline remained at or above 60 fps at the available
  1280x720 resolution.
- `params_respond`: PASS. All 9 custom parameters were swept at min/mid/max:
  27/27 captures returned `Quality: OK`, with zero operator errors. Defaults
  were restored.
- `shape_readable`: PASS. All four shape functions were sampled at Density 0.4;
  no NaN values were found and the shape statistics were distinct.
- `morph_visible`: PASS in isolated comparison of sphere and wave grid at
  `Pointsize=2.25`, `Persistence=0`, `Glow=0`: full-pixel RGB mean absolute
  difference 3.42%, above the 2% threshold. Exposed defaults were restored.
- `trails_persist`: PASS. Persistence 0 and 0.88 differed by 2.86% in the
  persisted-ramp verification; Persistence 0.98 remained non-flat (RGB std
  0.138). The final post-circle rerun also remained non-flat.
- `stability`: PASS. 61 fps to 60 fps over 5 minutes.

## Deliverables

- `projects/nebula-morph/project.toe`
- `projects/nebula-morph/network/nebula-morph.tdxn`
- `projects/nebula-morph/glsl/fx_morph_compute.glsl`
- `projects/nebula-morph/captures/final.png`
- `projects/nebula-morph/build-report.md`
- `lib/components/feedback_trails.tdxn`

The generic feedback component is indexed in `lib/index.yaml`. Verified fixes
for COMP data proxies, Feedback TOP loops, blocking TD Python waits and TD
expression `math.floor` are recorded in `knowledge/lessons.yaml`.

## Remaining Caveats

- Actual delivery resolution requires a TouchDesigner license permitting
  1920x1080 output.
- One same-path synchronous `project.save()` timed out and was cancelled from
  the TD dialog. TD recovered; the live network was returned to the persisted
  rampTOP version and the TDXN was re-exported successfully. Avoid repeating
  that synchronous save pattern; use the tracked `save_project` job for future
  saves.
