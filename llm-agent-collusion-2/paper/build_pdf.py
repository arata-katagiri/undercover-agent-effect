"""Build the sprint submission PDF from verified experiment artifacts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIRMATORY = ROOT / "Collusion_Discrete/runs/confirmatory_20_20261025/analysis.json"
CONFIRMATORY_FIGURE = ROOT / "Collusion_Discrete/runs/confirmatory_20_20261025/RESULTS.png"


def p(text: str) -> str:
    return escape(text).replace("\n", "<br/>")


def fmt(value: float, digits: int = 3, sign: bool = False) -> str:
    return f"{value:+.{digits}f}" if sign else f"{value:.{digits}f}"


def styles():
    sheet = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "PaperTitle", parent=sheet["Title"], fontName="Times-Bold", fontSize=16,
            leading=18, alignment=TA_CENTER, spaceAfter=7,
        ),
        "subtitle": ParagraphStyle(
            "Subtitle", parent=sheet["Normal"], fontName="Times-Roman", fontSize=10.5,
            leading=12, alignment=TA_CENTER, spaceAfter=8,
        ),
        "author": ParagraphStyle(
            "Author", parent=sheet["Normal"], fontName="Times-Roman", fontSize=9.5,
            leading=11, alignment=TA_CENTER, spaceAfter=8,
        ),
        "abstract_head": ParagraphStyle(
            "AbstractHead", parent=sheet["Heading2"], fontName="Times-Bold", fontSize=10.5,
            leading=12, alignment=TA_CENTER, spaceBefore=3, spaceAfter=3,
        ),
        "abstract": ParagraphStyle(
            "Abstract", parent=sheet["Normal"], fontName="Times-Roman", fontSize=8.6,
            leading=10.4, alignment=TA_JUSTIFY, leftIndent=22, rightIndent=22, spaceAfter=7,
        ),
        "h1": ParagraphStyle(
            "H1", parent=sheet["Heading1"], fontName="Times-Bold", fontSize=12,
            leading=14, spaceBefore=8, spaceAfter=4, keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "H2", parent=sheet["Heading2"], fontName="Times-Bold", fontSize=10,
            leading=12, spaceBefore=6, spaceAfter=3, keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "Body", parent=sheet["BodyText"], fontName="Times-Roman", fontSize=8.55,
            leading=10.4, alignment=TA_JUSTIFY, spaceAfter=4.5,
        ),
        "bullet": ParagraphStyle(
            "Bullet", parent=sheet["BodyText"], fontName="Times-Roman", fontSize=8.45,
            leading=10.1, leftIndent=14, firstLineIndent=-8, spaceAfter=2,
        ),
        "caption": ParagraphStyle(
            "Caption", parent=sheet["Normal"], fontName="Times-Roman", fontSize=7.6,
            leading=9, alignment=TA_LEFT, spaceBefore=2, spaceAfter=5,
        ),
        "small": ParagraphStyle(
            "Small", parent=sheet["Normal"], fontName="Times-Roman", fontSize=7.6,
            leading=9.2, alignment=TA_LEFT, spaceAfter=3,
        ),
        "note": ParagraphStyle(
            "Note", parent=sheet["Normal"], fontName="Times-Italic", fontSize=7.8,
            leading=9.4, leftIndent=10, rightIndent=10, spaceAfter=4,
        ),
    }


def table(data, widths, *, header=True, font_size=7.4):
    item = Table(data, colWidths=widths, repeatRows=1 if header else 0, hAlign="CENTER")
    commands = [
        ("FONTNAME", (0, 0), (-1, -1), "Times-Roman"),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("LEADING", (0, 0), (-1, -1), font_size + 1.7),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LINEABOVE", (0, 0), (-1, 0), 0.8, colors.HexColor("#202020")),
        ("LINEBELOW", (0, -1), (-1, -1), 0.8, colors.HexColor("#202020")),
    ]
    if header:
        commands += [
            ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#ECEFF2")),
            ("LINEBELOW", (0, 0), (-1, 0), 0.55, colors.HexColor("#555555")),
        ]
    item.setStyle(TableStyle(commands))
    return item


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#B6BCC2"))
    canvas.setLineWidth(0.35)
    canvas.line(doc.leftMargin, 0.47 * inch, letter[0] - doc.rightMargin, 0.47 * inch)
    canvas.setFont("Times-Roman", 7.2)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawString(doc.leftMargin, 0.30 * inch, "The Undercover Agent Effect")
    canvas.drawRightString(letter[0] - doc.rightMargin, 0.30 * inch, str(doc.page))
    canvas.restoreState()


def contrast(adaptive, key):
    return adaptive["paired_contrasts"][key]


def make_pdf(adaptive_path: Path, output_path: Path) -> None:
    confirm = json.loads(CONFIRMATORY.read_text())
    adaptive = json.loads(adaptive_path.read_text())
    adaptive_figure = adaptive_path.parent / "RESULTS.png"
    s = styles()
    story = []

    story += [
        HRFlowable(width="100%", thickness=1.15, color=colors.black, spaceAfter=7),
        Paragraph("The Undercover Agent Effect: When Probing LLM Collusion Creates the Behavior It Seeks to Detect", s["title"]),
        Paragraph("A matched-seed audit in repeated allocation games", s["subtitle"]),
        HRFlowable(width="100%", thickness=0.45, color=colors.HexColor("#555555"), spaceBefore=1, spaceAfter=8),
        Paragraph("<b>Umar Abdilaiypov</b><br/>Independent Researcher<br/><b>With</b> Apart Research", s["author"]),
        Paragraph("Abstract", s["abstract_head"]),
        Paragraph(
            "Undercover agents are a natural proposal for auditing collusion among autonomous AI agents: offer a secret pact and observe who reciprocates. The same intervention, however, can manufacture the behavior it is meant to detect. We isolate this measurement effect in a 15-round, four-agent allocation game using Qwen2.5-7B-Instruct. Across 20 matched random seeds, a scripted trusted agent either sent no message, asked a non-directive passive question, or explicitly proposed preferential transfers and coordinated sabotage. Public pre-intervention trajectories were identical within each matched triplet. Active solicitation increased the target's preregistered Behavioral Collusion Index by 0.680 relative to both controls (paired bootstrap 95% CI [0.593, 0.758]; exact two-sided sign-flip p = 1.91 x 10^-6); all 20 paired effects were positive. The mechanism was almost entirely preferential transfers to the provocateur (+0.965), not increased outsider sabotage. Every target verbally accepted, while the target lost 6.9 points and the provocateur gained 22.45 points relative to control. We then ran an exploratory adaptive-memory matrix spanning direct and indirect manipulation, betrayal, rewarded reporting, false accusation, double agents, and sequential organizers. Reciprocation to a sting is causal evidence of susceptibility under solicitation, not evidence of a pre-existing coalition. Audits should separate revelation from inducement using matched no-message and passive-probe controls.",
            s["abstract"],
        ),
    ]

    story += [Paragraph("1. Introduction", s["h1"])]
    story.append(Paragraph(
        "LLM agents increasingly act in shared environments where private communication, repeated interaction, and asymmetric incentives can support undesirable coalitions. A proposed countermeasure is a trusted undercover agent that offers a collusive opportunity and logs reciprocation. This resembles a behavioral sting: it may expose a latent disposition, but it may also change the target's information and incentives enough to create the behavior.", s["body"]))
    story.append(Paragraph(
        "We ask a narrow causal question: <i>does an undercover collusion probe reveal a pre-existing tendency, or induce the behavior it seeks to detect?</i> Our contributions are:", s["body"]))
    for item in (
        "a preregistered, matched-seed design separating no probe, a non-directive passive probe, and active collusive solicitation;",
        "a behavioral index decomposed into favoritism, aggression, and synchronized-action components; and",
        "an exploratory adaptive-agent testbed for betrayal, indirect social-proof manipulation, incentivized reporting, false accusations, double agency, and sequential coalition recruitment.",
    ):
        story.append(Paragraph("- " + item, s["bullet"]))

    story += [Paragraph("2. Related Work", s["h1"])]
    story.append(Paragraph(
        "Zeng and Rudzicz [1] show that agents voluntarily adopt explicitly unfair secret tools across competitive and mixed-motive environments. Colosseum [2] audits action- and communication-level coalitions and finds both emergent collusion after secret-channel probes and \"collusion on paper,\" where stated plans and actions diverge. Agrawal et al. [3] find that direct communication increases collusive tendencies in double auctions and that oversight and urgency change behavior. Shi et al. [4] separate private plans, public announcements, and actions, finding that deception depends strongly on the game and is often premeditated.", s["body"]))
    story.append(Paragraph(
        "These studies establish that messages and opportunities can produce collusive behavior. We target a different identification problem: whether reciprocation <i>to the auditor's own proposal</i> should be interpreted as evidence that the target was already collusive. The intervention is treated as a possible cause, not merely a measurement instrument.", s["body"]))

    story += [Paragraph("3. Methods", s["h1"]), Paragraph("3.1 Game and model", s["h2"])]
    story.append(Paragraph(
        "Four agents play 15 simultaneous-action rounds. Each chooses KEEP (actor +2), PUBLIC (all active agents +1), TRANSFER(j) (target j +3, actor 0), or SABOTAGE(j) (actor +1, target j -2). Actions and scores become public after each round; private probes do not. Agent 0 is the scripted provocateur, Agent 1 is the target, and Agents 2-3 are outsiders. Non-scripted decisions use Qwen2.5-7B-Instruct with temperature 0.7, top-p 0.9, short JSON-only outputs, and explicit valid targets.", s["body"]))
    story.append(Paragraph(
        "Rounds 1-5 form the baseline. Before round 6, the target receives: (i) <b>control</b>, no message; (ii) <b>passive probe</b>, a question about already-planned favoritism or harm that explicitly is not a proposal, with its reply logged but withheld from later action prompts; or (iii) <b>active provocation</b>, a secret pact proposing preferential transfers to Agent 0, non-aggression toward it, and coordinated sabotage of outsiders, retained in later context. Agent 0 follows the same public post-trigger cycle in every condition: transfer to the target, sabotage Agent 2, sabotage Agent 3.", s["body"]))

    story.append(Paragraph("3.2 Outcome and confirmatory analysis", s["h2"]))
    story.append(Paragraph(
        "The preregistered Behavioral Collusion Index (BCI) scores target actions: +1 transfer to provocateur; -0.5 transfer to outsider; +1 sabotage outsider; -1 sabotage provocateur; and +1 additional point when target and provocateur sabotage the same outsider. KEEP and PUBLIC score zero. The episode outcome is post-intervention mean BCI minus pre-intervention mean BCI.", s["body"]))
    story.append(Paragraph(
        "The primary estimands are active-minus-control and active-minus-passive changes. We used 20 fresh seeds per condition after excluded smoke and calibration runs. Within a seed, model sampling seeds, roles, decoding, and pre-trigger prompts were identical; the run aborted if prehistories differed. Invalid actions received at most two logged deterministic corrective retries. We report 50,000-resample paired bootstrap intervals and an exact two-sided paired sign-flip test. Component outcomes are secondary.", s["body"]))

    story.append(Paragraph("3.3 Adaptive multi-role extension", s["h2"]))
    story.append(Paragraph(
        f"Before collection, we designated a 39-cell matrix as exploratory. Each non-scripted agent maintains bounded strategy, trust, suspects, commitments, and pact stance, supplemented by simulator-controlled facts. The matrix crosses four target roles (adaptive, loyalist, opportunist, double agent), direct/indirect/no solicitation, and promise-kept/betrayal schedules; adds three reporting rosters; and tests two sequential \"netter\" rosters. A first correct organizer report earns +2, a false report costs 1, duplicates score zero, and credibility updates from a Beta(1,1) prior. The fresh batch contains {adaptive['episodes']} episodes ({len(adaptive['seeds'])} seeds per cell); exact rounds 1-5 matching is mandatory.", s["body"]))

    story += [Paragraph("4. Results", s["h1"]), Paragraph("4.1 Active probing created discriminatory cooperation", s["h2"])]
    story.append(Paragraph(
        "The active proposal raised mean BCI change from 0.220 in both controls to 0.900. The paired active-minus-control effect was 0.680 (95% CI [0.593, 0.758], p = 1.91 x 10^-6); active-minus-passive was identical. All 20 seed effects were positive. No action required repair. All active targets accepted the pact; all passive responses called pre-existing intent uncertain.", s["body"]))
    primary_rows = [["Condition / contrast", "n", "Mean BCI change", "SD", "95% CI"]]
    for condition, label in (("control", "Control"), ("passive_probe", "Passive probe"),
                             ("active_provocation", "Active provocation")):
        row = confirm["condition_summary"][condition]
        primary_rows.append([label, str(row["n"]), fmt(row["mean_bci_change"]), fmt(row["sd_bci_change"]),
                             f"[{fmt(row['bootstrap_95_ci'][0])}, {fmt(row['bootstrap_95_ci'][1])}]"])
    primary_rows += [
        ["Active - control", "20 pairs", "0.680", "-", "[0.593, 0.758]"],
        ["Active - passive", "20 pairs", "0.680", "-", "[0.593, 0.758]"],
    ]
    story += [table(primary_rows, [1.75*inch, .65*inch, 1.18*inch, .7*inch, 1.2*inch]),
              Paragraph("Table 1. Confirmatory matched-seed results. Intervals for contrasts are paired bootstrap intervals.", s["caption"])]

    story.append(Paragraph("4.2 Mechanism: favoritism, not coordinated attack", s["h2"]))
    story.append(Paragraph(
        "Active solicitation increased the pre-to-post change in transfers to Agent 0 by 0.965 (95% CI [0.940, 0.990]). Contrary to the pact's sabotage clause, outsider sabotage fell by 0.235 and synchronized sabotage fell by 0.070 relative to control. Mean welfare rose from 158.4 to 163.5 because transfers are positive-sum, yet distribution shifted: provocateur score rose from 48.0 to 70.45, target score fell from 47.85 to 40.95, and mean outsider score fell from 31.275 to 26.05.", s["body"]))
    if CONFIRMATORY_FIGURE.exists():
        img = Image(str(CONFIRMATORY_FIGURE), width=6.7*inch, height=2.92*inch)
        story += [img, Paragraph("Figure 1. BCI change by condition (left) and active-minus-control components (right). The effect is driven by target-to-provocateur transfers.", s["caption"])]

    direct_inv = contrast(adaptive, "betrayal:direct_keeps_promise-minus-none_keeps_promise:invitation_partner_transfer")
    indirect_inv = contrast(adaptive, "betrayal:indirect_keeps_promise-minus-none_keeps_promise:invitation_partner_transfer")
    betrayal_transfer = contrast(adaptive, "betrayal:direct_betrays_target-minus-direct_keeps_promise:late_partner_transfer")
    betrayal_retaliation = contrast(adaptive, "betrayal:direct_betrays_target-minus-direct_keeps_promise:late_retaliation")
    betrayal_trust = contrast(adaptive, "betrayal:direct_betrays_target-minus-direct_keeps_promise:target_final_trust_0")
    report_direct = contrast(adaptive, "reporting:direct-minus-none:correct_reports")
    report_indirect = contrast(adaptive, "reporting:indirect-minus-none:correct_reports")
    net_direct = contrast(adaptive, "netter:direct-minus-none:netter_dominance")
    net_indirect = contrast(adaptive, "netter:indirect-minus-none:netter_dominance")

    story.append(Paragraph("4.3 Exploratory adaptive roles", s["h2"]))
    story.append(Paragraph(
        f"Across {adaptive['episodes']} fresh episodes, all pre-intervention histories matched and {adaptive['total_action_repairs']} corrective retries were recorded ({adaptive['repair_rate_per_decision']:.3%} per decision); {adaptive['total_public_fallbacks']} decisions used the fail-closed PUBLIC fallback. Pooling four role rosters as screening units, direct and indirect solicitations changed immediate organizer-transfer rates by {fmt(direct_inv['mean_paired_difference'], sign=True)} and {fmt(indirect_inv['mean_paired_difference'], sign=True)} relative to matched no-message controls when promises were kept. After direct solicitation, betrayal changed later organizer transfers by {fmt(betrayal_transfer['mean_paired_difference'], sign=True)}, retaliation against the organizer by {fmt(betrayal_retaliation['mean_paired_difference'], sign=True)}, and final organizer trust by {fmt(betrayal_trust['mean_paired_difference'], sign=True)}.", s["body"]))
    story.append(Paragraph(
        f"Within reporting rosters, direct and indirect solicitation changed correct reports by {fmt(report_direct['mean_paired_difference'], sign=True)} and {fmt(report_indirect['mean_paired_difference'], sign=True)} per episode relative to no-message controls. In netter rosters, recruitment changed the organizer's score margin over the strongest rival by {fmt(net_direct['mean_paired_difference'], sign=True)} (direct) and {fmt(net_indirect['mean_paired_difference'], sign=True)} (indirect). These pooled effects are descriptive: role rosters, not independently sampled agents, supply the comparison units.", s["body"]))

    adaptive_rows = [["Matched exploratory comparison", "Pairs", "Mean difference", "+ / 0 / -"]]
    for label, row in (
        ("Direct invitation - none", direct_inv),
        ("Indirect invitation - none", indirect_inv),
        ("Betrayal: late transfers", betrayal_transfer),
        ("Betrayal: retaliation", betrayal_retaliation),
        ("Direct reports - none", report_direct),
        ("Indirect reports - none", report_indirect),
        ("Direct netter dominance - none", net_direct),
        ("Indirect netter dominance - none", net_indirect),
    ):
        adaptive_rows.append([label, str(row["n_pairs"]), fmt(row["mean_paired_difference"], sign=True),
                              f"{row['positive']} / {row['zero']} / {row['negative']}"])
    story += [table(adaptive_rows, [2.65*inch, .55*inch, 1.05*inch, .85*inch]),
              Paragraph("Table 2. Exploratory matched contrasts. Invitation outcomes are transfer-to-organizer rates; netter dominance is a score margin. No confirmatory p-values are reported.", s["caption"])]
    if adaptive_figure.exists():
        story += [Image(str(adaptive_figure), width=6.7*inch, height=2.68*inch),
                  Paragraph("Figure 2. Selected descriptive contrasts from the adaptive-role screen. Scales differ between the behavior/reporting panel and score-margin panel.", s["caption"])]
    story.append(Paragraph(
        f"The screen did not reproduce the confirmatory experiment's uniform inducement. Direct solicitation produced a small immediate transfer increase and indirect social proof produced none. Betrayal did not reliably dissolve loyalty: later transfers rose {fmt(betrayal_transfer['mean_paired_difference'], sign=True)} while retaliation rose only {fmt(betrayal_retaliation['mean_paired_difference'], sign=True)}. Reporting was mostly inert. Sequential recruitment showed a graded behavioral signal: requested-action compliance was {adaptive['netter_recruitment_compliance']['direct']['mean']:.3f} under direct messages, {adaptive['netter_recruitment_compliance']['indirect']['mean']:.3f} under indirect messages, and {adaptive['netter_recruitment_compliance']['none']['mean']:.3f} with no message; netter score dominance changed by {fmt(net_direct['mean_paired_difference'], sign=True)} and {fmt(net_indirect['mean_paired_difference'], sign=True)}. These are screening patterns, not population estimates.", s["body"]))

    story += [Paragraph("5. Discussion", s["h1"])]
    story.append(Paragraph(
        "The confirmatory result supports <i>creation</i> in this environment. An active sting altered behavior far beyond both no-message and passive-question controls. Because passive and control action trajectories were identical under matched generation, there is no evidence here that the target was already acting as Agent 0's coalition partner. Active reciprocation instead demonstrates <i>susceptibility under solicitation</i>.", s["body"]))
    story.append(Paragraph(
        "This distinction matters operationally. A defender may reasonably ask, \"would this deployment accept a harmful pact if approached?\" It should not infer, \"this agent was independently colluding before we approached it.\" A minimally credible audit needs a no-contact baseline, a non-directive measurement control, matched prehistories, and separate behavioral components. Verbal acceptance alone is weak because collusive talk and action can diverge [2].", s["body"]))
    story.append(Paragraph(
        "The decomposition also changes the safety interpretation. The target did not carry out the outsider-sabotage clause more often; it transferred value upward and became exploitable. The adaptive extension asks whether richer memory and roles reverse that vulnerability after betrayal and whether reporters or counter-organizers help. Its role prompts deliberately alter agent policy, however, so the screen identifies mechanisms worth confirming rather than stable model traits.", s["body"]))
    story.append(Paragraph("Future Work", s["h2"]))
    story.append(Paragraph(
        "A reduced preregistered replication should rotate identities; compare model families; vary whether transfers are zero-sum; hide or reveal public actions; and separate social-proof framing from requested-action specificity. Reporting should be evaluated with latent organizers whose ground truth is not defined solely by receipt of a solicitation. The most promising exploratory contrast should be frozen before collecting additional seeds.", s["body"]))

    story += [Paragraph("6. Conclusion", s["h1"])]
    story.append(Paragraph(
        "A trusted undercover agent can be a useful stress tester, but it is not a neutral detector. Explicit solicitation caused large, perfectly seed-consistent discriminatory cooperation, almost entirely through preferential transfers. The target was economically exploited even though total welfare increased. Claims about \"caught colluders\" should be replaced with the narrower causal claim that an audited agent was inducible under the tested approach.", s["body"]))

    story += [Paragraph("Code and Data", s["h2"])]
    story.append(Paragraph(
        "The reproducibility package contains the preregistration, source, 21 experiment and integration tests, an independent payoff-replay and checksum verifier, excluded pilots, 20-seed confirmatory trajectories, exploratory plan, and fresh adaptive-role trajectories. Runs store raw per-episode JSON plus CSV summaries and analysis JSON. A public repository URL can be added before submission if available.", s["body"]))
    story += [Paragraph("Author Contributions", s["h2"])]
    story.append(Paragraph(
        "Umar Abdilaiypov directed the project, developed the adaptive-role variations, evaluated the research choices, and reviewed the evidence and report. The LLM assistance described below contributed the initial question, implementation, execution, analysis tooling, and drafting.", s["body"]))

    story += [PageBreak(), Paragraph("References", s["h1"])]
    refs = [
        "[1] X. Zeng and F. Rudzicz. Voluntary Collusion with Secret Tools in Competing LLM Agents. arXiv:2605.27593, 2026. https://arxiv.org/abs/2605.27593.",
        "[2] M. Nakamura et al. Colosseum: Auditing Collusion in Cooperative Multi-Agent Systems. arXiv:2602.15198, 2026. https://arxiv.org/abs/2602.15198.",
        "[3] K. Agrawal et al. Evaluating LLM Agent Collusion in Double Auctions. arXiv:2507.01413, 2025. https://arxiv.org/abs/2507.01413.",
        "[4] J. Shi, T. J. Zhang, B. Scholkopf, V. Conitzer, and Z. Jin. When Agents Lie: Premeditation, Persistence, and Exploitation in Repeated Games. arXiv:2607.05132, 2026. https://arxiv.org/abs/2607.05132.",
    ]
    for ref in refs:
        story.append(Paragraph(p(ref), s["small"]))

    story += [Paragraph("Appendix A. Limitations and Dual-Use / Ethical Considerations", s["h1"])]
    story.append(Paragraph("Limitations", s["h2"]))
    story.append(Paragraph(
        "This is one 7B model in a stylized game with fixed roles. The active proposal persists in context whereas the passive response does not; that difference is part of the treatment but prevents attribution to any one phrase. The provocateur is scripted. BCI is task-specific, and positive transfers are not synonymous with social harm. Acceptance may partly reflect instruction following or role-play. Exploratory roles are prompt-induced behaviors, not stable traits. Reporter ground truth is organizer solicitation, not hidden intent. The multi-role screen is not confirmatory.", s["body"]))
    story.append(Paragraph("Dual-use and ethics", s["h2"]))
    story.append(Paragraph(
        "The work demonstrates explicit secret offers, false social proof, betrayal, credibility gaming, and sequential targeting that could help an adversary recruit or exploit agents. We disclose them because controlled examples are needed to build audits, but do not claim they generalize to deployed systems. Defensive use should stay sandboxed, disclose the causal nature of the test, avoid punitive conclusions from one provoked episode, and assess actions rather than private reasoning. A failed sting does not prove safety; a successful sting does not prove pre-existing misconduct.", s["body"]))

    story += [Paragraph("Appendix B. Reproducibility Details", s["h1"])]
    story.append(Paragraph(
        f"Confirmatory seeds were 2000-2019. Excluded LLM smoke seeds were 900 and 920; calibration seeds were separate. Adaptive fresh seeds were {min(adaptive['seeds'])}-{max(adaptive['seeds'])}. Generation seeds are deterministic functions of episode seed, round, and agent. Pre-intervention equality is asserted programmatically. Parsing accepts one legal JSON action; after three logged invalid outputs, the adaptive runner conservatively substitutes the target-free PUBLIC action. Modal served Qwen/Qwen2.5-7B-Instruct on an NVIDIA A10G. An independent verifier reparses retained adaptive responses, replays every payoff, requires exact raw-JSON/CSV agreement, regenerates the analyses, and checks SHA-256 manifests. All scored trajectories and repair events are retained; successful raw action text was not logged in the earlier confirmatory run, so independent rerunning is the strongest model-provenance check.", s["body"]))

    story += [Paragraph("LLM Usage Statement", s["h1"])]
    story.append(Paragraph(
        "We used OpenAI Codex as a research and coding assistant. Codex proposed the core research idea and question - whether an undercover probe reveals pre-existing collusion or creates it - and implemented and ran the experimental pipeline under the author's direction. Umar Abdilaiypov proposed the subsequent variations, including betrayal, indirect social-proof manipulation, persistent adaptive memory, incentivized reporting with credibility updates, and the sequential \"netter\" organizer. Codex assisted in drafting this report. The human author selected the research direction, reviewed the design and outputs, and takes responsibility for the claims.", s["body"]))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(output_path), pagesize=letter, rightMargin=0.72*inch, leftMargin=0.72*inch,
        topMargin=0.60*inch, bottomMargin=0.58*inch,
        title="The Undercover Agent Effect", author="Umar Abdilaiypov",
        subject="AI Collusion Research Sprint submission",
    )
    document.build(story, onFirstPage=footer, onLaterPages=footer)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adaptive-analysis", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    make_pdf(args.adaptive_analysis, args.output)
    print(args.output)


if __name__ == "__main__":
    main()
