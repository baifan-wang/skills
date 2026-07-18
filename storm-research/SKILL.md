---
name: storm-research
description: Run STORM-style multi-perspective research and evidence-grounded synthesis with the host agent's native reasoning and worker capabilities. Use for literature or industry reviews, contradiction mapping, question-first writing, cited reports, citation audits, or research over local workspace materials before drafting.
---

# Portable STORM Research

Rebuild the STORM/Co-STORM method as a portable Agent Skills workflow. Use the host's main agent as orchestrator and its child-agent, subagent, task-worker, or team feature for independent roles. Let native agent reasoning replace external LLM calls. Use real local or retrieved material as evidence; never treat model memory or agreement among roles as evidence.

## Load supporting references

- Read [roles.md](references/roles.md) before assigning research, writing, or audit workers.
- Read [artifacts.md](references/artifacts.md) before creating persistent research artifacts or a cited report.
- Read [platform-adapters.md](references/platform-adapters.md) when installing the Skill or mapping it to a host's tools.
- Read [source-mapping.md](references/source-mapping.md) only when explaining or extending the mapping from Stanford STORM/Co-STORM.

## Discover host capabilities

Before execution, identify which capabilities the host provides. Do not assume product-specific tool names.

- local file listing, search, and reading;
- document-format parsing when relevant;
- child agents, subagents, task workers, or agent teams;
- external web, database, or academic retrieval;
- shell or Python execution;
- persistent file writing.

Choose the strongest available implementation while preserving the workflow contracts:

- If isolated workers exist, assign independent roles through them.
- If only agent teams exist, keep evidence IDs and the final ledger owned by one orchestrator to avoid concurrent conflicts.
- If no worker feature exists, execute roles sequentially in the main agent and save each role packet before switching perspectives.
- If Python is unavailable, perform citation mapping and validation manually against [artifacts.md](references/artifacts.md).
- If network retrieval is unavailable or forbidden, remain local-only and report gaps instead of using model memory.

## Choose depth and source mode

Choose a depth:

- `quick`: 3 perspectives, one research pass, contradiction map, evidence-grounded briefing, and compact audit.
- `standard`: 3-5 perspectives in batches, one follow-up pass, refined outline, section drafting, citation audit, and critical review. Use by default.
- `rigorous`: 5-8 perspectives in batches, explicit search strategy, structured evidence table, iterative retrieval, detailed section writing, and independent citation or method review. Use for literature reviews or high-stakes work.

Choose a source mode:

- `local-only`: Use only files placed in scope. Do not retrieve external material.
- `hybrid`: Inspect local sources first, then retrieve only what is missing.
- `web-first`: Use when current external research is explicitly requested and local material is secondary.
- `interactive`: Apply a selected source mode but pause at user-selected scope, perspective, or outline checkpoints.

Record both choices in `00-scope.md`. Default to `standard` + `hybrid` unless the request clearly requires another mode.

## Orchestration rules

1. Keep planning, global source IDs, evidence merging, and final delivery in the orchestrator.
2. Treat the real user as the Co-STORM human participant; do not simulate the user unless explicitly requested.
3. Keep role workers as leaves. Do not allow them to create nested workers unless the host specifically requires hierarchical delegation.
4. Run perspective workers independently without sharing other perspectives' conclusions before their first pass.
5. Reserve capacity for the orchestrator. Batch roles according to the host's concurrency limit rather than assuming a fixed number.
6. Give every worker a bounded question, source policy, input artifact list, output contract, and stop condition.
7. Let each perspective worker preserve its own ask -> retrieve -> answer from evidence -> identify gap -> follow-up context.
8. Prefer evidence records over polished prose during research.
9. Keep reported results, source-author interpretations, and cross-source inferences visibly separate.
10. Never let multiple workers append concurrently to the global evidence ledger. Merge role packets serially.

## Workflow

### 1. Define scope

Inspect the current workspace before asking questions. Resolve or reasonably state:

- topic, decision, and requested deliverable;
- audience and output form;
- included and excluded subtopics;
- date, language, geography, and source-type limits;
- source mode, citation style, and depth.

Ask the user only when a missing choice would materially change the result.

### 2. Build perspectives and a question tree

Assign a `persona-planner` role. Require topic-specific perspectives rather than a fixed generic list. Always include basic facts and at least one adversarial, limitations, or evidence-quality angle.

Produce:

- each perspective's unique remit and exclusions;
- 3-6 questions per perspective;
- dependencies among questions;
- one likely blind spot;
- a deduplicated, progressive question tree.

The orchestrator removes overlapping roles before research begins.

### 3. Research independently

Assign one `perspective-researcher` role per accepted perspective, in batches when necessary. Each worker must:

- inspect relevant local material before external retrieval;
- use the host's format-aware readers when needed;
- retrieve external sources only when the selected mode permits it;
- prefer primary, official, or peer-reviewed sources appropriate to the domain;
- record sources, evidence units, and atomic claims with separate stable IDs;
- distinguish support, contradiction, context, and inference;
- surface missing evidence and useful follow-up questions;
- avoid drafting the final report.

Run one targeted follow-up pass for unresolved high-value questions in `standard` mode and iterative retrieval in `rigorous` mode. Stop when new work mostly duplicates existing evidence or reaches the agreed limit.

### 4. Consolidate and map contradictions

Assign a `contradiction-analyst` role the independent role packets, not a prewritten conclusion. Require:

- evidence-backed consensus;
- direct conflicts with claims and sources from both sides;
- conditional differences caused by population, method, timeframe, definition, or incentives;
- evidence-strength comparison without majority voting;
- missing perspectives and excluded claims.

Let the orchestrator assign global IDs and create `03-evidence-ledger.md` and `04-contradiction-map.md`.

### 5. Refine the outline from evidence

For `standard` or `rigorous` depth, preserve a short baseline outline based only on scope. Then assign an `outline-editor` role the scope, question tree, evidence ledger, contradiction map, and baseline outline.

Require every substantive section to identify:

- the question it answers;
- its analytical claim or comparison;
- supporting and counterevidence IDs;
- unresolved caveats;
- its relationship to adjacent sections.

Remove decorative sections with no evidence.

### 6. Draft by section

Assign `section-writer` roles in batches. Give each one only the approved section brief, relevant evidence, necessary neighboring summaries, and style constraints.

Require analytical synthesis instead of source-by-source summaries. Do not allow facts or citations outside the supplied evidence packet. Cite evidence placeholders such as `[@E001]`; do not create local numeric reference lists.

### 7. Audit and challenge

Run two independent gates:

1. `citation-auditor`: map every verifiable sentence to evidence; flag unsupported, overstated, misplaced, or context-breaking citations and broken locators.
2. `critical-reviewer`: challenge scope, reasoning, source bias, contradictions, missing perspectives, gap claims, and practical implications.

Revise only against specific findings. Preserve unresolved disagreements in the final report.

### 8. Finalize and deliver

After the audited draft is stable:

- Run `python scripts/validate_run.py <run-directory>` when Python is available.
- Run `python scripts/finalize_citations.py <draft.md> <03-evidence-ledger.md> <report.md> --map <citation-map.json>` to map evidence placeholders to unique source numbers.
- If the host resolves Skill-relative paths through an environment variable, use it; otherwise resolve paths relative to this `SKILL.md` directory.

Deliver the requested report with a concise methods note covering depth, source mode, perspectives, evidence limitations, unresolved conflicts, and created artifacts.

## Quality gates

- `Scope`: research question and boundaries are explicit.
- `Perspectives`: roles are distinct and include an adversarial angle.
- `Evidence`: factual claims have sources and locators; missing details remain missing.
- `Outline`: every substantive section maps to a question and evidence.
- `Draft`: synthesis preserves uncertainty and counterevidence.
- `Citations`: every verifiable sentence is supported at the strength stated.
- `Review`: major objections are resolved or disclosed.

## Hard constraints

- Do not invent citations, metadata, quotations, locators, samples, effects, or conclusions.
- Do not turn one source author's interpretation into a field-level result.
- Do not infer a research gap merely because the current retrieval found little evidence.
- Do not use agreement among roles as proof; roles may share the same source bias.
- Do not browse in local-only mode.
- Do not call external LLM APIs merely to reproduce STORM; use the host agent's native reasoning.
- Do not claim publication readiness solely because the report contains citations.
