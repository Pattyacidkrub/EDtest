from pathlib import Path
import html
import re

ROOT = Path(__file__).resolve().parents[1]
CHAPTER = ROOT / "docs/chapters/complete/Chapter181_Lithium.html"
BASE = ROOT / "scripts/rebuild_ch178.py"
BASE_TEXT = BASE.read_text(encoding="utf-8")
STYLE = BASE_TEXT.split('STYLE = r"""', 1)[1].split('"""', 1)[0]
SCRIPT = BASE_TEXT.split('SCRIPT = r"""', 1)[1].split('"""', 1)[0]


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
        ("B", "Why can chronic lithium toxicity be severe at lower serum levels than acute ingestion?", [("A", "Lithium binds charcoal tightly"), ("B", "Lithium has had time to distribute into the CNS"), ("C", "Lithium is metabolized to cyanide"), ("D", "The level is always falsely zero")], {"A": "Charcoal does not bind lithium.", "B": "Chronic exposure allows CNS distribution, so symptoms can be severe at lower serum values.", "C": "No cyanide metabolite.", "D": "Levels are useful when interpreted with timing."}),
        ("A", "First-line elimination support for volume-depleted lithium toxicity?", [("A", "Isotonic saline resuscitation"), ("B", "Fluid restriction"), ("C", "Loop diuretic loading"), ("D", "Activated charcoal")], {"A": "Saline corrects volume depletion and supports renal lithium elimination.", "B": "Worsens clearance.", "C": "Can worsen volume/electrolytes.", "D": "Charcoal does not bind lithium."}),
        ("D", "Which medication can precipitate lithium toxicity by reducing clearance?", [("A", "Albuterol"), ("B", "Ondansetron"), ("C", "Acetaminophen"), ("D", "Thiazide diuretic")], {"A": "Not a classic interaction.", "B": "Not the main lithium-clearance interaction.", "C": "Not typical.", "D": "Thiazides increase lithium levels through renal handling."}),
        ("C", "Sustained-release lithium ingestion with rising levels and protected airway may need:", [("A", "Naloxone"), ("B", "Physostigmine"), ("C", "Whole-bowel irrigation"), ("D", "Urine alkalinization")], {"A": "Opioid antidote.", "B": "Not lithium care.", "C": "Selected sustained-release ingestions can benefit from WBI.", "D": "Not lithium therapy."}),
        ("A", "Which finding strongly supports dialysis discussion?", [("A", "Coma or seizure with lithium toxicity"), ("B", "Mild nausea with falling levels"), ("C", "Remote tiny asymptomatic exposure"), ("D", "Normal creatinine and resolved symptoms")], {"A": "Severe neurologic toxicity is a major dialysis trigger.", "B": "May be observed with improvement.", "C": "Lower risk.", "D": "Less likely to need dialysis."}),
        ("B", "Why repeat lithium levels after hemodialysis?", [("A", "Lithium becomes acetaminophen"), ("B", "Post-dialysis rebound from redistribution can occur"), ("C", "Dialysis increases GI absorption"), ("D", "Levels are meaningless")], {"A": "No.", "B": "Lithium redistributes from tissues after dialysis.", "C": "No.", "D": "Serial levels remain important."}),
        ("C", "Which early test set is most useful?", [("A", "Urine drug screen only"), ("B", "Carboxyhemoglobin only"), ("C", "Serial lithium level, BMP/creatinine, electrolytes, ECG/clinical monitoring, pregnancy test when relevant"), ("D", "Liver enzymes only")], {"A": "UDS does not guide lithium.", "B": "Unrelated unless exposure suggests.", "C": "Correct.", "D": "Not the core."}),
        ("D", "Activated charcoal for isolated lithium ingestion is:", [("A", "The antidote"), ("B", "Mandatory for all"), ("C", "Useful because lithium is protein bound"), ("D", "Not useful because it does not bind lithium")], {"A": "No antidote.", "B": "No.", "C": "Lithium is not meaningfully protein bound.", "D": "Correct."}),
        ("A", "Classic lithium neurotoxicity includes:", [("A", "Coarse tremor, ataxia, dysarthria, confusion, myoclonus, seizures"), ("B", "Pinpoint pupils and apnea only"), ("C", "Bronchorrhea and salivation"), ("D", "Cherry-red skin")], {"A": "Correct.", "B": "Opioid pattern.", "C": "Cholinergic.", "D": "Not lithium."}),
        ("B", "Acute ingestion with high early level but minimal symptoms requires:", [("A", "Immediate discharge"), ("B", "Serial levels and observation because absorption/distribution may evolve"), ("C", "No renal testing"), ("D", "Only antipyretics")], {"A": "Unsafe.", "B": "Correct.", "C": "Renal function is central.", "D": "Not enough."}),
        ("C", "Main lithium elimination route?", [("A", "Hepatic CYP metabolism"), ("B", "Pulmonary exhalation"), ("C", "Renal excretion"), ("D", "Biliary secretion only")], {"A": "No.", "B": "No.", "C": "Correct.", "D": "No."}),
        ("A", "Highest-risk patient despite a moderate level?", [("A", "Elderly chronic user with confusion and renal impairment"), ("B", "Young asymptomatic acute exposure with falling levels"), ("C", "Normal renal function and no symptoms"), ("D", "Remote ingestion with undetectable level")], {"A": "Chronic CNS burden plus poor clearance is dangerous.", "B": "Lower risk.", "C": "Lower risk.", "D": "Lower risk."}),
        ("D", "Seizures from lithium toxicity should be treated initially with:", [("A", "Phenytoin only"), ("B", "More lithium"), ("C", "Activated charcoal"), ("D", "Benzodiazepines")], {"A": "Benzodiazepines first.", "B": "Wrong.", "C": "Does not bind lithium.", "D": "Correct."}),
        ("B", "Which factor lowers threshold for nephrology/toxicology consultation?", [("A", "Normal exam and falling level"), ("B", "Rising level with acute-on-chronic exposure"), ("C", "Single low level after remote exposure"), ("D", "Resolved nausea only")], {"A": "Less concerning.", "B": "Correct.", "C": "Lower risk.", "D": "Less concerning."}),
        ("C", "Disposition should wait for:", [("A", "One normal pulse"), ("B", "Negative UDS"), ("C", "Improving symptoms, adequate renal function, and serial lithium levels trending down"), ("D", "Patient request alone")], {"A": "Insufficient.", "B": "UDS not the decision tool.", "C": "Correct.", "D": "Not enough."}),
        ("A", "Why does dehydration worsen lithium toxicity?", [("A", "It reduces renal clearance and promotes lithium retention"), ("B", "It binds lithium in the gut"), ("C", "It creates cyanide"), ("D", "It makes lithium evaporate")], {"A": "Correct.", "B": "No.", "C": "No.", "D": "No."}),
        ("D", "Which exposure pattern is most concerning for delayed diagnosis?", [("A", "No exposure"), ("B", "Tiny one-time ingestion with negative serial levels"), ("C", "Remote resolved symptoms"), ("D", "Chronic toxicity from dose change, dehydration, or interacting medication")], {"A": "No.", "B": "Lower risk.", "C": "Lower risk.", "D": "Chronic toxicity can be subtle and severe."}),
        ("B", "Whole-bowel irrigation is most relevant for:", [("A", "Remote therapeutic dose"), ("B", "Large sustained-release ingestion with protected airway"), ("C", "All chronic toxicity"), ("D", "Any patient vomiting blood")], {"A": "No.", "B": "Correct.", "C": "No.", "D": "Contraindications matter."}),
        ("C", "Dialysis decision should be based on:", [("A", "Serum number only"), ("B", "Patient preference only"), ("C", "Symptoms, renal function, exposure pattern, level trend, and severity"), ("D", "Urine color only")], {"A": "Too narrow.", "B": "No.", "C": "Correct.", "D": "No."}),
        ("A", "Which chronic adverse effect can increase toxicity risk?", [("A", "Nephrogenic diabetes insipidus/renal dysfunction"), ("B", "Improved renal clearance"), ("C", "Complete immunity"), ("D", "Cyanide storage")], {"A": "Renal problems and volume depletion increase risk.", "B": "Wrong.", "C": "No.", "D": "No."}),
        ("D", "What is the board trap with early acute lithium levels?", [("A", "They are always useless"), ("B", "They diagnose cyanide"), ("C", "They replace symptoms"), ("D", "They can be high before CNS distribution or still rising with sustained release")], {"A": "They are useful in trend.", "B": "No.", "C": "No.", "D": "Correct."}),
        ("B", "Which symptom should trigger concern for severe neurotoxicity?", [("A", "Mild nausea only"), ("B", "Ataxia with confusion and myoclonus"), ("C", "Isolated rhinorrhea"), ("D", "Normal exam")], {"A": "Less severe.", "B": "Correct.", "C": "No.", "D": "No."}),
        ("C", "A patient taking lithium starts an ACE inhibitor and becomes confused. What should you suspect?", [("A", "No relationship"), ("B", "Opioid withdrawal"), ("C", "Reduced lithium clearance causing toxicity"), ("D", "Methemoglobinemia")], {"A": "Wrong.", "B": "No.", "C": "Correct.", "D": "No."}),
        ("D", "After dialysis, a rising lithium level means:", [("A", "The lab is forbidden"), ("B", "Lithium was cured"), ("C", "Discharge immediately"), ("D", "Rebound/redistribution may require more monitoring or repeat dialysis")], {"A": "No.", "B": "No.", "C": "Unsafe.", "D": "Correct."}),
        ("A", "Drug Dose Reference should:", [("A", "Recap doses after treatment logic appears in the clinical sections"), ("B", "Be the only treatment section"), ("C", "Replace dialysis discussion"), ("D", "Hide source tables")], {"A": "Correct.", "B": "Wrong.", "C": "Wrong.", "D": "Wrong."}),
        ("C", "Best one-sentence ED approach?", [("A", "Give charcoal and discharge"), ("B", "Ignore renal function"), ("C", "Classify exposure pattern, hydrate, trend levels/renal function, treat neurotoxicity, and dialyze severe cases"), ("D", "Use flumazenil for all")], {"A": "Wrong.", "B": "Wrong.", "C": "Correct.", "D": "Dangerous."}),
    ]
    return "\n".join(mcq(i, *item) for i, item in enumerate(raw, 1))


def main() -> None:
    old = CHAPTER.read_text(encoding="utf-8")
    backup = CHAPTER.with_suffix(CHAPTER.suffix + ".bak_rebuild_20260508")
    if not backup.exists():
        backup.write_bytes(CHAPTER.read_bytes())
    figs = extract_figures(old)
    for idx in (4, 8):
        if idx not in figs:
            raise RuntimeError(f"Missing source figure {idx}")
    doc = f"""<!doctype html><html lang="en" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Chapter 181 - Lithium</title><style>{STYLE}</style></head><body>
<header id="top-header"><button class="hdr-btn" data-sidebar-toggle title="Contents">☰</button><div class="hdr-title">Ch.181 Lithium</div><button class="hdr-btn theme-btn" data-theme-toggle>Dark</button></header>
<div class="app"><aside id="sidebar" class="sidebar"><button class="hdr-btn sidebar-close" data-sidebar-close>Close</button><div class="sidebar__block"><div class="sidebar__kicker">Chapter</div><h2>Lithium</h2><p class="meta"><b>Spine:</b> Tintinalli Ch.181</p><p class="meta"><b>Pattern:</b> Ch186/Ch201 rebuild</p></div><div class="sidebar__block"><div class="sidebar__kicker">Contents</div><a class="sidebar__link" href="#overview">Overview</a><a class="sidebar__link" href="#pk">PK</a><a class="sidebar__link" href="#features">Clinical Features</a><a class="sidebar__link" href="#diagnosis">Diagnosis</a><a class="sidebar__link" href="#treatment">Treatment</a><a class="sidebar__link" href="#dialysis">Dialysis</a><a class="sidebar__link" href="#drug-doses">Drug Dose Reference</a><a class="sidebar__link" href="#disposition">Disposition</a><a class="sidebar__link" href="#assessment">Assessment</a></div></aside>
<main id="main" class="main"><div class="content-wrap"><div class="utility-bar">Rebuilt chapter • table crops topic-local • MCQs show all explanations after answer • final crop QA</div>
<section class="hero section" id="overview"><div class="eyebrow">Toxicology Chapter 181</div><h1 class="hero__title">Lithium</h1><p class="lede">Lithium toxicity is a kinetics chapter: the number matters, but <mark>exposure pattern, renal function, volume status, neurologic exam, and serial trend</mark> decide management.</p><div class="callout warn"><strong>Board frame:</strong> acute, chronic, and acute-on-chronic lithium poisoning are not interpreted the same way.</div>{rosen_card("Rosen source check: lithium level interpretation", "Rosen emphasizes that lithium levels must be interpreted with exposure timing, symptoms, and renal function.", "Tintinalli organizes the ED management and dialysis triggers; Rosen reinforces not treating a single number without the clinical pattern.")}</section>
<section class="section" id="pk"><h2>Pharmacokinetics</h2><p>Lithium is a small monovalent cation with minimal protein binding and renal elimination. Volume depletion, renal impairment, NSAIDs, ACE inhibitors, ARBs, and thiazide diuretics can reduce clearance and raise levels. <u>Chronic toxicity</u> is dangerous because lithium has already distributed into the CNS.</p><p>Acute ingestions may have high early serum levels before CNS toxicity evolves, while sustained-release preparations can continue absorbing. Serial levels and repeated neurologic exams are mandatory when the timing or formulation is uncertain.</p></section>
<section class="section" id="features"><h2>Clinical Features</h2><p>GI symptoms such as nausea, vomiting, and diarrhea often occur early, but the dangerous findings are neurologic: <mark>coarse tremor, ataxia, dysarthria, confusion, myoclonus, seizures, and coma</mark>. Chronic toxicity may present subtly with weakness, falls, delirium, or worsening tremor.</p>{source_card(figs, 4, "Tintinalli Table 181-1. Clinical features of lithium toxicity", "Clinical feature table placed beside the symptom narrative where severity is recognized.")}</section>
<section class="section" id="diagnosis"><h2>Diagnosis</h2><p>Diagnosis uses the history, exposure pattern, symptoms, renal function, electrolytes, and serial lithium concentrations. A single level is never enough when the ingestion is acute, sustained-release, or acute-on-chronic. Check creatinine, sodium, glucose, ECG when indicated, pregnancy status when relevant, and coingestants if the story is unclear.</p><p><u>Do not be falsely reassured</u> by a moderate level in a chronic user with confusion or ataxia.</p></section>
<section class="section" id="treatment"><h2>Treatment</h2><p>Stop lithium and interacting drugs, protect the airway if needed, treat seizures with benzodiazepines, and restore euvolemia with isotonic saline. Hydration supports renal elimination, but monitor for volume overload in renal or cardiac disease.</p><p>Activated charcoal does not bind lithium. Whole-bowel irrigation can be considered for selected large sustained-release ingestions if the patient is stable and the airway is protected.</p>{source_card(figs, 8, "Tintinalli Table 181-2. Management of lithium toxicity", "Management table placed with treatment because it summarizes decontamination, fluids, and enhanced elimination.")}</section>
<section class="section" id="dialysis"><h2>Dialysis / Extracorporeal Removal</h2><p><mark>Hemodialysis is the definitive enhanced elimination tool</mark> for severe lithium poisoning because lithium is small, water soluble, and minimally protein bound. The decision is clinical: coma, seizure, severe confusion, dysrhythmia, renal failure, very high or rising levels, and chronic toxicity with neurologic impairment all lower the threshold.</p><p>Rebound can occur after dialysis as lithium redistributes from tissues, so levels and symptoms must be followed after treatment and dialysis repeated when needed.</p>{rosen_card("Rosen source check: dialysis threshold", "Rosen also frames dialysis around severe symptoms, renal impairment, and kinetic trend rather than a single isolated value.", "Tintinalli provides the management flow; Rosen reinforces clinical severity and post-dialysis rebound monitoring.")}</section>
<section class="section" id="drug-doses"><h2>Drug Dose Reference</h2><p>This is a quick recap after the clinical treatment sections, not a replacement for them.</p><div class="table-wrap"><table><thead><tr><th>Intervention</th><th>Use</th><th>Caution</th></tr></thead><tbody><tr><td>Isotonic saline</td><td>Correct volume depletion and support renal clearance</td><td>Avoid overload; monitor sodium/renal function.</td></tr><tr><td>Whole-bowel irrigation</td><td>Selected large sustained-release ingestion with protected airway</td><td>Avoid if ileus, obstruction, unstable airway, or shock.</td></tr><tr><td>Hemodialysis</td><td>Severe neurologic toxicity, renal failure, rising/high levels, or chronic toxicity with impairment</td><td>Monitor for rebound and repeat if needed.</td></tr></tbody></table></div></section>
<section class="section" id="disposition"><h2>Disposition</h2><p>Admit symptomatic patients, chronic toxicity, renal impairment, rising levels, sustained-release ingestion, or anyone needing dialysis consideration. Discharge requires improving symptoms, stable renal function, reliable follow-up, and serial lithium levels trending down.</p></section>
<section class="question-set section" id="assessment"><h2>Inline Assessment MCQs</h2>{build_mcqs()}</section>
</div></main></div><div class="score-pill" data-score-text>0 correct / 0 answered / 26 total</div><div class="image-modal" data-image-modal><button class="hdr-btn" data-modal-close>Close</button><img alt="Zoomed source"></div><script>{SCRIPT}</script></body></html>"""
    CHAPTER.write_text(doc, encoding="utf-8")
    print("rebuilt", CHAPTER)
    for token in ["source-card__label", "reference-image", "mcq-wrapper", "data-answer=", "<mark", "<u>", "Rosen source check", "Rosen vs Tintinalli", "reveal-all", "Source Check"]:
        print(token, doc.count(token))


if __name__ == "__main__":
    main()
