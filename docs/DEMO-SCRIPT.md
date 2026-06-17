# 60–90s demo video script (README hero / LinkedIn)

A tight screen-recording script for the local web app. Goal: in under 90s, show
that this is a **deterministic, cited EU AI Act engine with an AI-security lens** —
not a chatbot. Record at 1280×800, hide bookmarks, use the live demo or a local
run with `DEMO_MODE` off (so the inventory roll-up shows).

Tools: any screen recorder (Loom / OBS / ScreenStudio). Keep the cursor calm;
pause ~1s on each report so a viewer can read the headline row.

---

## Shot list

| # | Time | On screen | Voiceover / caption |
|---|------|-----------|---------------------|
| 1 | 0–8s | Landing page. Linger on the **amber countdown** ("… days until High-risk & Art. 50 obligations apply, 2 Aug 2026"). | "The EU AI Act's high-risk rules apply on 2 August 2026. AI Act Companion helps you get ready — locally, with no black box." |
| 2 | 8–16s | Open the **Load example** dropdown; pick **GridSentinel autonomous operations agent**. Click **Classify & generate**. | "Describe a system — or load an example. Everything's a deterministic rule, not an LLM guess." |
| 3 | 16–28s | Result view: the **High-risk** tier badge, the cited findings, the **Applies from 2 Aug 2026** line. Scroll to the **AI security lens** with the **Critical** severity badge. | "It cites the exact Article and Annex for every verdict — and rates AI-security risk by the architecture, not a checkbox. Here: Critical, because the model is the only access-control boundary." |
| 4 | 28–40s | Click the **Red-team plan** tab → scroll to a Critical test. Then the **Control catalogue** tab → the matching control. | "From the same profile it generates an authorized red-team test plan — and the matching defensive control that each test verifies. Offense and defense, linked." |
| 5 | 40–52s | Click **STRIDE threat model** → the six categories with severities. Then **Serious incident** → the Art. 73 deadline table. | "A STRIDE threat model that reuses the same severity, and an Art. 73 serious-incident helper with the reporting deadlines." |
| 6 | 52–64s | Click **Technical documentation** (Annex IV) and **Compliance tracker** → the Art. 99 penalty block. | "And the paperwork: Annex IV technical documentation, a conformity tracker, even the Art. 99 penalty exposure." |
| 7 | 64–75s | Open the **AI system inventory** → the portfolio roll-up (tier distribution, obligations due). | "Across a portfolio, it rolls up risk tiers and the obligations coming due by date." |
| 8 | 75–85s | Cut to the GitHub repo + the 🤗 live-demo badge. | "Local-first, open-source, fully tested. Try the live demo — link in the README." |

---

## One-liner (for the post)

> A free, open-source **EU AI Act** risk classifier with an **AI-security lens**:
> it cites the Article behind every verdict, rates risk by your architecture
> (not a checkbox), and generates the red-team plan, controls, STRIDE model,
> Annex IV docs and conformity tracker — deterministically, on your own machine.

## Notes

- If recording the **public demo**, the AI-assist panel is hidden (that's
  intentional — the demo shows the deterministic engine). Mention that the
  optional local AI only drafts inputs a human reviews.
- Best example for a single-clip story: **GridSentinel** (high-risk *and* Critical
  security). For a GPAI angle, use **OpenScribe-7B**.
