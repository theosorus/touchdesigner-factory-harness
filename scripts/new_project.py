#!/usr/bin/env python3
"""Scaffold a new TD Factory Harness project folder.

Usage:
    python scripts/new_project.py <slug> [--title "Human title"]

Creates projects/<slug>/ with the folder layout, a spec.yaml seeded from the
template, and a README. Does not create the .toe: the Builder does that by
copying the seed project or by launching TD.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUBDIRS = ("network", "scripts", "glsl", "assets", "captures")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def slugify(raw: str) -> str:
    s = raw.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return re.sub(r"-{2,}", "-", s)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--title", default=None)
    args = ap.parse_args()

    slug = slugify(args.slug)
    if not SLUG_RE.match(slug):
        print(f"invalid slug: {args.slug!r}", file=sys.stderr)
        return 2

    project = ROOT / "projects" / slug
    if project.exists():
        print(f"already exists: {project}", file=sys.stderr)
        return 1

    for sub in SUBDIRS:
        (project / sub).mkdir(parents=True, exist_ok=True)
        (project / sub / ".gitkeep").touch()

    title = args.title or slug.replace("-", " ").title()

    # seed the spec from the template, patching the identity fields only
    spec = (ROOT / "templates" / "spec.template.yaml").read_text(encoding="utf-8")
    spec = spec.replace("slug: my-project", f"slug: {slug}", 1)
    spec = spec.replace("title: My Project", f"title: {title}", 1)
    spec = re.sub(r"^created: .*$",
                  f"created: {dt.date.today().isoformat()}",
                  spec, count=1, flags=re.M)
    (project / "spec.yaml").write_text(spec, encoding="utf-8")

    readme = (ROOT / "templates" / "project-README.md").read_text(encoding="utf-8")
    readme = readme.replace("{{TITLE}}", title).replace("{{SLUG}}", slug)
    (project / "README.md").write_text(readme, encoding="utf-8")

    # optional seed .toe with Embody and Envoy already installed
    seed = ROOT / "templates" / "seed.toe"
    if seed.exists():
        shutil.copy2(seed, project / "project.toe")
        print("seeded project.toe from templates/seed.toe")

    print(f"created {project.relative_to(ROOT)}")
    print("next: fill spec.yaml, then run scripts/validate_spec.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
