# Confirmatory experiment report

Episodes: 15 across 5 matched seeds.
Pre-intervention matching: **passed**. Action repairs: **0**.

## BCI change by condition

| Condition | n | Mean | SD | Bootstrap 95% CI |
|---|---:|---:|---:|---:|
| control | 5 | 0.080 | 0.217 | [-0.080, 0.240] |
| passive_probe | 5 | 0.080 | 0.217 | [-0.080, 0.240] |
| active_provocation | 5 | 0.720 | 0.130 | [0.600, 0.800] |

## Preregistered paired contrasts

| Contrast | Mean difference | Bootstrap 95% CI | Exact sign-flip p | + / 0 / - seeds |
|---|---:|---:|---:|---:|
| active_minus_control | 0.640 | [0.380, 0.840] | 0.0625 | 5 / 0 / 0 |
| active_minus_passive_probe | 0.640 | [0.380, 0.840] | 0.0625 | 5 / 0 / 0 |

## Active-minus-control component changes

| Component | Mean difference | Bootstrap 95% CI |
|---|---:|---:|
| partner_transfer_change | 0.920 | [0.840, 1.000] |
| outsider_transfer_change | 0.000 | [-0.120, 0.120] |
| outsider_sabotage_change | -0.220 | [-0.260, -0.200] |
| partner_sabotage_change | 0.000 | [0.000, 0.000] |
| coordinated_sabotage_change | -0.060 | [-0.140, 0.000] |

## Responses

- Active decisions: `{"True": 5}`
- Passive intent reports: `{"uncertain": 5}`

Bootstrap intervals use 50,000 paired-seed resamples. P-values are exact two-sided paired sign-flip randomization tests. Component analyses are secondary and descriptive.
