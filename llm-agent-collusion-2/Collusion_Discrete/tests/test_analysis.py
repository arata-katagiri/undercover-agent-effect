import csv
import json

from collusion_discrete.analyze import analyze, exact_sign_flip_p


def test_exact_sign_flip_detects_consistently_positive_paired_effect():
    assert exact_sign_flip_p([1.0, 1.0, 1.0]) == 0.25


def test_analyze_matched_run(tmp_path):
    fields = [
        "condition", "replicate", "seed", "accepted", "reported_preexisting_intent",
        "action_repair_count", "pre_intervention_matched", "bci_change",
        "partner_transfer_change", "outsider_transfer_change", "outsider_sabotage_change",
        "partner_sabotage_change", "coordinated_sabotage_change",
    ]
    with (tmp_path / "episodes.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for seed in (1, 2):
            for condition, value in (("control", 0.0), ("passive_probe", 0.0),
                                     ("active_provocation", 1.0)):
                row = {
                    "condition": condition, "replicate": seed, "seed": seed,
                    "accepted": "True" if condition == "active_provocation" else "",
                    "reported_preexisting_intent": "no" if condition == "passive_probe" else "",
                    "action_repair_count": 0, "pre_intervention_matched": "True",
                    "bci_change": value, "partner_transfer_change": value,
                    "outsider_transfer_change": 0, "outsider_sabotage_change": 0,
                    "partner_sabotage_change": 0, "coordinated_sabotage_change": 0,
                }
                writer.writerow(row)
                records = tmp_path / "game_record"
                records.mkdir(exist_ok=True)
                (records / f"{condition}_{seed}.json").write_text(json.dumps({
                    "condition": condition,
                    "final_scores": {"0": 1.0, "1": 2.0, "2": 3.0, "3": 3.0},
                    "social_welfare": 9.0,
                }))
    result = analyze(tmp_path)
    assert result["primary_contrasts"]["active_minus_control"]["mean_difference"] == 1.0
    assert result["all_pre_intervention_histories_matched"] is True
    assert result["final_score_summary"]["control"]["mean_target_score"] == 2.0
