# Mapping from STORM source to this Skill

This Skill preserves the research architecture of the local Stanford STORM source while replacing Python model calls with native reasoning and worker capabilities from any compatible agent host.

| Original component | Agentic replacement |
|---|---|
| `STORMWikiRunner` | Main-agent orchestrator and quality gates |
| `STORMWikiLMConfigs` and `knowledge_storm/lm.py` | Host-native reasoning; no external LLM API required |
| `StormPersonaGenerator` | `persona-planner` worker, retaining the fixed basic-facts role plus dynamic perspectives |
| `WikiWriter` | Perspective-specific question generation |
| `TopicExpert` and `ConvSimulator` | Independent `perspective-researcher` workers plus targeted follow-up tasks |
| `knowledge_storm/rm.py` retrievers | Host-provided local readers and web, database, or academic retrieval capabilities |
| `StormInformationTable` | Stable source records and atomic evidence ledger |
| `StormOutlineGenerationModule` | Baseline outline plus evidence-refined `outline-editor` pass |
| Semantic snippet retrieval | Orchestrator-selected evidence packets keyed by question, claim, and source IDs |
| `StormArticleGenerationModule` | Batched `section-writer` workers |
| `StormArticlePolishingModule` | `synthesis-editor`, followed by citation and critical-review gates |
| Co-STORM `DiscourseManager` | Main-agent moderator controlling turns, follow-ups, role updates, and user checkpoints |
| Co-STORM `KnowledgeBase` | Persistent scope, question tree, evidence, contradiction, outline, and draft artifacts |
| `post_run` logs | Methods note, provenance records, audit report, and created-file list |

## Adaptations from the local materials

The three Markdown materials in the source workspace contribute these safeguards and extensions:

- define scope before searching;
- build a progressive question tree, not a flat prompt list;
- map contradictions and blind spots explicitly;
- build an evidence table before drafting;
- distinguish reported results, source-author interpretation, and review-author synthesis;
- write by bounded section rather than generating the whole report at once;
- audit whether each citation supports the adjacent claim;
- run an adversarial peer-review pass;
- never invent unreported study details or unsupported research gaps.

Promotional claims about completing doctoral-level research in minutes are not operational requirements and must not appear as quality guarantees.
