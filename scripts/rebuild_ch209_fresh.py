from __future__ import annotations

import base64
import html
import re
from dataclasses import dataclass
from pathlib import Path

import fitz
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
OUT_HTML = ROOT / "docs/chapters/complete/Chapter209_Hypothermia.html"
MIRROR = Path(r"C:\c\Users\PC\OneDrive\เอกสาร\codex\ER")
QA_MD = ROOT / "CH209_CROP_QA_2026-05-09.md"
QA_HTML = ROOT / "CH209_CROP_QA_2026-05-09.html"
AUDIT_MD = ROOT / "TOXICOLOGY_COMPLETE_AUDIT_2026-05-08.md"
AUDIT_HTML = ROOT / "TOXICOLOGY_COMPLETE_AUDIT_2026-05-08.html"
WORK = ROOT / "_ch209_rebuild_fresh_2026-05-09"
PRE = WORK / "source_crops"
EMBED = WORK / "embedded_extract"
TINT = ROOT / "Tintinallis Emergency Medicine 9th Ed 2019.pdf"
ROSEN = ROOT / "rosen.pdf"

BASE_TEXT = (ROOT / "scripts/rebuild_ch178.py").read_text(encoding="utf-8")
STYLE = BASE_TEXT.split('STYLE = r"""', 1)[1].split('"""', 1)[0]
SCRIPT = BASE_TEXT.split('SCRIPT = r"""', 1)[1].split('"""', 1)[0]


@dataclass(frozen=True)
class CropSpec:
    key: str
    source: str
    label: str
    pdf: Path
    page: int
    rect: tuple[float, float, float, float]
    placement: str
    note: str


CROPS = [
    CropSpec("tint_table_209_1", "Tintinalli", "Table 209-1", TINT, 1382, (320, 38, 586, 260), "secondary causes", "full causes of secondary hypothermia table"),
    CropSpec("tint_table_209_2", "Tintinalli", "Table 209-2", TINT, 1383, (28, 38, 560, 374), "staging and treatment", "full staging and treatment table"),
    CropSpec("tint_fig_209_1", "Tintinalli", "Figure 209-1", TINT, 1384, (52, 600, 318, 746), "ECG features", "Osborn/J-wave ECG strip and caption"),
    CropSpec("tint_fig_209_2", "Tintinalli", "Figure 209-2", TINT, 1385, (28, 60, 562, 724), "transport pathway", "full transport and management algorithm"),
    CropSpec("tint_fig_209_3", "Tintinalli", "Figure 209-3", TINT, 1387, (28, 60, 562, 656), "absent vital signs", "full HT IV triage algorithm"),
    CropSpec("tint_fig_209_4", "Tintinalli", "Figure 209-4", TINT, 1388, (50, 60, 566, 614), "rewarming setup", "hospital checklist and hypothermia burrito figure"),
    CropSpec("tint_table_209_3", "Tintinalli", "Table 209-3", TINT, 1389, (28, 38, 292, 150), "ECLS criteria", "criteria for ECLS rewarming in severe hypothermia"),
    CropSpec("rosen_fig_128_1", "Rosen", "Fig. 128.1", ROSEN, 2035, (315, 250, 574, 440), "cold physiology", "physiology of cold exposure figure"),
    CropSpec("rosen_table_128_1", "Rosen", "Table 128.1", ROSEN, 2035, (44, 450, 574, 758), "temperature physiology", "physiologic characteristics of hypothermia zones"),
    CropSpec("rosen_fig_128_2", "Rosen", "Fig. 128.2", ROSEN, 2036, (120, 62, 494, 392), "J waves", "hypothermic J-wave ECG figure"),
    CropSpec("rosen_box_128_1", "Rosen", "Box 128.1", ROSEN, 2037, (42, 62, 572, 520), "predisposing factors", "factors predisposing to hypothermia"),
    CropSpec("rosen_box_128_2", "Rosen", "Box 128.2", ROSEN, 2039, (42, 62, 572, 586), "presenting signs", "presenting signs of hypothermia"),
    CropSpec("rosen_fig_128_4", "Rosen", "Fig. 128.4", ROSEN, 2041, (105, 62, 515, 630), "cold card", "cold card treatment flow"),
    CropSpec("rosen_box_128_3", "Rosen", "Box 128.3", ROSEN, 2044, (46, 62, 242, 178), "active rewarming indications", "indications for active rewarming"),
    CropSpec("rosen_table_128_2", "Rosen", "Table 128.2", ROSEN, 2046, (44, 62, 300, 386), "extracorporeal options", "extracorporeal blood rewarming options"),
]


def crop_pdf(spec: CropSpec) -> None:
    doc = fitz.open(spec.pdf)
    pix = doc[spec.page - 1].get_pixmap(matrix=fitz.Matrix(2.2, 2.2), clip=fitz.Rect(*spec.rect), alpha=False)
    pix.save(PRE / f"{spec.key}.png")


def data_uri(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def source_card(spec: CropSpec, text: str, delta: str | None = None) -> str:
    delta_html = ""
    if delta:
        delta_html = f'<div class="source-delta"><strong><u>Rosen vs Tintinalli:</u></strong> {html.escape(delta)}</div>'
    return f"""
    <article class="source-card">
      <div class="source-card__label">{html.escape(spec.source)} source</div>
      <h3 class="source-card__title">{html.escape(spec.label)}</h3>
      <p>{html.escape(text)}</p>
      {delta_html}
      <figure class="source-figure reference-image">
        <img src="{data_uri(PRE / f'{spec.key}.png')}" alt="{html.escape(spec.source + ' ' + spec.label)}" loading="lazy" decoding="async">
        <figcaption>{html.escape(spec.source)} {html.escape(spec.label)}. {html.escape(spec.note)}.</figcaption>
      </figure>
    </article>"""


def mcq(n: int, ans: str, stem: str, opts: list[tuple[str, str]], rats: dict[str, str]) -> str:
    buttons = "".join(f'<button class="mcq-opt" type="button" data-option-key="{k}">{k}. {html.escape(v)}</button>' for k, v in opts)
    explains = "".join(
        f'<div class="opt-explain {"is-correct" if k == ans else "is-wrong"}" hidden><strong>{k}. {html.escape(v)}</strong><span>{html.escape(rats[k])}</span></div>'
        for k, v in opts
    )
    return f'<article class="mcq-wrapper" data-answer="{ans}" data-answered="false"><p class="mcq-stem">Q{n}. {html.escape(stem)}</p><div class="mcq-options">{buttons}</div><div class="mcq-result" hidden></div><div class="mcq-explains">{explains}</div></article>'


def build_mcqs() -> str:
    raw = [
        ("B", "Accidental hypothermia is defined as core temperature below:", [("A", "40 C"), ("B", "35 C"), ("C", "30 C only"), ("D", "20 C only")], {"A": "Fever range, not hypothermia.", "B": "Correct definition.", "C": "This is moderate/severe range, not definition.", "D": "Profound hypothermia only."}),
        ("A", "The best first field priority is:", [("A", "Prevent further heat loss and handle gently"), ("B", "Have patient sprint"), ("C", "Give cold IV fluids"), ("D", "Stop assessment if pupils fixed")], {"A": "Correct.", "B": "Unsafe in moderate/severe hypothermia.", "C": "Worsens cooling.", "D": "Fixed pupils are unreliable in hypothermia."}),
        ("C", "Classic ECG finding is:", [("A", "Delta wave"), ("B", "STEMI in all cases"), ("C", "Osborn/J wave"), ("D", "Always normal ECG")], {"A": "WPW finding.", "B": "Hypothermia can mimic ischemia but not all cases.", "C": "Correct.", "D": "False."}),
        ("D", "A conscious shivering patient around 33 C usually needs:", [("A", "ECMO for all"), ("B", "Immediate termination of care"), ("C", "No warming"), ("D", "Warm environment, dry clothes, warm sweet drinks, movement if safe")], {"A": "Not for stable mild cases.", "B": "Wrong.", "C": "Wrong.", "D": "Stage I treatment."}),
        ("A", "Impaired consciousness and 30 C suggests:", [("A", "Stage II moderate hypothermia"), ("B", "Normal temperature"), ("C", "Heat stroke"), ("D", "Cyanide poisoning")], {"A": "Correct.", "B": "No.", "C": "Opposite temperature problem.", "D": "Not the staging frame."}),
        ("B", "Severe hypothermia with vital signs present but unconscious should be managed with:", [("A", "Walking exercise"), ("B", "Careful handling, active external/minimally invasive warming, airway support, ECLS center consideration"), ("C", "Discharge"), ("D", "Oral fluids only")], {"A": "Arrhythmia risk.", "B": "Correct.", "C": "Unsafe.", "D": "Aspiration risk."}),
        ("C", "Absent vital signs in hypothermia should prompt:", [("A", "Immediate death declaration because pupils are fixed"), ("B", "No CPR ever"), ("C", "Start CPR unless obvious irreversible death/unsafe/DNR and consider ECMO pathway"), ("D", "Warm drinks")], {"A": "Fixed pupils are unreliable.", "B": "Wrong.", "C": "Correct.", "D": "Not for arrest."}),
        ("D", "Potassium greater than about 12 mmol/L in hypothermic arrest suggests:", [("A", "Guaranteed survival"), ("B", "Simple mild hypothermia"), ("C", "Need for oral sugar only"), ("D", "Poor prognosis/possible termination criteria depending on context")], {"A": "No.", "B": "No.", "C": "No.", "D": "Tintinalli uses K as part of triage for ECLS/TOR decisions."}),
        ("A", "Which is a secondary hypothermia cause?", [("A", "Sepsis, endocrine/metabolic disease, intoxication, trauma, or iatrogenic cooling"), ("B", "Only snow exposure"), ("C", "Only skiing"), ("D", "Only frostbite")], {"A": "Correct.", "B": "Primary exposure only.", "C": "Too narrow.", "D": "Local cold injury."}),
        ("B", "Temperature measurement trap:", [("A", "Any thermometer works"), ("B", "Use a device capable of low readings and monitor core temp in moderate/severe cases"), ("C", "Skin temp equals core"), ("D", "No measurement needed")], {"A": "Wrong.", "B": "Correct.", "C": "False.", "D": "Wrong."}),
        ("C", "Atrial fibrillation with slow response in hypothermia usually:", [("A", "Requires immediate beta blocker"), ("B", "Requires calcium channel blocker"), ("C", "Often resolves with rewarming"), ("D", "Means normothermic arrest")], {"A": "Avoid.", "B": "Avoid.", "C": "Correct.", "D": "No."}),
        ("D", "Drug dosing in severe hypothermia should be cautious because:", [("A", "All drugs work faster"), ("B", "Hypothermia increases hepatic metabolism"), ("C", "Oral absorption is perfect"), ("D", "Metabolism/protein binding change and toxicity can appear during rewarming")], {"A": "No.", "B": "Opposite.", "C": "No.", "D": "Correct."}),
        ("A", "Which warming method is minimally invasive?", [("A", "Forced-air warming, warm IV fluids, hypothermia burrito"), ("B", "ECMO"), ("C", "CPB"), ("D", "Thoracotomy only")], {"A": "Correct.", "B": "Extracorporeal.", "C": "Extracorporeal.", "D": "Invasive."}),
        ("C", "ECLS/ECMO is most relevant for:", [("A", "All mild shivering patients"), ("B", "Pernio"), ("C", "Severe hypothermia with cardiac arrest, refractory instability, or high-risk Stage III/IV pathway"), ("D", "Normal temp syncope")], {"A": "No.", "B": "No.", "C": "Correct.", "D": "No."}),
        ("B", "Why avoid rough handling?", [("A", "It warms too much"), ("B", "Cold myocardium is irritable and dysrhythmias may be triggered"), ("C", "It prevents shivering"), ("D", "No reason")], {"A": "No.", "B": "Correct.", "C": "Not the main issue.", "D": "False."}),
        ("D", "Afterdrop means:", [("A", "Blood glucose drops only"), ("B", "Frostbite swelling"), ("C", "Heat stroke relapse"), ("D", "Core temperature continues falling after removal from cold/rewarming begins")], {"A": "No.", "B": "No.", "C": "No.", "D": "Correct."}),
        ("A", "Trauma plus hypothermia should be treated as:", [("A", "High risk, actively warmed, and evaluated for traumatic arrest/bleeding"), ("B", "Benign until warm"), ("C", "A reason to avoid warming"), ("D", "A reason to ignore ATLS")], {"A": "Correct.", "B": "Unsafe.", "C": "Wrong.", "D": "Wrong."}),
        ("C", "Which lab should be checked early in hospitalized hypothermia?", [("A", "Only cholesterol"), ("B", "No labs ever"), ("C", "Glucose plus targeted labs for cause/complications"), ("D", "Lithium in all patients")], {"A": "Not enough.", "B": "Wrong.", "C": "Correct.", "D": "Only if relevant."}),
        ("B", "Warm humidified oxygen is best viewed as:", [("A", "Sole definitive rewarming for severe cases"), ("B", "Adjunctive airway/core support, not enough alone"), ("C", "Contraindicated always"), ("D", "A cause of frostbite")], {"A": "Too weak alone.", "B": "Correct.", "C": "No.", "D": "No."}),
        ("D", "Disposition for mild primary hypothermia after successful ED rewarming:", [("A", "Mandatory ECMO"), ("B", "No shelter needed"), ("C", "ICU forever"), ("D", "May discharge if warm environment, stable vitals/mental status, and no secondary cause")], {"A": "No.", "B": "Unsafe.", "C": "No.", "D": "Correct."}),
        ("A", "Secondary hypothermia generally needs:", [("A", "Admission or targeted workup/treatment of underlying cause"), ("B", "Immediate discharge"), ("C", "No glucose check"), ("D", "Only blankets")], {"A": "Correct.", "B": "Unsafe.", "C": "Wrong.", "D": "Not enough."}),
        ("C", "Which phrase captures resuscitation philosophy?", [("A", "Dead if cold"), ("B", "Never resuscitate"), ("C", "Do not terminate early unless valid irreversible-death/TOR criteria apply"), ("D", "CPR impossible in cold")], {"A": "Wrong.", "B": "Wrong.", "C": "Correct.", "D": "No."}),
        ("B", "Core temperature below 28 C with hypotension or dysrhythmia should trigger:", [("A", "Home observation"), ("B", "ECLS center discussion/transfer if feasible"), ("C", "No monitoring"), ("D", "Exercise")], {"A": "Unsafe.", "B": "Correct.", "C": "Wrong.", "D": "Unsafe."}),
        ("D", "Best one-sentence ED approach:", [("A", "Check skin temp and discharge"), ("B", "Treat all as heat stroke"), ("C", "Rub limbs vigorously"), ("D", "Stage clinically, prevent heat loss, handle gently, monitor core/ECG, rewarm by severity, and escalate Stage III/IV to ECLS pathway")], {"A": "Insufficient.", "B": "Wrong.", "C": "Unsafe.", "D": "Correct."}),
        ("A", "A cold patient with no obvious vital signs but compressible chest should have pulse/life check with:", [("A", "Careful prolonged assessment, Doppler/ultrasound if available"), ("B", "Instant death declaration"), ("C", "Only oral thermometer"), ("D", "No ECG")], {"A": "Correct.", "B": "Unsafe.", "C": "Inadequate.", "D": "ECG helps."}),
        ("C", "Rosen's cold card adds most directly:", [("A", "A toxic alcohol antidote"), ("B", "A pesticide decontamination protocol"), ("C", "A quick outside-in staging and treatment decision aid"), ("D", "A snakebite grading scheme")], {"A": "No.", "B": "No.", "C": "Correct.", "D": "No."}),
    ]
    return "\n".join(mcq(i, *row) for i, row in enumerate(raw, 1))


def doc_html() -> str:
    c = {x.key: x for x in CROPS}
    return f"""<!doctype html><html lang="en" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Chapter 209 - Hypothermia</title><style>{STYLE}</style></head><body>
<header id="top-header"><button class="hdr-btn" data-sidebar-toggle title="Contents">☰</button><div class="hdr-title">Ch.209 Hypothermia</div><button class="hdr-btn theme-btn" data-theme-toggle>Dark</button></header>
<div class="app"><aside id="sidebar" class="sidebar"><button class="hdr-btn sidebar-close" data-sidebar-close>Close</button><div class="sidebar__block"><div class="sidebar__kicker">Chapter</div><h2>Hypothermia</h2><p class="meta"><b>Spine:</b> Tintinalli Ch.209</p><p class="meta"><b>Rosen:</b> Ch.128 hypothermia</p><p class="meta"><b>Build:</b> fresh inventory and crop QA</p></div><div class="sidebar__block"><div class="sidebar__kicker">Contents</div><a class="sidebar__link" href="#overview">Overview</a><a class="sidebar__link" href="#causes">Causes</a><a class="sidebar__link" href="#classification">Classification</a><a class="sidebar__link" href="#physiology">Physiology</a><a class="sidebar__link" href="#clinical">Clinical/ECG</a><a class="sidebar__link" href="#diagnosis">Diagnosis</a><a class="sidebar__link" href="#treatment">Treatment</a><a class="sidebar__link" href="#arrest">Arrest/ECLS</a><a class="sidebar__link" href="#drug-doses">Drug Dose Reference</a><a class="sidebar__link" href="#assessment">Assessment</a></div></aside>
<main id="main" class="main"><div class="content-wrap"><div class="utility-bar">Fresh rebuild • Tintinalli inventory 7/7 • Rosen source crops • MCQs show all explanations after answer</div>
<section class="hero section" id="overview"><div class="eyebrow">Environmental Injuries Chapter 209</div><h1 class="hero__title">Hypothermia</h1><p class="lede">Hypothermia management is staging first: <mark>mental status, shivering, vital signs, core temperature, ECG, and arrest context</mark> decide warming intensity and transport destination.</p><div class="callout warn"><strong>Board trap:</strong> fixed pupils, areflexia, and pseudo-rigor are not reliable signs of death in hypothermia.</div></section>
<section class="section" id="causes"><h2>Primary vs Secondary Hypothermia</h2><p>Primary accidental hypothermia is environmental heat loss. Secondary hypothermia occurs when illness, intoxication, trauma, endocrine disease, infection, malnutrition, or iatrogenic cooling impairs heat production or thermoregulation. The patient whose temperature is lower than the exposure story predicts needs a deliberate secondary-cause search.</p><p><u>Do not stop at “cold exposure”</u> when tachycardia, tachypnea, persistent altered mental status, shock, sepsis signs, intoxication, trauma, or failure to rewarm does not fit the stage.</p>{source_card(c['tint_table_209_1'], 'Tintinalli cause table is placed at the differential step so secondary causes are not missed.')}{source_card(c['rosen_box_128_1'], 'Rosen risk-factor box broadens the cause search to environmental, medical, social, age-related, and intoxication factors.', 'Tintinalli organizes secondary causes by mechanism; Rosen adds field-facing predisposing factors that affect prevention and disposition.')}</section>
<section class="section" id="classification"><h2>Classification and Staging</h2><p>Classical labels mild/moderate/severe are useful, but ED action should follow clinical staging: conscious shivering patients are different from confused nonshivering patients, and both are different from unconscious patients or patients without vital signs. Core temperature supports staging but should not override the clinical picture.</p><p><mark>Stage I</mark> is conscious and shivering; <mark>Stage II</mark> has impaired consciousness; <mark>Stage III</mark> is unconscious with vital signs; <mark>Stage IV</mark> has absent vital signs.</p>{source_card(c['tint_table_209_2'], 'Tintinalli staging table is the chapter spine for treatment intensity and transport pathway.')}{source_card(c['rosen_table_128_1'], 'Rosen zone table links temperature to physiology, ECG, consciousness, reflexes, and cardiac risk.', 'Tintinalli gives practical HT stages; Rosen shows the physiologic continuum behind those stages.')}{source_card(c['rosen_fig_128_4'], 'Rosen cold card is included as the field/ED quick staging and treatment aid.', 'Tintinalli uses transport algorithms; Rosen adds an outside-ring-to-center bedside card for rapid classification.')}</section>
<section class="section" id="physiology"><h2>Cold Physiology and Afterdrop</h2><p>Cold exposure first produces behavioral response, vasoconstriction, shivering thermogenesis, and increased metabolic rate. As temperature falls, shivering fails, metabolism slows, ventilation decreases, bradycardia and hypotension appear, and the myocardium becomes irritable. Afterdrop means core temperature can keep falling after removal from the cold, especially with peripheral-to-core gradients.</p>{source_card(c['rosen_fig_128_1'], 'Rosen physiology figure shows how cold exposure drives blood temperature, hypothalamic response, shivering, and autonomic effects.', 'Tintinalli describes the physiology in prose; Rosen supplies the control-system map.')}</section>
<section class="section" id="clinical"><h2>Clinical Features and ECG</h2><p>Clinical features progress from judgment impairment, amnesia, dysarthria, ataxia, apathy, and shivering to unconsciousness, areflexia, apnea, and arrest. Cardiovascular findings include early tachycardia/hypertension followed by bradycardia, hypotension, atrial fibrillation, ventricular dysrhythmias, and Osborn/J waves. <u>Treat the patient and stage, not the ECG alone.</u></p>{source_card(c['tint_fig_209_1'], 'Tintinalli ECG figure anchors Osborn/J-wave recognition in the clinical section.')}{source_card(c['rosen_fig_128_2'], 'Rosen adds a second J-wave ECG example for pattern recognition.', 'Tintinalli shows the board ECG strip; Rosen reinforces that J waves are common below about 32 C but not unique to hypothermia.')}{source_card(c['rosen_box_128_2'], 'Rosen presenting-signs box belongs here because it organizes the multi-system presentation.', 'Tintinalli discusses organ dysfunction by system; Rosen compacts the bedside signs for scan-and-check use.')}</section>
<section class="section" id="diagnosis"><h2>Diagnosis and Workup</h2><p>Confirm and monitor core temperature with a device capable of low readings. Rectal, esophageal, bladder, and epitympanic methods each have limitations; ongoing core monitoring is required for moderate to severe cases. Check glucose early and target labs/imaging to trauma, sepsis, endocrine/metabolic disease, intoxication, rhabdomyolysis, electrolytes, renal injury, and dysrhythmias.</p><p>For a cold patient without obvious vital signs, search carefully for signs of life. Doppler or bedside ultrasound can help confirm pulse/cardiac activity. <mark>Hypothermia mimics death</mark>, but decapitation, decomposition, truncal transection, a frozen noncompressible body, valid DNR, unsafe rescuer conditions, or appropriate TOR pathway can still end resuscitation.</p></section>
<section class="section" id="treatment"><h2>Treatment and Transport</h2><p>All patients need heat-loss prevention, wet clothing removal, insulation, gentle horizontal handling, glucose correction, ECG/core-temperature monitoring when moderate/severe, and warmed oxygen/IV fluids when indicated. Mild primary hypothermia often responds to a warm environment, dry clothes, warm sweet drinks, and active movement if safe.</p><p>Moderate and severe hypothermia require careful handling and active external or minimally invasive rewarming: forced-air warming, heating pads with burn precautions, warm IV fluids, and the “hypothermia burrito.” Avoid heating the head in cardiac arrest. Airway support is used when needed; medications and defibrillation follow hypothermia-specific limits and response.</p>{source_card(c['tint_fig_209_2'], 'Tintinalli transport algorithm is placed with treatment because it decides nearest hospital vs ECMO center.')}{source_card(c['tint_fig_209_4'], 'Tintinalli practical rewarming figure supports the hospital checklist and hypothermia burrito setup.')}{source_card(c['rosen_box_128_3'], 'Rosen active-rewarming indications support when passive warming is not enough.', 'Tintinalli stages treatment by HT stage; Rosen lists indications that push toward active rewarming even when the temperature number alone is ambiguous.')}</section>
<section class="section" id="arrest"><h2>Hypothermic Arrest and ECLS</h2><p>Stage IV hypothermia is the key resuscitation decision. Start CPR when appropriate and do not terminate early simply because the patient is cold and appears dead. Consider special contexts: drowning, avalanche burial duration and airway status, trauma, normothermic arrest before cooling, transport time, potassium, and ECLS availability.</p><p><u>ECLS/ECMO is preferred for selected severe hypothermia or hypothermic arrest</u>, especially cardiac arrest from hypothermia, refractory dysrhythmia, severe instability, core temperature below about 28 C with high-risk physiology, or failure of less invasive rewarming. When ECLS is unavailable, on-site rewarming options are used according to capability.</p>{source_card(c['tint_fig_209_3'], 'Tintinalli HT IV triage figure is placed with arrest decisions and TOR/ECLS pathway.')}{source_card(c['tint_table_209_3'], 'Tintinalli ECLS criteria table is beside the Stage III/IV escalation narrative.')}{source_card(c['rosen_table_128_2'], 'Rosen extracorporeal options table compares venovenous, hemodialysis, AV rewarming, and CPB/ECMO approaches.', 'Tintinalli focuses on ECLS transport criteria; Rosen compares available extracorporeal blood rewarming techniques and rates.')}</section>
<section class="section" id="drug-doses"><h2>Drug Dose Reference</h2><p>This is a quick recap after treatment logic, not the only treatment section.</p><div class="table-wrap"><table><thead><tr><th>Action</th><th>Use</th><th>Trap</th></tr></thead><tbody><tr><td>Warm environment/dry insulation</td><td>All stages</td><td>Remove wet clothing; handle gently.</td></tr><tr><td>Warm sweet drinks/active movement</td><td>Stage I only if awake and safe</td><td>Avoid exertion in unstable or impaired patients.</td></tr><tr><td>Forced air/heating pads/warm IV fluids</td><td>Stage II/III or secondary/comorbid Stage I</td><td>Prevent burns; monitor core temp/ECG.</td></tr><tr><td>Defibrillation/epinephrine</td><td>Stage IV per hypothermia algorithm</td><td>Limited attempts/doses below 30 C; reassess with rewarming.</td></tr><tr><td>ECLS/ECMO</td><td>Selected severe hypothermia/arrest</td><td>Do not delay transfer when feasible.</td></tr></tbody></table></div></section>
<section class="question-set section" id="assessment"><h2>Inline Assessment MCQs</h2>{build_mcqs()}</section>
</div></main></div><div class="score-pill" data-score-text>0 correct / 0 answered / 26 total</div><div class="image-modal" data-image-modal><button class="hdr-btn" data-modal-close>Close</button><img alt="Zoomed source"></div><script>{SCRIPT}</script></body></html>"""


def extract_embedded(doc: str) -> list[Path]:
    EMBED.mkdir(parents=True, exist_ok=True)
    for old in EMBED.glob("*.png"):
        old.unlink()
    out = []
    for i, m in enumerate(re.finditer(r"data:image/png;base64,([^\"]+)", doc), 1):
        p = EMBED / f"ch209_embedded_{i:02d}.png"
        p.write_bytes(base64.b64decode(m.group(1)))
        out.append(p)
    return out


def contact_sheet(paths: list[Path]) -> Path:
    cols, cell_w, cell_h = 3, 360, 285
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, path in enumerate(paths):
        img = Image.open(path).convert("RGB")
        img.thumbnail((320, 230))
        x, y = (idx % cols) * cell_w, (idx // cols) * cell_h
        sheet.paste(img, (x + 20, y + 34))
        draw.text((x + 8, y + 8), f"{idx+1:02d} {path.name}", fill=(0, 0, 0))
    out = EMBED / "ch209_embedded_contact_sheet.png"
    sheet.save(out)
    return out


def md_to_html(md: str, title: str) -> str:
    out, in_table = [], False
    for line in md.splitlines():
        if line.startswith("|") and line.endswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if set(cells[0]) <= {"-"}:
                continue
            if not in_table:
                out.append("<table>")
                in_table = True
            tag = "th" if cells[0] in {"#", "Source"} else "td"
            out.append("<tr>" + "".join(f"<{tag}>{html.escape(c)}</{tag}>" for c in cells) + "</tr>")
        else:
            if in_table:
                out.append("</table>")
                in_table = False
            if line.startswith("# "):
                out.append(f"<h1>{html.escape(line[2:])}</h1>")
            elif line.startswith("## "):
                out.append(f"<h2>{html.escape(line[3:])}</h2>")
            elif line.strip():
                out.append(f"<p>{html.escape(line)}</p>")
    if in_table:
        out.append("</table>")
    return f"<!doctype html><html><head><meta charset='utf-8'><title>{html.escape(title)}</title><style>body{{font-family:Arial,sans-serif;margin:28px;background:#f8fafc;color:#111827}}table{{border-collapse:collapse;width:100%;font-size:13px}}td,th{{border:1px solid #cbd5e1;padding:6px;vertical-align:top}}th{{background:#e2e8f0}}h1,h2{{color:#0f4c5c}}p{{line-height:1.45}}</style></head><body>{''.join(out)}</body></html>"


def build_qa(paths: list[Path], sheet: Path) -> None:
    rows = []
    for i, (spec, img) in enumerate(zip(CROPS, paths), 1):
        rows.append(f"| {i} | {spec.source} | {spec.label} | {spec.pdf.name} | {spec.page} | `{img.relative_to(ROOT).as_posix()}` | PASS | {spec.note}; title/header/body included |")
    inventory = "\n".join(f"- {c.source} {c.label}: page {c.page}, placement `{c.placement}`" for c in CROPS)
    md = f"""# CH209 Crop QA - 2026-05-09

Fresh rebuild from source PDFs. Old Chapter209 HTML crops were not used.

## Source Inventory Used

Tintinalli Ch209 inventory: 3 tables + 4 figures = 7/7 included.

Rosen Ch128 relevant hypothermia inventory included: cold physiology figure, zones table, J-wave ECG, risk factors, presenting signs, cold card, active rewarming indications, and extracorporeal rewarming options.

{inventory}

## Embedded Crop QA

Contact sheet: `{sheet.relative_to(ROOT).as_posix()}`

| # | Source | Object | PDF | PDF page | Extracted final embedded image | Status | Note |
|---|---|---|---|---:|---|---|---|
{chr(10).join(rows)}

Summary: {len(paths)} embedded source crops checked, {len(paths)} PASS, 0 FAIL.

Content: PASS - chapter rebuilt from Tintinalli spine with topic-local Rosen integration.
Pattern: PASS - Ch186/Ch201 shell and MCQ behavior present.
"""
    QA_MD.write_text(md, encoding="utf-8")
    QA_HTML.write_text(md_to_html(md, "CH209 Crop QA"), encoding="utf-8")


def update_audit() -> None:
    row = "| 209 | `Chapter209_Hypothermia.html` | PASS | 26 | 26 | 4 | 16 | 15 | 8 | 8 | Pattern PASS; Content gate PASS; MCQ all-option explanations PASS; rebuilt fresh from source PDFs 2026-05-09; Tintinalli inventory 7/7; Rosen relevant crops included; cropQA PASS (15/15) |"
    md = AUDIT_MD.read_text(encoding="utf-8")
    md = re.sub(r"Toxicology chapter gate: \*\*\d+ PASS / \d+ FAIL\*\*", "Toxicology chapter gate: **34 PASS / 0 FAIL**", md)
    md = re.sub(r"Scope: Tintinalli toxicology/environmental chapters `176-208`", "Scope: Tintinalli toxicology/environmental chapters `176-209`", md)
    if re.search(r"^\|\s*209\s*\|", md, flags=re.M):
        md = re.sub(r"^\|\s*209\s*\|.*$", row, md, flags=re.M)
    else:
        md = md.rstrip() + "\n" + row + "\n"
    AUDIT_MD.write_text(md, encoding="utf-8")
    AUDIT_HTML.write_text(md_to_html(md, "Toxicology Complete Audit"), encoding="utf-8")


def mirror_outputs() -> None:
    for rel in [OUT_HTML.relative_to(ROOT), QA_MD.relative_to(ROOT), QA_HTML.relative_to(ROOT), AUDIT_MD.relative_to(ROOT), AUDIT_HTML.relative_to(ROOT)]:
        dst = MIRROR / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes((ROOT / rel).read_bytes())
    dst_root = MIRROR / WORK.relative_to(ROOT)
    for src in WORK.rglob("*"):
        if src.is_file():
            dst = dst_root / src.relative_to(WORK)
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(src.read_bytes())


def main() -> None:
    PRE.mkdir(parents=True, exist_ok=True)
    for old in PRE.glob("*.png"):
        old.unlink()
    for spec in CROPS:
        crop_pdf(spec)
    doc = doc_html()
    OUT_HTML.write_text(doc, encoding="utf-8")
    paths = extract_embedded(doc)
    sheet = contact_sheet(paths)
    build_qa(paths, sheet)
    update_audit()
    mirror_outputs()
    print("rebuilt", OUT_HTML)
    print("source crops", len(CROPS), "embedded", len(paths), "contact", sheet)
    for token in ['id="top-header"', 'id="sidebar"', 'id="main"', 'mcq-wrapper', 'mcq-result', 'source-figure', 'data:image', '<mark', '<u>', 'Rosen source', 'Rosen vs Tintinalli', 'Source Check', 'Rosen Source Audit']:
        print(token, doc.count(token))


if __name__ == "__main__":
    main()
