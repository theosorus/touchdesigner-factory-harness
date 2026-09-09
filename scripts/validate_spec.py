#!/usr/bin/env python3
"""Gate between the Architect and the Builder.

Usage:
    python scripts/validate_spec.py <slug>

Checks that a spec is executable: required fields present, stage graph sane,
budgets coherent, acceptance criteria machine checkable. Exit code 0 means the
Builder is allowed to start. Anything else is a hard stop.

Only dependency is PyYAML. If it is missing the script says so and exits 3
rather than pretending the spec is valid.
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML is required: pip install pyyaml", file=sys.stderr)
    raise SystemExit(3)

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_TOP = ("slug", "title", "intent", "output", "inputs",
                "budget", "pipeline", "acceptance", "risks", "deliverables")
REQUIRED_OUTPUT = ("mode", "resolution", "target_fps", "fps_tolerance", "final_op")
REQUIRED_STAGE = ("id", "responsibility", "consumes", "produces", "budget_ops")

# criteria phrased like these are not checkable by a tool call
VAGUE = ("looks", "feels", "nice", "beautiful", "organic", "good", "cool",
         "joli", "beau", "sympa", "propre")


def fail(errors: list[str], msg: str) -> None:
    errors.append(msg)


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2

    slug = sys.argv[1]
    path = ROOT / "projects" / slug / "spec.yaml"
    if not path.exists():
        print(f"no spec at {path}", file=sys.stderr)
        return 2

    spec = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    errors: list[str] = []
    warnings: list[str] = []

    for key in REQUIRED_TOP:
        if key not in spec or spec[key] in (None, ""):
            fail(errors, f"missing top level field: {key}")
    if errors:
        report(errors, warnings)
        return 1

    if spec["slug"] != slug:
        fail(errors, f"slug mismatch: folder {slug!r} vs spec {spec['slug']!r}")

    raw = path.read_text(encoding="utf-8")
    for marker in ("my-project", "Two to five sentences",
                   "one sentence, what this stage produces",
                   "responsibility: ...", "{{"):
        if marker in raw:
            fail(errors, f"template placeholder left in the spec: {marker!r}")

    out = spec["output"]
    for key in REQUIRED_OUTPUT:
        if key not in out:
            fail(errors, f"output.{key} is missing")
    if out.get("mode") not in ("realtime", "render"):
        fail(errors, "output.mode must be realtime or render")

    budget = spec["budget"]
    stages = spec["pipeline"] or []
    if not stages:
        fail(errors, "pipeline has no stages")
    if len(stages) > budget.get("max_stages", 6):
        fail(errors, f"{len(stages)} stages exceeds budget.max_stages")

    ids: list[str] = []
    total_ops = 0
    for i, stage in enumerate(stages):
        label = stage.get("id", f"#{i}")
        for key in REQUIRED_STAGE:
            if key not in stage:
                fail(errors, f"stage {label}: missing {key}")
        sid = stage.get("id")
        if sid in ids:
            fail(errors, f"duplicate stage id: {sid}")
        ids.append(sid)
        total_ops += stage.get("budget_ops", 0)

        produces = stage.get("produces", "")
        if produces and not produces.startswith("out_"):
            fail(errors, f"stage {label}: produces must be a Null named out_*")

        for dep in stage.get("consumes") or []:
            if dep not in ids[:-1]:
                fail(errors, f"stage {label}: consumes {dep!r}, "
                             "which is not an earlier stage")

        for par in stage.get("params") or []:
            if not par.get("help"):
                fail(errors, f"stage {label}: parameter "
                             f"{par.get('name', '?')} has no help text")

    if total_ops > budget.get("max_ops_total", 40):
        fail(errors, f"sum of stage budgets ({total_ops}) exceeds "
                     f"budget.max_ops_total ({budget.get('max_ops_total')})")

    if not any(s.get("produces") and out.get("final_op", "").endswith(s["produces"])
               for s in stages):
        warnings.append("output.final_op does not match any stage Null; "
                        "make sure the final chain is explicit")

    acc = spec["acceptance"] or []
    if len(acc) < 3:
        fail(errors, "at least 3 acceptance criteria are required")
    for crit in acc:
        text = str(crit.get("check", "")).lower()
        if not text:
            fail(errors, f"acceptance {crit.get('id', '?')}: empty check")
        if any(word in text for word in VAGUE):
            fail(errors, f"acceptance {crit.get('id', '?')}: not machine "
                         f"checkable ({text[:50]!r})")

    if not spec["risks"]:
        fail(errors, "risks is empty")

    for inp in spec["inputs"] or []:
        if inp.get("source") != "mock" and not inp.get("mock"):
            warnings.append(f"input {inp.get('name')}: no mock declared, "
                            "the pipeline cannot be built without the real source")

    report(errors, warnings)
    return 1 if errors else 0


def report(errors: list[str], warnings: list[str]) -> None:
    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    if not errors:
        print("OK    spec is executable, the Builder can start")


if __name__ == "__main__":
    raise SystemExit(main())
