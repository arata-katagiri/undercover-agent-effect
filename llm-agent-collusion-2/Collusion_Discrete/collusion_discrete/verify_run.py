"""Audit raw experiment records and reproduce every reported analysis value."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

from .analyze import analyze as analyze_confirmatory
from .analyze_adaptive import analyze as analyze_adaptive
from .adaptive_roles import AgentMemory, parse_decision
from .game import Choice, DiscreteCoalitionGame


MANIFEST = "RAW_DATA.sha256"


def _raw_files(run_dir: Path) -> Iterable[Path]:
    for name in ("experiment.json", "episodes.csv", "summary.csv"):
        path = run_dir / name
        if path.exists():
            yield path
    yield from sorted((run_dir / "game_record").glob("*.json"))


def _digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_manifest(run_dir: Path) -> None:
    lines = [f"{_digest(path)}  {path.relative_to(run_dir)}" for path in _raw_files(run_dir)]
    (run_dir / MANIFEST).write_text("\n".join(lines) + "\n")


def check_manifest(run_dir: Path) -> int:
    path = run_dir / MANIFEST
    if not path.exists():
        return 0
    checked = 0
    for line in path.read_text().splitlines():
        expected, relative = line.split("  ", 1)
        actual = _digest(run_dir / relative)
        if actual != expected:
            raise AssertionError(f"checksum mismatch: {relative}")
        checked += 1
    return checked


def _audit_history(record: Dict[str, Any]) -> None:
    count = len(record.get("roles", [])) or len(record["history"][0]["choices"])
    game = DiscreteCoalitionGame(agent_count=count)
    for expected_round, observed in enumerate(record["history"], start=1):
        if observed["round"] != expected_round:
            raise AssertionError(f"non-sequential round in {record.get('scenario', record['condition'])}")
        choices = {
            int(actor): Choice(choice["action"], choice["target"])
            for actor, choice in observed["choices"].items()
        }
        replayed = game.step(choices)
        report_rewards = defaultdict(float)
        for verdict in observed.get("report_verdicts", []):
            report_rewards[int(verdict["reporter"])] += float(verdict["reward"])
        for agent in range(count):
            expected_delta = float(replayed["deltas"][str(agent)]) + report_rewards[agent]
            actual_delta = float(observed["deltas"][str(agent)])
            if abs(expected_delta - actual_delta) > 1e-9:
                raise AssertionError(f"bad payoff delta in round {expected_round}, agent {agent}")
            game.scores[agent] += report_rewards[agent]
            if abs(game.scores[agent] - float(observed["scores"][str(agent)])) > 1e-9:
                raise AssertionError(f"bad cumulative score in round {expected_round}, agent {agent}")
        if abs(sum(game.scores.values()) - float(observed["social_welfare"])) > 1e-9:
            raise AssertionError(f"bad welfare in round {expected_round}")

    if "final_scores" in record:
        for agent, score in record["final_scores"].items():
            if abs(game.scores[int(agent)] - float(score)) > 1e-9:
                raise AssertionError("final score does not match replay")
    else:
        if abs(game.scores[0] - float(record["provocateur_score"])) > 1e-9:
            raise AssertionError("provocateur score does not match replay")
        if abs(game.scores[1] - float(record["target_score"])) > 1e-9:
            raise AssertionError("target score does not match replay")


def _history_key(record: Dict[str, Any], kind: str) -> Tuple[Any, ...]:
    if kind == "confirmatory":
        return (int(record["seed"]),)
    return (record["match_group"], int(record["seed"]))


def _record_key(record: Dict[str, Any], kind: str) -> Tuple[str, int, int]:
    name = record["condition"] if kind == "confirmatory" else record["scenario"]
    return (str(name), int(record["seed"]), int(record["replicate"]))


def _audit_csv_rows(rows: list[Dict[str, str]], records: list[Dict[str, Any]], kind: str) -> None:
    """Require every value consumed by analysis to be an exact export of a raw record."""
    record_by_key = {_record_key(record, kind): record for record in records}
    if len(record_by_key) != len(records):
        raise AssertionError("duplicate raw-record identity")
    seen = set()
    for row in rows:
        name = row["condition"] if kind == "confirmatory" else row["scenario"]
        key = (name, int(row["seed"]), int(row["replicate"]))
        if key not in record_by_key:
            raise AssertionError(f"CSV row has no matching raw record: {key}")
        if key in seen:
            raise AssertionError(f"duplicate CSV identity: {key}")
        seen.add(key)
        record = record_by_key[key]
        for field, observed in row.items():
            if field not in record:
                raise AssertionError(f"CSV field {field!r} missing from raw record {key}")
            expected = "" if record[field] is None else str(record[field])
            if observed != expected:
                raise AssertionError(
                    f"CSV/raw mismatch for {key}, field {field}: {observed!r} != {expected!r}"
                )
    if seen != set(record_by_key):
        raise AssertionError("one or more raw records have no matching CSV row")


def _audit_adaptive_raw_decisions(record: Dict[str, Any]) -> int:
    """Check retained model JSON against the action actually scored.

    Deterministic smoke policies have no raw model text and are intentionally skipped. A malformed
    final response is accepted only when the logged fail-closed fallback is PUBLIC.
    """
    checked = 0
    count = len(record["roles"])
    fallback_keys = {
        (int(event["agent_id"]), int(event["round"]))
        for event in record.get("action_repair_events", [])
        if event.get("fallback") == "PUBLIC"
    }
    for logged in record.get("decision_log", []):
        raw = logged.get("raw", "")
        if not raw:
            continue
        agent = int(logged["agent"])
        round_number = int(logged["round"])
        observed = record["history"][round_number - 1]["choices"][str(agent)]
        memory = AgentMemory("audit", {}, [], [])
        try:
            parsed = parse_decision(
                raw,
                agent_id=agent,
                valid_targets=[candidate for candidate in range(count) if candidate != agent],
                memory=memory,
            ).choice
        except ValueError:
            if (agent, round_number) not in fallback_keys or observed != {
                "action": "PUBLIC", "target": None
            }:
                raise AssertionError(
                    f"invalid raw decision without matching PUBLIC fallback: agent {agent}, "
                    f"round {round_number}"
                )
        else:
            if observed != {"action": parsed.action, "target": parsed.target}:
                raise AssertionError(
                    f"raw/scored action mismatch: agent {agent}, round {round_number}"
                )
        checked += 1
    return checked


def audit(run_dir: Path, kind: str) -> Dict[str, Any]:
    rows = list(csv.DictReader((run_dir / "episodes.csv").open()))
    records = [json.loads(path.read_text())
               for path in sorted((run_dir / "game_record").glob("*.json"))]
    if not rows or len(rows) != len(records):
        raise AssertionError("episodes.csv and raw JSON record counts differ or are empty")
    expected = json.loads((run_dir / "experiment.json").read_text()).get("episodes")
    if expected is not None and int(expected) != len(records):
        raise AssertionError("experiment.json episode count differs from raw records")
    _audit_csv_rows(rows, records, kind)

    grouped: Dict[Tuple[Any, ...], set[str]] = defaultdict(set)
    raw_decisions_checked = 0
    for record in records:
        _audit_history(record)
        if kind == "adaptive":
            raw_decisions_checked += _audit_adaptive_raw_decisions(record)
        if not record.get("pre_intervention_matched"):
            raise AssertionError("record is not marked pre-intervention matched")
        prehistory = json.dumps(record["history"][:5], sort_keys=True, separators=(",", ":"))
        grouped[_history_key(record, kind)].add(prehistory)
    mismatched = [key for key, histories in grouped.items() if len(histories) != 1]
    if mismatched:
        raise AssertionError(f"pre-intervention histories differ for {mismatched[:3]}")

    stored = json.loads((run_dir / "analysis.json").read_text())
    reproduced = analyze_confirmatory(run_dir) if kind == "confirmatory" else analyze_adaptive(run_dir)
    reproduced["run_dir"] = stored.get("run_dir", reproduced["run_dir"])
    if reproduced != stored:
        raise AssertionError("analysis.json does not exactly reproduce from episodes.csv and records")

    return {
        "kind": kind,
        "episodes": len(records),
        "matched_units": len(grouped),
        "rounds_replayed": sum(len(record["history"]) for record in records),
        "manifest_files_checked": check_manifest(run_dir),
        "analysis_exactly_reproduced": True,
        "csv_rows_exactly_match_raw": True,
        "payoffs_exactly_replayed": True,
        "pre_intervention_matching_verified": True,
        "retained_raw_decisions_checked": raw_decisions_checked,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--kind", choices=("auto", "confirmatory", "adaptive"), default="auto")
    parser.add_argument("--write-manifest", action="store_true")
    args = parser.parse_args()
    kind = args.kind
    if kind == "auto":
        metadata = json.loads((args.run_dir / "experiment.json").read_text())
        kind = "adaptive" if metadata.get("exploratory") else "confirmatory"
    if args.write_manifest:
        write_manifest(args.run_dir)
    print(json.dumps(audit(args.run_dir, kind), indent=2))


if __name__ == "__main__":
    main()
