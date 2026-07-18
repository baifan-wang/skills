# Platform adapters

Keep the core workflow platform-neutral. Map capabilities by purpose rather than hard-coding tool names.

## Required and optional capabilities

Minimum requirement:

- load a directory-based Skill with `SKILL.md`;
- read local text files or accept supplied material.

Optional capabilities improve execution:

- child agents, subagents, tasks, or agent teams for isolated perspectives;
- web, academic, or database retrieval for hybrid research;
- shell and Python for deterministic validation and citation numbering;
- persistent writes for resumable run artifacts.

If optional capabilities are absent, follow the fallback rules in `SKILL.md`.

## Agent Skills compatible hosts

This directory follows the Agent Skills open structure:

```text
storm-research/
├── SKILL.md
├── references/
└── scripts/
```

Install the whole directory in the host's documented Skill location. Preserve relative paths and UTF-8 encoding.

## Claude Code

Install as either:

- project Skill: `.claude/skills/storm-research/`
- personal Skill: `~/.claude/skills/storm-research/`

Invoke explicitly with `/storm-research` or let Claude load it from the description. Claude Code can implement independent roles with subagents; agent teams are optional and should still use one orchestrator-owned evidence ledger. Do not depend on Claude-only frontmatter so the same directory stays portable.

## Codex

Install under the configured Codex skills directory, commonly `$CODEX_HOME/skills/storm-research/` or the platform's personal Skill location. Invoke with the host's Skill syntax, commonly `$storm-research`. Map independent roles to the available collaboration or subagent feature; otherwise use sequential role passes.

## Other agent software

For a host that supports the Agent Skills standard, install the directory unchanged. For a host with a different extension format:

1. Use `SKILL.md` as the main workflow prompt.
2. Keep `references/` as on-demand context.
3. Keep `scripts/` as optional deterministic utilities.
4. Map these abstract operations to host tools: inspect files, retrieve evidence, create isolated workers, wait for results, send follow-ups, persist artifacts, and execute Python.
5. If the host cannot load supporting files, concatenate only the reference needed for the current phase instead of permanently loading all references.

## Worker semantics

Different roles do not require different model providers. They require:

- isolated first-pass context;
- distinct role remit and question scope;
- identical evidence output contracts;
- orchestrator-controlled merging and global IDs.

When a host offers no true context isolation, emulate it by completing and saving one role packet before reading or generating the next role's findings.

## Python utilities

The bundled scripts require Python 3.9+ and only the standard library. They are optional when the host cannot execute Python, but their checks must then be performed manually.
