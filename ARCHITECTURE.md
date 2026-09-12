# TD Factory Harness: architecture

A factory for TouchDesigner projects driven by two agent roles. You write a sentence, you get
a running `.toe`, version-controlled and verified.

## The principle

The problem with an agent building TouchDesigner on its own is that it has no contract. It
improvises, piles up operators, and forty turns later you have a network nobody can read. The
fix is to cut the work in two, with a written artifact in between.

```
human prompt
    |
    v
[Agent 1: Architect]  ------> projects/<slug>/spec.yaml   (contract, reviewed by you)
    |                                    |
   no MCP,                               |
   no TD open                            v
                            [Agent 2: Builder] -----> live TD session over Envoy
                                         |                     |
                                         v                     v
                              build-report.md          project.toe + .tdxn + captures
```

`spec.yaml` is the checkpoint. Until it is approved, nothing is built. Once approved it
outlives the session: another agent, a sub-agent, or you three weeks later can replay it.

## Why two roles rather than one

| | Architect | Builder |
|---|---|---|
| Input | a vague sentence | a validated spec.yaml |
| Output | a spec.yaml | a running TD project |
| Tools | files, web search, reading `lib/` | Envoy MCP, files |
| TD open | no | yes |
| Context | wide, exploratory | narrow, executive |
| Mode | plan mode | execution |
| Cost of failure | you re-read 60 lines of YAML | you throw away 40 minutes of build |

Splitting moves the cost of a mistake from the build to the review. A wrong spec is fixed in
thirty seconds.

The two roles may share one session — that is cheaper in context. What must not be skipped is
the gate: the validator exits 0, **and** a human approves in writing. An agent never approves
its own spec, and silence is not approval. When both roles share a session, the Builder
re-reads `spec.yaml` from disk before building: from that point the file is the contract, not
the memory of having written it.

## The seven layers

**1. The contract (`templates/spec.template.yaml`)**
The schema the Architect fills in. It forces the decisions that are expensive to change later:
resolution, target fps, operator budget, inputs, exposed parameters, stage breakdown,
acceptance criteria.

**2. The conventions (`.claude/rules/`)**
Loaded in every conversation. Naming, layout, container structure, TD Python rules. This is
what makes two projects generated three months apart read the same way.

**3. The skills (`.claude/skills/`)**
`td-architect` and `td-builder`, loaded on demand. They hold workflows, not conventions.

**4. The library (`lib/`)**
The real long-term lever. Every component that works is exported as TDXN and indexed. By
project 10, the Builder assembles more than it builds. That is when a factory starts paying
off.

**5. The projects (`projects/<slug>/`)**
One self-contained folder per project: its spec, its `.toe`, its externalized code, its
captures and its build report.

**6. Verification**
No build is "finished" without: a capture with a `pass` quality verdict, `get_op_errors` empty
across the hierarchy, fps within tolerance of the baseline measured before the build, and
every custom parameter exercised at its bounds.

**7. The error memory (`knowledge/lessons.yaml`)**
Every resolved error with an identified cause and a verified fix becomes a greppable lesson,
shared by all agents and all harnesses. Three occurrences of the same pattern and the lesson
gets promoted into a convention. This is what stops a factory making the same mistake twice.

## Repository layout

```
td-factory/
├── AGENTS.md                   # canonical entry point for any agent, not just Claude
├── CLAUDE.md                   # global context, read on every Claude session
├── ARCHITECTURE.md             # this file
├── .claude/
│   ├── rules/
│   │   └── 00-studio-conventions.md
│   ├── skills/
│   │   ├── td-architect/SKILL.md
│   │   ├── td-builder/SKILL.md
│   │   └── td-auto-improve/SKILL.md
│   └── commands/
│       ├── new-td-project.md    # /new-td-project <prompt>
│       └── build-td-project.md  # /build-td-project <slug>
├── templates/
│   ├── spec.template.yaml
│   └── project-README.md
├── scripts/
│   ├── new_project.py           # scaffold a project folder
│   └── validate_spec.py         # the gate: is this spec executable
├── lib/
│   └── index.yaml               # registry of reusable TDXN components
├── knowledge/
│   └── lessons.yaml             # error memory, shared across agents
└── projects/
    └── <slug>/
        ├── spec.yaml            # the contract
        ├── project.toe          # binary, not diffable
        ├── network/             # TDXN exports, the readable source of truth
        ├── scripts/             # externalized python
        ├── glsl/                # externalized shaders
        ├── assets/
        ├── captures/            # timestamped visual evidence
        ├── build-report.md      # what the Builder did and verified
        └── README.md
```

## What an agent needs on hand to do this work

An agent building TD needs seven things, and at least three are always missing when it goes
wrong:

1. **A written contract** of what it must produce, with checkable criteria. Otherwise it
   declares victory too early.
2. **API introspection**: the real parameter names, not the guessed ones. Envoy provides
   `get_docs`, `get_td_class_details`, `get_parameter`.
3. **Visual feedback with a machine verdict**: a capture it can look at, plus an
   `is_black` / `is_flat` / `pass` it can read without looking.
4. **The real state of the network** in few tokens. `read_tdxn` rather than 200 `get_op`
   calls.
5. **A budget**: operator count, GPU cook time, fps floor. Without a budget it builds until it
   stutters.
6. **A library** of what already worked. Otherwise it reinvents the same feedback loop on
   every project, with a different bug each time.
7. **An error memory**: what already cost time and how it was resolved. Otherwise every agent
   repeats the same mistake, also with a different bug each time.

## Requirements

- TouchDesigner 2025.33070 or newer
- Embody + Envoy installed in the seed `.toe` (the Setup Wizard writes `.mcp.json`,
  Embody's `.claude/rules/` and `.claude/skills/`)
- An MCP-capable agent: Claude Code, or any other that reads `AGENTS.md` (the canonical,
  harness-independent entry point)
- Python 3.11+ for the scaffold scripts

Coexistence note: Embody generates its own files under `.claude/`. This factory's files are
prefixed (`00-studio-conventions.md`) or carry names that do not collide (`td-architect`,
`td-builder`). Embody keeps a fingerprint of what it generates and does not overwrite a file
you edited — but it never renames one of its own files either.
