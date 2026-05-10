from pathlib import Path
import html
import re

ROOT = Path(__file__).resolve().parents[1]
CHAPTER = ROOT / "docs/chapters/complete/Chapter180_Antipsychotics.html"
BASE = ROOT / "scripts/rebuild_ch178.py"
STYLE = BASE.read_text(encoding="utf-8").split('STYLE = r"""', 1)[1].split('"""', 1)[0]
SCRIPT = BASE.read_text(encoding="utf-8").split('SCRIPT = r"""', 1)[1].split('"""', 1)[0]


def extract_figures(source: str) -> dict[int, dict[str, str]]:
    pat = re.compile(
        r'<figure class="source-figure[^"]*reference-image[^"]*"[^>]*>\s*'
        r'<img[^>]+src="(data:image/[^"]+)"[^>]*alt="([^"]*)"[^>]*>\s*'
        r"<figcaption[^>]*>(.*?)</figcaption>",
        re.S,
    )
    return {
        i: {
            "src": m.group(1),
            "alt": html.unescape(m.group(2)),
            "cap": html.unescape(re.sub("<.*?>", "", m.group(3))).strip(),
        }
        for i, m in enumerate(pat.finditer(source), 1)
    }


def source_card(figs: dict[int, dict[str, str]], idx: int, title: str, note: str) -> str:
    f = figs[idx]
    return f"""
    <article class="source-card">
      <div class="source-card__label">Tintinalli source</div>
      <h3 class="source-card__title">{html.escape(title)}</h3>
      <p>{html.escape(note)}</p>
      <figure class="reference-image">
        <img src="{f['src']}" alt="{html.escape(f['alt'])}" loading="lazy" decoding="async">
        <figcaption>{html.escape(f['cap'])}</figcaption>
      </figure>
    </article>
    """


def rosen_card(title: str, note: str, delta: str) -> str:
    return f"""
    <article class="source-card rosen-source">
      <div class="source-card__label">Rosen source check</div>
      <h3 class="source-card__title">{html.escape(title)}</h3>
      <p>{html.escape(note)}</p>
      <div class="source-delta"><strong><u>Rosen vs Tintinalli:</u></strong> {html.escape(delta)}</div>
    </article>
    """


def mcq(n: int, ans: str, stem: str, opts: list[tuple[str, str]], rats: dict[str, str]) -> str:
    buttons = "".join(
        f'<button class="mcq-opt" type="button" data-option-key="{k}">{k}. {html.escape(v)}</button>'
        for k, v in opts
    )
    explains = "".join(
        f'<div class="opt-explain {"is-correct" if k == ans else "is-wrong"}" hidden>'
        f"<strong>{k}. {html.escape(v)}</strong><span>{html.escape(rats[k])}</span></div>"
        for k, v in opts
    )
    return f'<article class="mcq-wrapper" data-answer="{ans}" data-answered="false"><p class="mcq-stem">Q{n}. {html.escape(stem)}</p><div class="mcq-options">{buttons}</div><div class="mcq-result" hidden></div><div class="mcq-explains">{explains}</div></article>'


def build_mcqs() -> str:
    raw = [
        ("A", "Most common cardiovascular pattern in many antipsychotic overdoses?", [("A", "Sinus tachycardia and orthostatic hypotension"), ("B", "Profound bradycardia in all patients"), ("C", "Cyanide-like shock"), ("D", "No ECG concerns ever")], {"A": "Anticholinergic and alpha-blocking effects commonly produce tachycardia and orthostasis.", "B": "Not typical.", "C": "Not the mechanism.", "D": "QT/QRS issues can occur."}),
        ("B", "Which ECG problem raises torsades risk?", [("A", "Short QT only"), ("B", "QT prolongation"), ("C", "Normal PR interval"), ("D", "Sinus rhythm alone")], {"A": "Not the torsades marker.", "B": "QT prolongation predisposes to torsades.", "C": "Not the issue.", "D": "Not enough."}),
        ("C", "Antipsychotic overdose with QRS widening should prompt consideration of:", [("A", "Naloxone"), ("B", "Fomepizole"), ("C", "Sodium bicarbonate"), ("D", "N-acetylcysteine")], {"A": "Opioid antidote.", "B": "Toxic alcohol antidote.", "C": "QRS widening from sodium-channel blockade physiology is treated with bicarbonate.", "D": "Acetaminophen antidote."}),
        ("D", "Acute dystonia after dopamine antagonist exposure is treated with:", [("A", "More haloperidol"), ("B", "Fomepizole"), ("C", "Hydroxocobalamin"), ("D", "Diphenhydramine or benztropine")], {"A": "Can worsen EPS.", "B": "No.", "C": "No.", "D": "Anticholinergic therapy rapidly treats acute dystonia."}),
        ("A", "Akathisia is often mistaken for:", [("A", "Worsening psychiatric agitation"), ("B", "Caustic injury"), ("C", "Cyanide poisoning"), ("D", "Renal colic")], {"A": "Inner restlessness can look like agitation.", "B": "No.", "C": "No.", "D": "No."}),
        ("B", "Classic NMS pattern?", [("A", "Clonus within minutes after MDMA"), ("B", "Fever, lead-pipe rigidity, altered mental status, autonomic instability"), ("C", "Pinpoint pupils and apnea"), ("D", "Bronchorrhea and salivation")], {"A": "Serotonin/sympathomimetic pattern.", "B": "Classic NMS.", "C": "Opioid.", "D": "Cholinergic."}),
        ("C", "NMS differs from serotonin syndrome because NMS is usually:", [("A", "Always painless"), ("B", "Defined by diarrhea only"), ("C", "Slower onset with rigidity/bradyreflexia"), ("D", "Caused by SSRI overdose only")], {"A": "No.", "B": "No.", "C": "Key distinction.", "D": "SSRIs cause serotonin syndrome."}),
        ("D", "Initial treatment of suspected NMS includes:", [("A", "Continue dopamine antagonist"), ("B", "Discharge"), ("C", "Acetaminophen only"), ("D", "Stop agent, supportive care, cooling, fluids, ICU-level monitoring when severe")], {"A": "Wrong.", "B": "Unsafe.", "C": "Insufficient.", "D": "Correct."}),
        ("A", "A patient with antipsychotic overdose and torsades should receive:", [("A", "Magnesium sulfate"), ("B", "Activated charcoal at 24 hours as sole therapy"), ("C", "Physostigmine reflexively"), ("D", "Beta blocker only")], {"A": "Magnesium treats torsades.", "B": "Not sole therapy.", "C": "Not reflexively safe.", "D": "Not first-line torsades treatment."}),
        ("B", "Which finding requires escalation rather than simple observation?", [("A", "Resolved mild drowsiness and normal ECG"), ("B", "Hyperthermia with rigidity"), ("C", "Normal vitals"), ("D", "Remote tiny exposure")], {"A": "Lower risk.", "B": "Severe toxidrome/NMS concern.", "C": "Lower risk if stable.", "D": "Lower risk."}),
        ("C", "Best first-line medication for toxin-related seizures/agitation?", [("A", "Phenytoin for all"), ("B", "More antipsychotic"), ("C", "Benzodiazepines"), ("D", "Flumazenil")], {"A": "Not first-line for most toxicologic seizures.", "B": "Can worsen.", "C": "Correct.", "D": "Can provoke seizures."}),
        ("D", "What should drive disposition after symptomatic overdose?", [("A", "Patient preference only"), ("B", "Urine drug screen only"), ("C", "One normal BP only"), ("D", "Mental status, vitals, temperature, ECG, coingestants, and symptom trend")], {"A": "No.", "B": "UDS is limited.", "C": "Insufficient.", "D": "Correct."}),
        ("A", "Which antipsychotic adverse syndrome can develop with therapeutic dosing as well as overdose?", [("A", "NMS"), ("B", "Cyanide poisoning"), ("C", "Toxic alcohol acidosis"), ("D", "Methemoglobinemia in all cases")], {"A": "NMS can occur after dopamine antagonist exposure even without huge overdose.", "B": "No.", "C": "No.", "D": "No."}),
        ("B", "Why avoid antipyretics as sole treatment for NMS?", [("A", "They always cause seizures"), ("B", "Heat is driven by muscle rigidity and autonomic dysfunction"), ("C", "They reverse dopamine blockade"), ("D", "They widen QRS")], {"A": "No.", "B": "Correct.", "C": "No.", "D": "No."}),
        ("C", "Refractory hypotension after antipsychotic overdose may need:", [("A", "Long-acting antihypertensive"), ("B", "Fluid restriction"), ("C", "IV fluids and vasopressors"), ("D", "No monitoring")], {"A": "Wrong direction.", "B": "Wrong.", "C": "Correct.", "D": "Unsafe."}),
        ("D", "Which feature fits anticholinergic effects from antipsychotics?", [("A", "Bronchorrhea"), ("B", "Miosis with apnea"), ("C", "Lacrimation and diarrhea only"), ("D", "Tachycardia, dry mucosa, urinary retention, delirium")], {"A": "Cholinergic.", "B": "Opioid.", "C": "Cholinergic.", "D": "Anticholinergic pattern."}),
        ("A", "Which EPS is an emergency because airway/laryngeal involvement can occur?", [("A", "Acute dystonia"), ("B", "Mild insomnia"), ("C", "Simple nausea"), ("D", "Remote headache")], {"A": "Dystonia can affect neck, jaw, tongue, and rarely airway.", "B": "No.", "C": "No.", "D": "No."}),
        ("B", "Dantrolene or bromocriptine in NMS should be viewed as:", [("A", "Replacement for supportive care"), ("B", "Adjuncts for severe cases after expert/ICU discussion"), ("C", "Mandatory for all mild EPS"), ("D", "Antidotes for opioid toxicity")], {"A": "Supportive care remains core.", "B": "Correct.", "C": "No.", "D": "No."}),
        ("C", "Which lab complication matters in NMS?", [("A", "Low carboxyhemoglobin only"), ("B", "No lab abnormalities ever"), ("C", "Elevated CK/rhabdomyolysis and renal injury risk"), ("D", "Mandatory methemoglobinemia")], {"A": "No.", "B": "False.", "C": "Correct.", "D": "No."}),
        ("D", "Which patient needs telemetry?", [("A", "All remote asymptomatic tiny ingestions forever"), ("B", "Only if UDS positive"), ("C", "Never"), ("D", "QT prolongation, QRS widening, syncope, dysrhythmia, severe overdose, or significant symptoms")], {"A": "Too broad.", "B": "No.", "C": "False.", "D": "Correct."}),
        ("A", "Treatment table for NMS belongs:", [("A", "In the NMS section next to NMS narrative"), ("B", "Only in Drug Dose Reference"), ("C", "Only in MCQs"), ("D", "Hidden from chapter")], {"A": "Topic-local placement is the rule.", "B": "Wrong.", "C": "Wrong.", "D": "Wrong."}),
        ("B", "Most antipsychotic overdose care is:", [("A", "Chelation"), ("B", "Supportive with targeted ECG/EPS/NMS interventions"), ("C", "Hemodialysis for all"), ("D", "NAC for all")], {"A": "No.", "B": "Correct.", "C": "No.", "D": "No."}),
        ("C", "Which exposure history changes risk?", [("A", "Only favorite color"), ("B", "No medication list needed"), ("C", "Agent, dose, time, formulation, coingestants, and recent dose changes"), ("D", "Shoe size")], {"A": "No.", "B": "Wrong.", "C": "Correct.", "D": "No."}),
        ("D", "Which is a safe summary of NMS vs serotonin syndrome?", [("A", "They are identical"), ("B", "Serotonin syndrome has lead-pipe rigidity and bradyreflexia only"), ("C", "NMS is always instant"), ("D", "Serotonin syndrome is faster with clonus/hyperreflexia; NMS is slower with rigidity/bradyreflexia")], {"A": "No.", "B": "Reversed.", "C": "No.", "D": "Correct."}),
        ("A", "Severe hyperthermia in NMS may require:", [("A", "ICU care, cooling, sedation, airway control, and renal/rhabdo monitoring"), ("B", "Home observation"), ("C", "Only oral acetaminophen"), ("D", "No fluids")], {"A": "Correct.", "B": "Unsafe.", "C": "Insufficient.", "D": "Wrong."}),
        ("C", "Best one-sentence ED approach?", [("A", "Ignore ECG and temperature"), ("B", "Treat all with flumazenil"), ("C", "Support ABCs, monitor ECG/temperature, treat EPS and dysrhythmias, recognize NMS, and disposition by clinical course"), ("D", "Discharge all awake patients")], {"A": "Wrong.", "B": "Dangerous.", "C": "Correct.", "D": "Unsafe."}),
    ]
    return "\n".join(mcq(i, *item) for i, item in enumerate(raw, 1))


def main() -> None:
    old = CHAPTER.read_text(encoding="utf-8")
    backup = CHAPTER.with_suffix(CHAPTER.suffix + ".bak_rebuild_20260508")
    if not backup.exists():
        backup.write_bytes(CHAPTER.read_bytes())
    figs = extract_figures(old)
    for idx in (1, 9, 11):
        if idx not in figs:
            raise RuntimeError(f"Missing figure {idx}")
    doc = f"""<!doctype html><html lang="en" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Chapter 180 - Antipsychotics</title><style>{STYLE}</style></head><body>
<header id="top-header"><button class="hdr-btn" data-sidebar-toggle title="Contents">☰</button><div class="hdr-title">Ch.180 Antipsychotics</div><button class="hdr-btn theme-btn" data-theme-toggle>Dark</button></header>
<div class="app"><aside id="sidebar" class="sidebar"><button class="hdr-btn sidebar-close" data-sidebar-close>Close</button><div class="sidebar__block"><div class="sidebar__kicker">Chapter</div><h2>Antipsychotics</h2><p class="meta"><b>Spine:</b> Tintinalli Ch.180</p><p class="meta"><b>Pattern:</b> Ch186/Ch201 rebuild</p></div><div class="sidebar__block"><div class="sidebar__kicker">Contents</div><a class="sidebar__link" href="#overview">Overview</a><a class="sidebar__link" href="#overdose">Overdose</a><a class="sidebar__link" href="#ecg">ECG / Shock</a><a class="sidebar__link" href="#eps">EPS</a><a class="sidebar__link" href="#nms">NMS</a><a class="sidebar__link" href="#drug-doses">Drug Dose Reference</a><a class="sidebar__link" href="#disposition">Disposition</a><a class="sidebar__link" href="#assessment">Assessment</a></div></aside>
<main id="main" class="main"><div class="content-wrap"><div class="utility-bar">Rebuilt chapter • table crops topic-local • MCQs show all explanations after answer • final crop QA</div>
<section class="hero section" id="overview"><div class="eyebrow">Toxicology Chapter 180</div><h1 class="hero__title">Antipsychotics</h1><p class="lede">Antipsychotic poisoning is usually supportive-care heavy, but the ED must actively look for <mark>CNS depression, hypotension, QT/QRS abnormalities, EPS, and neuroleptic malignant syndrome</mark>.</p><div class="callout warn"><strong>Board frame:</strong> do not confuse medication-induced akathisia, dystonia, or NMS with simple psychiatric agitation.</div>{source_card(figs, 1, "Tintinalli Table 180-1. Common antipsychotics", "Agent table placed up front to anchor typical/atypical exposure recognition and adverse-effect risk.")}{rosen_card("Rosen source check: antipsychotic toxicity sorting", "Rosen emphasizes the same bedside sort: airway/CNS depression, anticholinergic effects, hypotension, ECG toxicity, EPS, and NMS.", "Tintinalli provides the agent table and NMS criteria; Rosen reinforces early syndrome recognition and supportive stabilization.")}</section>
<section class="section" id="overdose"><h2>Clinical Features of Overdose</h2><p>Overdose ranges from mild sedation to coma, aspiration risk, anticholinergic delirium, sinus tachycardia, orthostatic hypotension, seizures, and dysrhythmias. A medication list matters because high-potency agents are more EPS-prone, while several agents can prolong QT or contribute to hypotension.</p><p>ED assessment should include glucose, temperature, serial vitals, ECG, coingestant screen when indicated, and repeated mental-status exams. <u>Airway risk</u> and hemodynamics come before trying to label the exact psychiatric drug.</p></section>
<section class="section" id="ecg"><h2>ECG and Shock Treatment</h2><p>ECG treatment is interval-driven. <mark>QT prolongation</mark> increases torsades risk and should trigger electrolyte correction, avoidance of more QT-prolonging drugs, telemetry, and magnesium for torsades. QRS widening suggests sodium-channel blockade physiology and should prompt sodium bicarbonate boluses with reassessment.</p><p>Hypotension usually responds to fluids, but refractory shock needs vasopressors and ICU-level monitoring. Seizures or severe agitation should be treated with <u>benzodiazepines</u>, not flumazenil.</p></section>
<section class="section" id="eps"><h2>Extrapyramidal Symptoms</h2><p>EPS can occur after therapeutic dosing or overdose. Acute dystonia causes painful neck, jaw, tongue, back, or eye deviation and can rarely threaten the airway. Treat with diphenhydramine or benztropine and continue short oral therapy because symptoms can recur after the IV medication wears off.</p><p>Akathisia is subjective inner restlessness and is often mislabeled as worsening agitation. Parkinsonism and tardive dyskinesia are usually less acute ED overdose problems, but recognition prevents unnecessary antipsychotic escalation.</p></section>
<section class="section" id="nms"><h2>Neuroleptic Malignant Syndrome</h2><p>NMS is a delayed dopamine-antagonist emergency with <mark>fever, lead-pipe rigidity, altered mental status, autonomic instability, and elevated CK</mark>. It usually evolves over hours to days, unlike serotonin syndrome, which is faster and features clonus/hyperreflexia.</p><p>Treatment is immediate discontinuation of the offending agent, airway and ICU-level supportive care when severe, aggressive fluids, active cooling, benzodiazepines for agitation, and renal/rhabdomyolysis monitoring. Dantrolene or bromocriptine can be considered in severe cases with toxicology/critical-care involvement, but they do not replace supportive care.</p>{source_card(figs, 9, "Tintinalli Table 180-2. Diagnostic criteria for neuroleptic malignant syndrome", "Diagnostic criteria table placed inside the NMS section where it is used.")}{source_card(figs, 11, "Tintinalli Table 180-3. Treatment of neuroleptic malignant syndrome", "Treatment table placed next to the NMS treatment narrative, not in Drug Dose Reference.")}{rosen_card("Rosen source check: NMS vs serotonin syndrome", "Rosen also separates NMS from serotonin syndrome by time course and neuromuscular exam.", "Tintinalli gives criteria and treatment table; Rosen reinforces the bedside distinction: rigidity/bradyreflexia for NMS versus clonus/hyperreflexia for serotonin syndrome.")}</section>
<section class="section" id="drug-doses"><h2>Drug Dose Reference</h2><p>This section is only a quick recap after the clinical sections. Treatment logic and source tables belong above.</p><div class="table-wrap"><table><thead><tr><th>Problem</th><th>ED treatment anchor</th><th>Board caution</th></tr></thead><tbody><tr><td>Acute dystonia</td><td>Diphenhydramine or benztropine; short oral continuation</td><td>Can recur after initial improvement.</td></tr><tr><td>Torsades/QT</td><td>Magnesium sulfate, electrolyte correction, telemetry</td><td>Do not add QT-prolonging drugs casually.</td></tr><tr><td>QRS widening</td><td>Sodium bicarbonate and reassess ECG/hemodynamics</td><td>Treat the interval, not only the drug name.</td></tr><tr><td>NMS</td><td>Stop agent, fluids, cooling, benzodiazepines, ICU care; consider dantrolene/bromocriptine in severe cases</td><td>Antipyretics alone are inadequate.</td></tr></tbody></table></div></section>
<section class="section" id="disposition"><h2>Disposition</h2><p>Admit patients with coma, aspiration risk, persistent symptoms, hypotension, seizure, abnormal ECG, hyperthermia, rigidity, or suspected NMS. Mild exposures can be observed until mental status, vitals, ambulation, and ECG are reassuring.</p></section>
<section class="question-set section" id="assessment"><h2>Inline Assessment MCQs</h2>{build_mcqs()}</section>
</div></main></div><div class="score-pill" data-score-text>0 correct / 0 answered / 26 total</div><div class="image-modal" data-image-modal><button class="hdr-btn" data-modal-close>Close</button><img alt="Zoomed source"></div><script>{SCRIPT}</script></body></html>"""
    CHAPTER.write_text(doc, encoding="utf-8")
    print("rebuilt", CHAPTER)
    for token in ["source-card__label", "reference-image", "mcq-wrapper", "data-answer=", "<mark", "<u>", "Rosen source check", "Rosen vs Tintinalli", "reveal-all"]:
        print(token, doc.count(token))


if __name__ == "__main__":
    main()
