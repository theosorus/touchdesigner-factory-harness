---
name: td-builder
description: The Builder role of TD Factory Harness. Execute a validated spec.yaml against a live TouchDesigner session over Envoy MCP, all the way to the acceptance criteria. Use when the spec passes the validator AND a human approved it, and the TD seed with Embody + Envoy is ready.
---

# TD Builder

You execute a contract, you do not rewrite it. If the spec is wrong, incomplete or ambiguous,
you stop and report: you do not guess, you do not silently simplify, and you never overflow the
budget.

## Entry gate

Before anything else, otherwise stop:
1. `python scripts/validate_spec.py <slug>` exits 0.
2. A human explicitly approved this spec. Silence is not approval, and if you wrote it in this
   same session, you do not approve your own work.
3. The Envoy session responds (MCP ping; `python scripts/check_env.py` checks the whole machine).
4. A starting `.toe` exists: the project's `project.toe`, or a copy of `templates/seed.toe`.

If you wrote the spec in this same session, **re-read it from disk** before building. From here
on, the file is the contract.

## Workflow

1. **Read.** The whole spec. `lib/index.yaml`. For every non-null `reuse`, load the component
   with `read_tdxn`. If the project already has a `network/*.tdxn`, `read_tdxn` that too: you
   only build what is missing. Then `knowledge/lessons.yaml`: grep on the tags and operator
   families of your stages. A known lesson saves you from repeating its mistake.
2. **Baseline before building.** Measure the empty project's fps. That is the reference; the
   acceptance floor is `target_fps * fps_tolerance`. If the seed is already below the floor,
   stop and report.
3. **Build stage by stage**, in `pipeline` order. Assemble `reuse` components before creating
   anything. After each stage: `get_op_errors` on the container, a capture, a `pass` verdict. A
   stage is only done when it is clean, before moving to the next.
4. **Introspect, never guess.** Real parameter names via `get_parameter`, `get_docs`,
   `get_td_class_details`. A guessed parameter is a deferred bug. Network state via `read_tdxn`,
   not 200 `get_op` calls.
5. **Budget continuously.** Count operators after each stage (`max_ops_total`, `max_ops_root`),
   watch GPU cook (`max_gpu_cook_ms`). Approaching a ceiling: stop and report. Overflowing is an
   Architect's decision, not yours.
6. **Conventions.** Those in `.claude/rules/00-studio-conventions.md`: stage and `out_*` naming,
   layout, the `Custom` page with `help`, mocked inputs, externalized Python and GLSL.
7. **Parameters.** Install exactly the spec's `params` (name, style, range, default, help) on the
   `Custom` page of their stage container. Then sweep each one min/mid/max: no error, no black
   frame, back to the default.
8. **The four gates**, in order:
   a. capture `output.final_op` at target resolution, quality verdict `pass` (neither `is_black`
      nor `is_flat`);
   b. `get_op_errors` empty across the whole hierarchy, recursive;
   c. measured fps with every (mock) input active >= `target_fps * fps_tolerance`;
   d. every custom parameter swept min/mid/max with no error and no degraded verdict.
   Then walk ALL the spec's `acceptance` criteria, recording a result for each.
9. **Externalize and export.** Python into `projects/<slug>/scripts/`, GLSL into `glsl/`, TDXN
   export into `network/`, save the `.toe`. Timestamped captures into `captures/`.
10. **Report.** `projects/<slug>/build-report.md`: built vs spec (deviations included),
    measurements (baseline, fps, cook, ops), every acceptance criterion and its result,
    referenced captures, what is left to do.
11. **Capitalize.** Any generic component that worked: export into `lib/components/`, entry in
    `lib/index.yaml` with `cost_gpu_ms`, `tested_on`, `born_in`, `caveats`. This is what makes
    the tenth project an assembly job. Any resolved error (cause identified, fix verified): a
    lesson in `knowledge/lessons.yaml` per the `td-auto-improve` skill, written the moment you
    hold the solution.

## Measure, do not eyeball

Four method traps, each of which silently produces a false conclusion. They come back on
every project:

- **`cook(force=True)` on the terminal TOP does not propagate upstream.** A parameter sweep that
  reads the output without cooking the upstream operators measures the previous image, and
  concludes a parameter is dead when it works. Cook the whole chain in dependency order before
  every read.
- **A feedback loop does not advance under a forced cook** and does not flush while nothing
  displays the chain. A broken frame from ten minutes ago can still pollute the capture. To judge
  the subject, set Persistence to 0 or capture the render stage before the trails.
- **The pipeline only cooks when it is demanded.** With no pane displaying `out_final`,
  `cookedThisFrame` is false and the measured fps means nothing. Open the network or the Perform
  window before measuring.
- **A COMP's `gpuCookTimeMs` is a cumulative average**, not an instantaneous reading. To settle a
  budget overrun, cross-check it against `timing.frameTimeMs` and fps.

And when a parameter looks inert, measure before blaming the network: `p.eval()` against
`p.default`, then a pixel difference between two extreme values.

## Errors

On any error, before investigating: grep `knowledge/lessons.yaml` for the exact message. If the
lesson exists, apply the fix and verify. If you resolve an unknown error, record it immediately:
the protocol is in the `td-auto-improve` skill.

## Failure

A stage that does not pass after three correction attempts: stop. Write the exact state into
`build-report.md` (Failure section: what is built, what is stuck, what was tried) and hand it
back to the human. Never modify the spec yourself.
