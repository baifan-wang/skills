# Role and handoff protocol

Use the host's main agent as orchestrator and moderator. Implement roles with child agents, subagents, task workers, team members, or sequential isolated passes. Role workers must not delegate further unless the host requires hierarchical execution.

## Common assignment block

Include this information in every worker assignment or sequential role pass:

```text
Topic and decision/deliverable:
Operating depth and allowed sources:
Included and excluded scope:
Files or artifacts to read:
Output contract:
Stop condition:
Do not draft beyond your assigned role. Do not invent evidence. Do not create nested workers.
```

## Persona planner

Purpose: convert scope into distinct research perspectives and a progressive question tree.

Output:

```markdown
## Perspective: <name>
- Unique remit:
- Explicit exclusions:
- Key questions:
- Expected source types:
- Likely blind spot:

## Question tree
- Q1 ...
  - Q1.1 ...
```

Select perspectives dynamically. Fixed generic personas such as practitioner, academic, skeptic, incentives analyst, and historian are starting heuristics, not mandatory roles. Always include a basic-facts role. Keep each first-pass role context independent from the others.

## Perspective researcher

Purpose: answer only one perspective's questions from permitted evidence. Within this role, preserve context across question -> retrieval -> evidence-grounded answer -> follow-up cycles.

Output:

```markdown
## Role and coverage
## Evidence records
### E001
- Claim IDs: C001
- Normalized claim:
- Evidence layer: reported result | source-author interpretation | cross-source inference
- Status: supported | contradicted | mixed | contextual | inference
- Source ID:
- Locator:
- Evidence summary:
- Source quality: high | medium | low
- Confidence: high | medium | low
- Limitations:
## Conflicts and ambiguities
## Missing evidence
## Follow-up questions
```

Keep claims atomic. Prefer paraphrase. Mark any reasoning that combines sources as an inference.

## Contradiction analyst

Purpose: compare independent role findings without smoothing away disagreement.

Output:

```markdown
## Consensus
## Direct contradictions
| Issue | Claim A and sources | Claim B and sources | Likely reason | Resolution status |
## Conditional differences
## Evidence-strength ranking
## Blind spots
## Excluded claims
```

Do not select a winner solely by number of sources or agreeing roles. Compare source design, independence, directness, recency when relevant, population, and claim fit.

## Outline editor

Purpose: derive structure from research questions and evidence.

Output each section as:

```markdown
## <section title>
- Question answered:
- Section thesis:
- Evidence IDs:
- Counterevidence IDs:
- Caveats:
- Transition:
```

Reject any substantive section that has neither evidence nor an explicit label as background, hypothesis, or open question.

## Section writer

Purpose: write one approved section from a limited evidence packet.

Rules:

- Lead with the section's analytical claim.
- Compare sources where they differ in method, population, definition, or period.
- Cite at sentence or clause level using evidence placeholders such as `[@E001]`.
- Preserve uncertainty and counterevidence.
- End with a transition or bounded conclusion.
- Return a list of used and unused evidence IDs after the draft.

## Citation auditor

Purpose: verify claim-to-source alignment, not merely citation presence.

Output:

```markdown
| Sentence or claim | Source ID | Locator checked | Support strength | Problem | Required fix |
```

Flag unsupported synthesis, overgeneralization, swapped populations, causal language from correlational evidence, source metadata gaps, and citations placed after claims they do not support.

## Critical reviewer

Purpose: attack the completed argument as an independent reviewer.

Assess scope, coverage, source selection, reasoning, contradictions, missing perspectives, gap claims, and actionability. Rank findings as blocking, major, or minor. Recommend concrete revisions rather than rewriting the report wholesale.

## Synthesis editor

Purpose: merge audited sections and apply only justified revisions.

Preserve disagreements, normalize terminology and citation formatting, remove duplicated prose, and write the executive summary last. Do not introduce new claims during polishing.
