import sys
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import argparse
import re
from collections import Counter
from pathlib import Path


SOURCE_HEADER = re.compile(r"^###\s+(S\d+)\s*$", re.MULTILINE)
EVIDENCE_HEADER = re.compile(r"^###\s+(E\d+)\s*$", re.MULTILINE)
SOURCE_FIELD = re.compile(r"^-\s+Source ID:\s*(S\d+)\s*$", re.MULTILINE)
LOCATOR_FIELD = re.compile(r"^-\s+Locator:\s*(.+?)\s*$", re.MULTILINE)
CITATION_TOKEN = re.compile(r"@?(E\d+)")
CITATION_GROUP = re.compile(r"\[((?:@E\d+\s*(?:[;,]\s*)?)+)\]")


def duplicate_values(values: list[str]) -> list[str]:
    return sorted(value for value, count in Counter(values).items() if count > 1)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an Agentic STORM run directory.")
    parser.add_argument("run_directory", type=Path)
    args = parser.parse_args()

    run_dir = args.run_directory.resolve()
    ledger_path = run_dir / "03-evidence-ledger.md"
    errors: list[str] = []

    if not ledger_path.is_file():
        print(f"FAIL: missing {ledger_path}")
        return 1

    ledger_text = ledger_path.read_text(encoding="utf-8")
    source_ids = SOURCE_HEADER.findall(ledger_text)
    evidence_matches = list(EVIDENCE_HEADER.finditer(ledger_text))
    evidence_ids = [match.group(1) for match in evidence_matches]

    for duplicate in duplicate_values(source_ids):
        errors.append(f"duplicate source ID: {duplicate}")
    for duplicate in duplicate_values(evidence_ids):
        errors.append(f"duplicate evidence ID: {duplicate}")

    source_set = set(source_ids)
    evidence_to_source: dict[str, str] = {}
    for index, match in enumerate(evidence_matches):
        evidence_id = match.group(1)
        block_end = evidence_matches[index + 1].start() if index + 1 < len(evidence_matches) else len(ledger_text)
        block = ledger_text[match.end():block_end]
        source_match = SOURCE_FIELD.search(block)
        locator_match = LOCATOR_FIELD.search(block)
        if source_match is None:
            errors.append(f"{evidence_id} has no Source ID")
        else:
            source_id = source_match.group(1)
            evidence_to_source[evidence_id] = source_id
            if source_id not in source_set:
                errors.append(f"{evidence_id} references missing source {source_id}")
        if locator_match is None or not locator_match.group(1).strip():
            errors.append(f"{evidence_id} has no locator")

    referenced_evidence: set[str] = set()
    checked_files = 0
    for path in sorted(run_dir.rglob("*.md")):
        if path == ledger_path:
            continue
        text = path.read_text(encoding="utf-8")
        groups = CITATION_GROUP.findall(text)
        if groups:
            checked_files += 1
        for group in groups:
            referenced_evidence.update(CITATION_TOKEN.findall(group))

    for evidence_id in sorted(referenced_evidence - set(evidence_ids)):
        errors.append(f"citation references missing evidence ID: {evidence_id}")
    for evidence_id in sorted(referenced_evidence):
        if evidence_id not in evidence_to_source:
            errors.append(f"cited evidence has no source mapping: {evidence_id}")

    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print(
        "PASS: "
        f"sources={len(source_ids)}, evidence={len(evidence_ids)}, "
        f"cited_evidence={len(referenced_evidence)}, citation_files={checked_files}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
