# Research artifact contract

Use persistent artifacts for long or high-stakes work. Store them under a user-selected directory or, by default, `.storm-research/<topic-slug>/` beneath the current workspace.

## Directory layout

```text
00-scope.md
01-personas.md
02-question-tree.md
research/
  <perspective>.md
03-evidence-ledger.md
04-contradiction-map.md
05-baseline-outline.md
05-outline.md
draft/
  <section>.md
06-citation-audit.md
07-critical-review.md
report.md
```

Create only artifacts needed for the requested depth. A quick briefing may combine planning files and omit per-section drafts.

## Stable identifiers

- Use `S001`, `S002`, ... for sources.
- Use `E001`, `E002`, ... for located evidence units.
- Use `C001`, `C002`, ... for atomic claims.
- Never reuse an ID for a different source or claim.
- Keep stable IDs through drafting and auditing. Section writers cite `[@E001]`; convert these placeholders to the requested citation style only in the final merge.

## Source record

```markdown
### S001
- Type: local | web | paper | official | dataset | other
- Title:
- Author or organization:
- Date:
- Path, URL, DOI, or database ID:
- Locator: page, section, heading, line, table, figure, or paragraph
- Accessed: YYYY-MM-DD, when relevant
- Quality notes:
```

For local files, use a resolvable path and line, heading, page, sheet, or slide locator. For web sources, link the exact supporting page. For papers, record DOI or stable database ID when available.

## Evidence record

```markdown
### E001
- Claim IDs: C001
- Normalized claim:
- Evidence layer: reported result | source-author interpretation | cross-source inference
- Status: supported | contradicted | mixed | contextual | inference
- Source ID: S001
- Locator:
- Evidence summary:
- Directness: direct | indirect
- Source quality: high | medium | low
- Confidence: high | medium | low
- Scope conditions:
- Limitations:
- Recorded by:
```

Do not merge two independently testable assertions into one claim. Create separate evidence records when a claim uses different source locations. If the claim is an inference across sources, state the reasoning and preserve the supporting claims. If a source does not report a detail, record `not reported` rather than completing it from context.

## Contradiction record

```markdown
### X001: <issue>
- Position A: C... supported by E...
- Position B: C... supported by E...
- Difference type: factual | definitional | methodological | temporal | population | value judgment
- Evidence comparison:
- Resolution: resolved | conditional | unresolved
- Treatment in report:
```

## Section brief

```markdown
## <section>
- Question answered:
- Thesis:
- Supporting claims:
- Counterclaims:
- Evidence IDs allowed:
- Required caveats:
- Excluded material:
- Target length and style:
```

## Citation audit rule

Audit every externally verifiable sentence. A source must support the exact proposition at the strength stated. A citation is inadequate when it only concerns the same topic, supports a narrower population, reports correlation while the sentence claims causation, or reflects an author's interpretation presented as an observed result.

Do not let parallel section writers create numeric references. Keep `[@E...]` placeholders until the audited sections are merged. Map evidence IDs to source IDs, then number unique sources by first appearance in the merged report.

## Final evidence status

Use one of these labels when uncertainty matters:

- `well supported`: multiple independent, direct, suitable sources or one decisive primary source;
- `provisionally supported`: direct but limited evidence;
- `contested`: credible evidence points in different directions;
- `insufficient evidence`: available material cannot justify the claim;
- `inference`: transparent synthesis that is not directly stated by a source.

Never convert `insufficient evidence` into a fact during polishing.
