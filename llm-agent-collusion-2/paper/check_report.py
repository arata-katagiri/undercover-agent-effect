"""Check that the official-template report contains the audited result values."""
from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree


W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def docx_text(path: Path) -> tuple[list[str], str]:
    with zipfile.ZipFile(path) as archive:
        root = ElementTree.fromstring(archive.read("word/document.xml"))
    tokens = [node.text or "" for node in root.iter(W + "t")]
    return tokens, re.sub(r"\s+", " ", " ".join(tokens)).strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docx", type=Path, required=True)
    parser.add_argument("--adaptive-analysis", type=Path, required=True)
    args = parser.parse_args()
    adaptive = json.loads(args.adaptive_analysis.read_text())
    tokens, text = docx_text(args.docx)

    forbidden = ("PROJECT TITLE", "Author name", "Summarize your project",
                 "How to use this template", "[Reference", "placeholder", "TBD")
    found = [value for value in forbidden if value.lower() in text.lower()]
    if found:
        raise AssertionError(f"template or draft text remains: {found}")

    required = (
        "0.680", "0.965", "1.91 × 10⁻⁶", f"{adaptive['episodes']} fresh episodes",
        f"seeds were {min(adaptive['seeds'])}-{max(adaptive['seeds'])}",
        "Codex proposed the core research idea", "Umar Abdilaipov proposed the subsequent variations",
        "takes responsibility for the claims",
    )
    missing = [value for value in required if value not in text]
    if missing:
        raise AssertionError(f"required audited values or disclosures missing: {missing}")

    try:
        start = tokens.index("Abstract") + 1
        end = tokens.index("1. Introduction")
    except ValueError as error:
        raise AssertionError("could not locate abstract boundaries") from error
    abstract = " ".join(tokens[start:end])
    words = re.findall(r"\b[\w'-]+\b", abstract)
    if not 150 <= len(words) <= 250:
        raise AssertionError(f"abstract has {len(words)} words; expected 150-250")

    print(json.dumps({
        "docx": str(args.docx),
        "abstract_words": len(words),
        "no_template_placeholders": True,
        "confirmatory_values_present": True,
        "adaptive_episode_count_present": True,
        "llm_usage_disclosure_present": True,
    }, indent=2))


if __name__ == "__main__":
    main()
