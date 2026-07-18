import sys
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import argparse
import json
import re
from pathlib import Path


EVIDENCE_HEADER = re.compile(r"^###\s+(E\d+)\s*$", re.MULTILINE)
SOURCE_FIELD = re.compile(r"^-\s+Source ID:\s*(S\d+)\s*$", re.MULTILINE)
CITATION_GROUP = re.compile(r"\[((?:@E\d+\s*(?:[;,]\s*)?)+)\]")
EVIDENCE_TOKEN = re.compile(r"@?(E\d+)")


def parse_evidence_sources(ledger_text: str) -> dict[str, str]:
    matches = list(EVIDENCE_HEADER.finditer(ledger_text))
    mapping: dict[str, str] = {}
    for index, match in enumerate(matches):
        evidence_id = match.group(1)
        block_end = matches[index + 1].start() if index + 1 < len(matches) else len(ledger_text)
        block = ledger_text[match.end():block_end]
        source_match = SOURCE_FIELD.search(block)
        if source_match:
            mapping[evidence_id] = source_match.group(1)
    return mapping


def finalize(text: str, evidence_to_source: dict[str, str]) -> tuple[str, dict[str, int]]:
    source_to_number: dict[str, int] = {}

    def replace_group(match: re.Match[str]) -> str:
        evidence_ids = EVIDENCE_TOKEN.findall(match.group(1))
        numbers: list[int] = []
        for evidence_id in evidence_ids:
            source_id = evidence_to_source.get(evidence_id)
            if source_id is None:
                raise ValueError(f"Citation references unknown or unmapped evidence ID: {evidence_id}")
            if source_id not in source_to_number:
                source_to_number[source_id] = len(source_to_number) + 1
            number = source_to_number[source_id]
            if number not in numbers:
                numbers.append(number)
        return "".join(f"[{number}]" for number in numbers)

    return CITATION_GROUP.sub(replace_group, text), source_to_number


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert STORM evidence placeholders to stable numeric source citations."
    )
    parser.add_argument("draft", type=Path)
    parser.add_argument("ledger", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--map", dest="map_path", type=Path)
    args = parser.parse_args()

    draft_text = args.draft.read_text(encoding="utf-8")
    ledger_text = args.ledger.read_text(encoding="utf-8")
    evidence_to_source = parse_evidence_sources(ledger_text)
    finalized, source_to_number = finalize(draft_text, evidence_to_source)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(finalized, encoding="utf-8")

    if args.map_path:
        used_evidence = sorted(set(EVIDENCE_TOKEN.findall(" ".join(CITATION_GROUP.findall(draft_text)))))
        payload = {
            "evidence_to_source": {
                evidence_id: evidence_to_source[evidence_id] for evidence_id in used_evidence
            },
            "source_to_number": source_to_number,
        }
        args.map_path.parent.mkdir(parents=True, exist_ok=True)
        args.map_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    print(f"Finalized {len(source_to_number)} unique source citations -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
