from pathlib import Path
import html
import re

ROOT = Path(__file__).resolve().parents[1]
CHAPTER = ROOT / "docs/chapters/complete/Chapter179_MonoamineOxidaseInhibitors.html"


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
        ("B", "What mechanism explains tyramine reactions in patients taking nonselective MAOIs?", [("A", "Direct cyanide release"), ("B", "Reduced monoamine breakdown with excess catecholamine effect"), ("C", "Opioid receptor blockade"), ("D", "Methemoglobin formation")], {"A": "No cyanide mechanism.", "B": "MAO inhibition prevents monoamine breakdown; tyramine can trigger catecholamine excess and hypertensive crisis.", "C": "Unrelated.", "D": "Unrelated."}),
        ("A", "A patient on phenelzine eats aged cheese and develops severe hypertension and headache. First ED priority?", [("A", "Assess end-organ symptoms, monitor closely, sedate if agitated, and use short-acting titratable antihypertensive if needed"), ("B", "Give long-acting beta blocker and discharge"), ("C", "Induce emesis"), ("D", "Give naloxone")], {"A": "Hypertensive crisis needs monitored, titratable management.", "B": "Long-acting agents are risky and discharge is unsafe.", "C": "Not appropriate.", "D": "Not opioid toxicity."}),
        ("C", "Which finding supports serotonin syndrome from an MAOI interaction?", [("A", "Lead-pipe rigidity over days"), ("B", "Pinpoint pupils and apnea"), ("C", "Clonus and hyperreflexia"), ("D", "Isolated bradycardia")], {"A": "More NMS-like.", "B": "Opioid toxidrome.", "C": "Clonus and hyperreflexia are key.", "D": "Not typical."}),
        ("D", "Which medication combination is especially dangerous with MAOIs?", [("A", "Acetaminophen"), ("B", "Inhaled albuterol alone"), ("C", "Oral rehydration solution"), ("D", "Meperidine, dextromethorphan, linezolid, or serotonergic antidepressants")], {"A": "Not the classic interaction.", "B": "Not the key interaction.", "C": "No.", "D": "These can precipitate serotonin toxicity or severe adrenergic effects."}),
        ("A", "Why can MAOI overdose be delayed?", [("A", "Pharmacodynamic effect and absorption/distribution can delay severe features"), ("B", "It must be metabolized to carbon monoxide"), ("C", "It binds charcoal for 48 hours"), ("D", "It causes only immediate symptoms")], {"A": "Severe toxicity can appear after a latent period.", "B": "No.", "C": "Charcoal binding does not explain delay.", "D": "False."}),
        ("B", "Best first-line treatment for agitation/seizures in MAOI toxicity?", [("A", "Phenytoin first"), ("B", "Benzodiazepines"), ("C", "Flumazenil"), ("D", "Haloperidol escalation")], {"A": "Not first-line for toxicologic seizures.", "B": "Benzodiazepines reduce agitation, catecholamine output, and seizures.", "C": "Can provoke seizures.", "D": "Can worsen hyperthermic/toxicologic agitation."}),
        ("D", "Severe MAOI hyperthermia is best managed by:", [("A", "Acetaminophen only"), ("B", "Observation only"), ("C", "Long-acting oral antihypertensive"), ("D", "Aggressive sedation, active cooling, and paralysis/intubation if needed")], {"A": "Antipyretics do not stop muscle heat generation.", "B": "Unsafe.", "C": "Does not treat hyperthermia.", "D": "Correct for life-threatening hyperthermia."}),
        ("C", "Which antihypertensive principle is preferred in MAOI hypertensive crisis?", [("A", "Slow oral therapy only"), ("B", "Never treat blood pressure"), ("C", "Short-acting, titratable agents with close monitoring"), ("D", "Long-acting depot medication")], {"A": "Too slow/uncontrolled.", "B": "Severe crisis needs treatment.", "C": "Titration prevents overshoot.", "D": "Risky."}),
        ("A", "Which diagnosis is in the differential for MAOI toxicity because it also causes hyperthermia/agitation?", [("A", "Sympathomimetic or serotonin toxicity"), ("B", "Simple ankle sprain"), ("C", "Appendicitis only"), ("D", "Isolated urticaria")], {"A": "These overlap clinically.", "B": "No.", "C": "No.", "D": "No."}),
        ("B", "Disposition for symptomatic intentional MAOI overdose should usually be:", [("A", "Immediate discharge"), ("B", "Monitored admission/ICU depending severity and delayed-risk window"), ("C", "No ECG monitoring"), ("D", "Only outpatient follow-up")], {"A": "Unsafe.", "B": "Delayed severe toxicity warrants monitoring.", "C": "ECG and vitals matter.", "D": "Too low acuity."}),
        ("D", "What makes linezolid relevant to this chapter?", [("A", "It is an opioid"), ("B", "It is a toxic alcohol antidote"), ("C", "It causes cyanide poisoning"), ("D", "It has MAOI activity and can interact with serotonergic drugs")], {"A": "No.", "B": "No.", "C": "No.", "D": "Correct."}),
        ("A", "Which exam clue should be actively checked in suspected serotonin syndrome?", [("A", "Inducible/spontaneous clonus"), ("B", "Asterixis only"), ("C", "Papilledema only"), ("D", "Absent bowel sounds only")], {"A": "Clonus is a high-yield diagnostic clue.", "B": "Not key.", "C": "Not key.", "D": "Can occur in anticholinergic toxicity but not the handle here."}),
        ("C", "Why should treatment tables not be placed only in Drug Dose Reference?", [("A", "Because doses are never useful"), ("B", "Because MCQs replace treatment"), ("C", "Treatment logic must live in the relevant clinical section first"), ("D", "Because source tables are forbidden")], {"A": "Doses are useful.", "B": "MCQs do not replace content.", "C": "Correct gate.", "D": "Source tables are allowed topic-locally."}),
        ("B", "Which patient needs poison-center/toxicology involvement?", [("A", "Remote asymptomatic low-risk exposure only"), ("B", "Severe MAOI overdose with hyperthermia, seizures, or hemodynamic instability"), ("C", "Simple laceration"), ("D", "Mild seasonal allergy")], {"A": "May still call, but less urgent.", "B": "High-risk toxicity needs expert support.", "C": "No.", "D": "No."}),
        ("A", "The safe-medication table in an MAOI chapter is most useful for:", [("A", "Avoiding dangerous interaction assumptions and recognizing lower-risk choices"), ("B", "Replacing all clinical judgment"), ("C", "Treating seizures"), ("D", "Diagnosing appendicitis")], {"A": "Correct.", "B": "No table replaces context.", "C": "Not a seizure table.", "D": "No."}),
        ("D", "Which food history matters in MAOI users?", [("A", "Plain water"), ("B", "Rice only"), ("C", "Ice chips"), ("D", "Aged/fermented tyramine-rich foods")], {"A": "No.", "B": "No.", "C": "No.", "D": "Tyramine-rich foods can precipitate crisis."}),
        ("C", "Which vital sign pattern is concerning in MAOI toxicity?", [("A", "Completely normal repeated vitals after observation"), ("B", "Mild isolated rhinorrhea"), ("C", "Severe hypertension, tachycardia, hyperthermia, or hypotension after severe toxicity"), ("D", "Normal temperature only")], {"A": "Less concerning.", "B": "No.", "C": "Correct.", "D": "One normal value is insufficient."}),
        ("A", "Cyproheptadine may be considered when MAOI toxicity overlaps with:", [("A", "Serotonin syndrome"), ("B", "Pure opioid overdose"), ("C", "Cyanide poisoning"), ("D", "Caustic ingestion")], {"A": "It is a serotonin antagonist adjunct.", "B": "Naloxone territory.", "C": "Hydroxocobalamin territory.", "D": "No."}),
        ("B", "Which statement about MAOI selectivity is most board-relevant?", [("A", "All MAOIs have no interactions"), ("B", "MAO-A/MAO-B selectivity and reversibility influence interaction risk, but overdose still requires clinical monitoring"), ("C", "MAOIs are all opioid antagonists"), ("D", "Selectivity removes all risk")], {"A": "False.", "B": "Correct.", "C": "No.", "D": "False."}),
        ("D", "What is the role of activated charcoal?", [("A", "Mandatory at 24 hours"), ("B", "Never considered"), ("C", "An antidote"), ("D", "Consider early after significant ingestion if airway is protected")], {"A": "Too late/universal.", "B": "May be considered early.", "C": "Not an antidote.", "D": "Correct."}),
        ("A", "Which feature suggests sympathomimetic crisis rather than simple anxiety?", [("A", "Marked hypertension, diaphoresis, hyperthermia, and neuromuscular findings"), ("B", "Normal exam"), ("C", "Isolated worry"), ("D", "Chronic mild insomnia only")], {"A": "Objective autonomic and neuromuscular findings are concerning.", "B": "Less supportive.", "C": "Not enough.", "D": "Not acute toxicity."}),
        ("C", "Which drug should generally be avoided as a reflex answer for MAOI hypertensive crisis?", [("A", "Carefully titrated short-acting vasodilator"), ("B", "Benzodiazepine for agitation"), ("C", "Long-acting non-titratable antihypertensive"), ("D", "Cooling for hyperthermia")], {"A": "Reasonable when indicated.", "B": "Reasonable.", "C": "Overshoot risk.", "D": "Needed when hot."}),
        ("B", "Why repeat assessment matters in MAOI overdose?", [("A", "Findings never change"), ("B", "Severe effects may be delayed and can evolve from agitation to seizures/shock/hyperthermia"), ("C", "It is only for billing"), ("D", "ECG is forbidden")], {"A": "False.", "B": "Correct.", "C": "No.", "D": "ECG monitoring is useful."}),
        ("D", "Which lab/monitoring package is reasonable in serious MAOI toxicity?", [("A", "No labs ever"), ("B", "Only urine color"), ("C", "Only pregnancy test for everyone"), ("D", "ECG, electrolytes, renal function, CK/temperature monitoring when hyperthermic or rigid, and coingestant screening as indicated")], {"A": "Unsafe.", "B": "No.", "C": "Pregnancy testing may matter but not only.", "D": "Correct."}),
        ("A", "What is the main board trap in MAOI chapters?", [("A", "Dangerous interactions and delayed severe toxicity despite initially nonspecific symptoms"), ("B", "All MAOI exposures are harmless"), ("C", "Charcoal is the antidote"), ("D", "No medication history is needed")], {"A": "Correct.", "B": "False.", "C": "False.", "D": "Medication/food history is central."}),
        ("C", "Best one-sentence ED summary?", [("A", "Ignore the medication list"), ("B", "Treat every patient with discharge"), ("C", "Identify interaction/overdose pattern, monitor for delayed autonomic-neurologic toxicity, control agitation/seizures/hyperthermia, and use titratable hemodynamic therapy"), ("D", "Use flumazenil for all")], {"A": "Wrong.", "B": "Wrong.", "C": "Correct.", "D": "Dangerous."}),
    ]
    return "\n".join(mcq(i, *item) for i, item in enumerate(raw, 1))


STYLE = Path(ROOT / "scripts/rebuild_ch178.py").read_text(encoding="utf-8").split('STYLE = r"""', 1)[1].split('"""', 1)[0]
SCRIPT = Path(ROOT / "scripts/rebuild_ch178.py").read_text(encoding="utf-8").split('SCRIPT = r"""', 1)[1].split('"""', 1)[0]


def main() -> None:
    old = CHAPTER.read_text(encoding="utf-8")
    backup = CHAPTER.with_suffix(CHAPTER.suffix + ".bak_rebuild_20260508")
    if not backup.exists():
        backup.write_bytes(CHAPTER.read_bytes())
    figs = extract_figures(old)
    for idx in (1, 4, 8):
        if idx not in figs:
            raise RuntimeError(f"Missing figure {idx}")
    doc = f"""<!doctype html><html lang="en" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Chapter 179 - Monoamine Oxidase Inhibitors</title><style>{STYLE}</style></head><body>
<header id="top-header"><button class="hdr-btn" data-sidebar-toggle title="Contents">☰</button><div class="hdr-title">Ch.179 Monoamine Oxidase Inhibitors</div><button class="hdr-btn theme-btn" data-theme-toggle>Dark</button></header>
<div class="app"><aside id="sidebar" class="sidebar"><button class="hdr-btn sidebar-close" data-sidebar-close>Close</button><div class="sidebar__block"><div class="sidebar__kicker">Chapter</div><h2>Monoamine Oxidase Inhibitors</h2><p class="meta"><b>Spine:</b> Tintinalli Ch.179</p><p class="meta"><b>Pattern:</b> Ch186/Ch201 rebuild</p></div><div class="sidebar__block"><div class="sidebar__kicker">Contents</div><a class="sidebar__link" href="#overview">Overview</a><a class="sidebar__link" href="#mechanism">Mechanism</a><a class="sidebar__link" href="#interactions">Interactions</a><a class="sidebar__link" href="#features">Clinical Features</a><a class="sidebar__link" href="#diagnosis">Diagnosis</a><a class="sidebar__link" href="#treatment">Treatment</a><a class="sidebar__link" href="#drug-doses">Drug Dose Reference</a><a class="sidebar__link" href="#disposition">Disposition</a><a class="sidebar__link" href="#assessment">Assessment</a></div></aside>
<main id="main" class="main"><div class="content-wrap"><div class="utility-bar">Rebuilt chapter • table crops only • reveal-all MCQs • final crop QA</div>
<section class="hero section" id="overview"><div class="eyebrow">Toxicology Chapter 179</div><h1 class="hero__title">Monoamine Oxidase Inhibitors</h1><p class="lede">MAOI toxicity is an interaction-heavy chapter: the ED danger is <mark>delayed autonomic and neurologic deterioration</mark>, tyramine/catecholamine hypertensive crisis, and serotonin syndrome from interacting drugs.</p><div class="callout warn"><strong>Board frame:</strong> every MAOI patient needs a medication, OTC/cough product, antibiotic, serotonergic, sympathomimetic, and food history. The first exam can be deceptively mild.</div>{source_card(figs, 1, "Tintinalli Table 179-1. FDA-approved monoamine oxidase inhibitors", "Agent table placed up front to anchor exposure recognition and selectivity/reversibility context.")}{rosen_card("Rosen source check: MAOI interaction framing", "Rosen emphasizes MAOI poisonings as interaction-driven autonomic and serotonergic emergencies rather than simple sedative ingestions.", "Tintinalli provides the agent and treatment structure; Rosen reinforces medication-reconciliation and toxidrome sorting at the bedside.")}</section>
<section class="section" id="mechanism"><h2>Mechanism and Pharmacokinetics</h2><p>Monoamine oxidase normally metabolizes norepinephrine, serotonin, dopamine, and tyramine. When MAO activity is inhibited, patients can develop excess catecholamine or serotonin activity. <u>MAO-A</u> is more tied to serotonin/norepinephrine metabolism, while MAO-B is more tied to dopamine metabolism, but selectivity can be lost in overdose or with interacting drugs.</p><p>The practical ED implication is delay. Severe toxicity can appear after a latent period, especially with intentional overdose, sustained absorption, or acute-on-chronic exposure. Do not clear a patient only because the first set of vitals looks acceptable.</p></section>
<section class="section" id="interactions"><h2>Drug and Food Interactions</h2><p>The classic food interaction is a tyramine-rich meal such as aged cheese, cured meats, fermented products, or some concentrated yeast/soy products. Tyramine can release norepinephrine and trigger <mark>hypertensive crisis</mark> with headache, diaphoresis, chest pain, neurologic symptoms, or aortic/coronary risk.</p><p>Drug interactions are just as important: SSRIs/SNRIs, TCAs, meperidine, tramadol, dextromethorphan, linezolid, sympathomimetics, cocaine/amphetamines, and some OTC cold products can produce serotonin syndrome or adrenergic crisis. The safe-medication table is helpful, but it does not replace bedside context.</p>{source_card(figs, 4, "Tintinalli Table 179-2. Medications considered safe in combination with MAOIs", "Placed in the interaction section because this table is about medication selection and avoiding dangerous combinations.")}{rosen_card("Rosen source check: interaction history", "Rosen similarly prioritizes recent medication changes, OTC products, serotonergic combinations, and sympathomimetic exposure.", "Tintinalli gives examples and ED treatment; Rosen emphasizes that the diagnosis often comes from the medication history before any lab confirms it.")}</section>
<section class="section" id="features"><h2>Clinical Features</h2><p>MAOI toxicity can begin with nonspecific nausea, anxiety, tremor, tachycardia, or hypertension, then progress to agitation, delirium, seizures, hyperthermia, rigidity, hypotension, dysrhythmias, coma, or shock. Severe cases may move between sympathetic excess and circulatory collapse.</p><p>Serotonin syndrome overlap is recognized by <mark>clonus, hyperreflexia, tremor, agitation, diaphoresis, and hyperthermia</mark>. Hypertensive crisis is more catecholamine-driven and may present with severe headache, chest pain, neurologic deficits, or end-organ injury.</p></section>
<section class="section" id="diagnosis"><h2>Diagnosis and Differential</h2><p>Diagnosis is clinical. Order ECG, electrolytes, renal function, glucose, temperature monitoring, CK when rigid/hyperthermic, and coingestant testing as indicated, but do not wait for a confirmatory MAOI level. The differential includes sympathomimetic toxicity, serotonin syndrome, NMS, anticholinergic toxicity, withdrawal states, sepsis, CNS infection, thyroid storm, and heat illness.</p>{source_card(figs, 8, "Tintinalli Table 179-3. Differential diagnosis of MAOI overdose", "Differential table placed with diagnosis because it is used to separate MAOI toxicity from look-alike hyperadrenergic and hyperthermic syndromes.")}</section>
<section class="section" id="treatment"><h2>Treatment</h2><p>Treatment begins with ABCs, IV access, cardiac monitoring, temperature measurement, glucose/electrolyte correction, and poison-center consultation for significant exposure. Early activated charcoal can be considered for a serious recent ingestion if the airway is protected, but supportive care is the core.</p><p><u>Benzodiazepines</u> are first-line for agitation and seizures and also reduce adrenergic output. Hyperthermia requires active cooling; severe muscle activity may require intubation, paralysis, and ICU care. Hypertensive crisis should be treated with short-acting, titratable agents and careful monitoring; avoid long-acting non-titratable therapy that can overshoot. Hypotension after severe toxicity requires fluids and vasopressors guided by hemodynamics.</p><div class="callout danger"><strong>Trap:</strong> antipyretics alone do not fix hyperthermia from serotonin syndrome or severe muscle activity.</div></section>
<section class="section" id="drug-doses"><h2>Drug Dose Reference</h2><p>This is a recap after the treatment narrative, not the only place where treatment appears.</p><div class="table-wrap"><table><thead><tr><th>Problem</th><th>ED treatment anchor</th><th>Board caution</th></tr></thead><tbody><tr><td>Agitation/seizure</td><td>Benzodiazepines; escalate airway/ICU support if recurrent</td><td>Avoid flumazenil and reflex antipsychotic escalation.</td></tr><tr><td>Hypertensive crisis</td><td>Short-acting titratable antihypertensive/vasodilator with close monitoring</td><td>Avoid long-acting agents that overshoot.</td></tr><tr><td>Serotonin syndrome</td><td>Stop agents, benzodiazepines, cooling; consider enteral cyproheptadine for moderate/severe cases</td><td>Severe hyperthermia needs sedation/paralysis/intubation.</td></tr><tr><td>Hypotension/shock</td><td>IV fluids, vasopressors, ECG-guided care</td><td>May follow severe toxicity or treatment overshoot.</td></tr></tbody></table></div></section>
<section class="section" id="disposition"><h2>Disposition and Follow-up</h2><p>Intentional MAOI overdose, symptoms, abnormal ECG, hyperthermia, seizures, severe hypertension, hypotension, or concerning interactions need monitored admission and often ICU-level care. Asymptomatic accidental exposures may still need observation because severe toxicity can be delayed.</p><p>Discharge requires a reliable exposure history, stable repeated vitals, normal mental status, no evolving neuromuscular findings, acceptable ECG, and poison-center agreement when risk is uncertain.</p></section>
<section class="question-set section" id="assessment"><h2>Inline Assessment MCQs</h2>{build_mcqs()}</section>
</div></main></div><div class="score-pill" data-score-text>0 correct / 0 answered / 26 total</div><div class="image-modal" data-image-modal><button class="hdr-btn" data-modal-close>Close</button><img alt="Zoomed source"></div><script>{SCRIPT}</script></body></html>"""
    CHAPTER.write_text(doc, encoding="utf-8")
    print("rebuilt", CHAPTER)
    for token in ["source-card__label", "reference-image", "mcq-wrapper", "data-answer=", "<mark", "<u>", "Rosen source check", "Rosen vs Tintinalli"]:
        print(token, doc.count(token))


if __name__ == "__main__":
    main()
