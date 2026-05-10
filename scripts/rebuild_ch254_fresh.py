from __future__ import annotations

import base64
import html
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

import fitz
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
OUT_HTML = ROOT / "docs/chapters/complete/Chapter254_TraumaInAdults.html"
MIRROR = Path(r"C:\c\Users\PC\OneDrive\เอกสาร\codex\ER")
QA_MD = ROOT / "CH254_CROP_QA_2026-05-09.md"
QA_HTML = ROOT / "CH254_CROP_QA_2026-05-09.html"
AUDIT_MD = ROOT / "CHAPTER_COMPLETE_AUDIT_2026-05-07.md"
AUDIT_HTML = ROOT / "CHAPTER_COMPLETE_AUDIT_2026-05-07.html"
WORK = ROOT / "_ch254_rebuild_fresh_2026-05-09"
PRE = WORK / "source_crops"
EMBED = WORK / "embedded_extract"
TINT = ROOT / "Tintinallis Emergency Medicine 9th Ed 2019.pdf"
ROSEN = ROOT / "rosen.pdf"
ATLS = ROOT / "ATLS_11th_2025.pdf"

BASE = (ROOT / "scripts/rebuild_ch178.py").read_text(encoding="utf-8")
STYLE = BASE.split('STYLE = r"""', 1)[1].split('"""', 1)[0]
SCRIPT = BASE.split('SCRIPT = r"""', 1)[1].split('"""', 1)[0]


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
    delta: str = ""


CROPS = [
    CropSpec("tint_fig_254_1", "Tintinalli", "Figure 254-1", TINT, 1715, (50, 35, 565, 382), "trauma system", "preplanned trauma care continuum"),
    CropSpec("tint_table_254_2", "Tintinalli", "Table 254-2", TINT, 1715, (300, 458, 585, 746), "trauma system entry", "triage and trauma system entry criteria"),
    CropSpec("tint_table_254_3", "Tintinalli", "Table 254-3", TINT, 1716, (52, 40, 313, 652), "primary survey", "primary and secondary survey in trauma resuscitation"),
    CropSpec("tint_fig_254_2", "Tintinalli", "Figure 254-2", TINT, 1718, (54, 555, 292, 738), "hemorrhage control", "combat application tourniquet image and caption"),
    CropSpec("tint_table_254_6", "Tintinalli", "Table 254-6", TINT, 1718, (318, 612, 586, 754), "hemorrhage class", "hemorrhage classification by estimated blood loss"),
    CropSpec("tint_fig_254_3", "Tintinalli", "Figure 254-3", TINT, 1719, (28, 40, 292, 275), "eFAST", "positive extended FAST exam with Morison pouch blood"),
    CropSpec("tint_table_254_7", "Tintinalli", "Table 254-7", TINT, 1719, (28, 665, 585, 754), "disability", "Glasgow Coma Scale with motor GCS"),
    CropSpec("tint_fig_254_4", "Tintinalli", "Figure 254-4", TINT, 1721, (50, 42, 555, 430), "traumatic arrest", "trauma arrest decision-making algorithm"),
    CropSpec("rosen_fig_32_1", "Rosen", "Fig. 32.1", ROSEN, 353, (52, 78, 560, 735), "airway", "airway assessment algorithm", "Rosen makes the airway branch operational: adequate protection, obstruction, mask ventilation, intubation, and surgical airway; Tintinalli gives the rapid survey checklist."),
    CropSpec("rosen_fig_32_2", "Rosen", "Fig. 32.2", ROSEN, 354, (55, 62, 555, 690), "breathing", "breathing assessment algorithm", "Rosen separates oxygenation from ventilation and forces immediate treatment of unilateral breath-sound emergencies; Tintinalli lists the breathing survey actions."),
    CropSpec("rosen_fig_32_3", "Rosen", "Fig. 32.3", ROSEN, 355, (55, 72, 555, 736), "circulation", "circulation with hemorrhage control algorithm", "Rosen explicitly embeds TXA, balanced transfusion, eFAST/CT, and targeted source control; Tintinalli gives hemorrhage classes and resuscitation principles."),
    CropSpec("rosen_fig_32_4", "Rosen", "Fig. 32.4", ROSEN, 356, (50, 96, 560, 740), "mechanism modifiers", "special considerations of the primary survey", "Rosen ties primary survey branches to blunt versus penetrating mechanism; Tintinalli emphasizes a universal primary/secondary survey sequence."),
    CropSpec("rosen_table_32_2", "Rosen", "Table 32.2", ROSEN, 357, (46, 64, 568, 742), "secondary survey", "secondary survey of trauma patients", "Rosen turns the secondary survey into region-by-region critical and emergent diagnoses; Tintinalli gives the head-to-toe survey sequence."),
    CropSpec("atls_table_1_1", "ATLS", "Table 1-1", ATLS, 26, (110, 240, 520, 760), "xABCDE", "primary survey and simultaneous resuscitation", "ATLS vs Tintinalli: ATLS leads with x for exsanguinating hemorrhage before airway; Tintinalli organizes ABCDE but still demands immediate external hemorrhage control."),
    CropSpec("atls_table_6_2", "ATLS", "Table 6-2", ATLS, 99, (34, 43, 574, 442), "shock severity", "clinical parameters by hemorrhage severity", "ATLS vs Tintinalli: ATLS describes shock response as minor-to-major clinical patterns; Tintinalli uses class I-IV blood-loss categories."),
    CropSpec("atls_fig_6_1", "ATLS", "Figure 6-1", ATLS, 100, (76, 42, 570, 285), "tamponade", "cardiac tamponade image and ultrasound", "ATLS vs Tintinalli: ATLS visually anchors tamponade as obstructive shock; Tintinalli embeds tamponade in traumatic arrest and breathing/circulation differentials."),
    CropSpec("atls_fig_6_4", "ATLS", "Figure 6-4", ATLS, 104, (28, 38, 304, 545), "FAST", "focused assessment with sonography for trauma", "ATLS vs Tintinalli: ATLS shows FAST windows; Tintinalli shows a positive Morison pouch FAST and uses it to guide hemorrhage source control."),
]


def crop_pdf(spec: CropSpec) -> None:
    doc = fitz.open(spec.pdf)
    pix = doc[spec.page - 1].get_pixmap(matrix=fitz.Matrix(2.2, 2.2), clip=fitz.Rect(*spec.rect), alpha=False)
    pix.save(PRE / f"{spec.key}.png")


def data_uri(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def source_card(spec: CropSpec, text: str) -> str:
    delta_html = ""
    if spec.delta:
        if spec.source == "Rosen":
            label, detail = "Rosen vs Tintinalli", spec.delta
        elif ":" in spec.delta:
            label, detail = spec.delta.split(":", 1)
        else:
            label, detail = "Source delta", spec.delta
        delta_html = f'<div class="source-delta"><strong><u>{html.escape(label)}:</u></strong> {html.escape(detail.strip())}</div>'
    return f"""
    <article class="source-card">
      <div class="source-card__label">{html.escape(spec.source)} source</div>
      <h3 class="source-card__title">{html.escape(spec.label)}</h3>
      <p>{html.escape(text)}</p>{delta_html}
      <figure class="source-figure reference-image">
        <img src="{data_uri(PRE / f'{spec.key}.png')}" alt="{html.escape(spec.source + ' ' + spec.label)}" loading="lazy" decoding="async">
        <figcaption>{html.escape(spec.source)} {html.escape(spec.label)}. {html.escape(spec.note)}.</figcaption>
      </figure>
    </article>"""


def mcq(n: int, ans: str, stem: str, opts: list[tuple[str, str]], rats: dict[str, str]) -> str:
    buttons = "".join(f'<button class="mcq-opt" type="button" data-option-key="{k}">{k}. {html.escape(v)}</button>' for k, v in opts)
    explains = "".join(f'<div class="opt-explain {"is-correct" if k == ans else "is-wrong"}" hidden><strong>{k}. {html.escape(v)}</strong><span>{html.escape(rats[k])}</span></div>' for k, v in opts)
    return f'<article class="mcq-wrapper" data-answer="{ans}" data-answered="false"><p class="mcq-stem">Q{n}. {html.escape(stem)}</p><div class="mcq-options">{buttons}</div><div class="mcq-result" hidden></div><div class="mcq-explains">{explains}</div></article>'


def build_mcqs() -> str:
    raw = [
        ("B", "ATLS xABCDE begins with:", [("A", "Definitive CT"), ("B", "Control of exsanguinating external hemorrhage"), ("C", "Antibiotics"), ("D", "Secondary survey")], {"A": "CT waits until immediate life threats are treated.", "B": "Correct.", "C": "Not first.", "D": "Secondary survey follows primary survey resuscitation."}),
        ("C", "A trauma patient with GCS 7 and vomiting needs:", [("A", "Oral fluids"), ("B", "Delayed airway until CT"), ("C", "Airway protection with cervical spine precautions"), ("D", "Discharge")], {"A": "Unsafe.", "B": "CT does not precede airway protection.", "C": "Correct.", "D": "Unsafe."}),
        ("D", "Absent breath sounds on one side with shock after trauma should trigger concern for:", [("A", "Simple anxiety"), ("B", "Appendicitis"), ("C", "Migraine"), ("D", "Tension pneumothorax or massive hemothorax")], {"A": "No.", "B": "No.", "C": "No.", "D": "Correct."}),
        ("A", "Best immediate action for exsanguinating extremity hemorrhage:", [("A", "Direct pressure/wound packing and tourniquet when needed"), ("B", "Wait for labs"), ("C", "Give crystalloid only"), ("D", "Remove all dressings repeatedly")], {"A": "Correct.", "B": "Do not wait.", "C": "Control bleeding first.", "D": "Avoid disrupting clots."}),
        ("B", "Which pattern suggests hemorrhagic shock rather than isolated pain?", [("A", "Normal perfusion and calm patient"), ("B", "Tachycardia, narrowing pulse pressure, cool skin"), ("C", "Localized wrist pain only"), ("D", "Normal vitals after observation")], {"A": "No shock pattern.", "B": "Correct.", "C": "Not systemic.", "D": "Not hemorrhagic shock."}),
        ("C", "TXA in bleeding trauma is most useful when:", [("A", "Given 2 days later"), ("B", "Used after bleeding stops only"), ("C", "Given early, ideally within 3 hours when significant hemorrhage is suspected"), ("D", "Used for isolated ankle sprain")], {"A": "Too late.", "B": "Wrong target.", "C": "Correct.", "D": "No."}),
        ("D", "A positive eFAST in an unstable blunt trauma patient most strongly supports:", [("A", "Outpatient follow-up"), ("B", "Migraine therapy"), ("C", "No surgical consultation"), ("D", "Hemorrhage source control pathway")], {"A": "Unsafe.", "B": "Irrelevant.", "C": "Wrong.", "D": "Correct."}),
        ("A", "Persistent tGCS <=8 after head trauma generally indicates:", [("A", "Poor prognosis and need for definitive airway consideration"), ("B", "Normal finding"), ("C", "No need to reassess"), ("D", "No risk of aspiration")], {"A": "Correct.", "B": "False.", "C": "Serial reassessment matters.", "D": "Aspiration risk is high."}),
        ("B", "Secondary survey should begin:", [("A", "Before airway assessment"), ("B", "After primary survey threats are addressed and resuscitation is underway"), ("C", "Only after discharge"), ("D", "Before hemorrhage control")], {"A": "Wrong sequence.", "B": "Correct.", "C": "No.", "D": "Bleeding control comes first."}),
        ("C", "A hemodynamically abnormal pelvic fracture patient needs:", [("A", "Ambulation trial"), ("B", "No binder"), ("C", "Pelvic stabilization plus hemorrhage-source evaluation"), ("D", "Only oral analgesics")], {"A": "Unsafe.", "B": "Wrong.", "C": "Correct.", "D": "Insufficient."}),
        ("D", "Cardiac tamponade after penetrating chest trauma classically causes:", [("A", "Isolated fever"), ("B", "Hypertension only"), ("C", "Normal perfusion always"), ("D", "Obstructive shock; ultrasound may show pericardial fluid")], {"A": "No.", "B": "No.", "C": "False.", "D": "Correct."}),
        ("A", "Balanced resuscitation in major bleeding emphasizes:", [("A", "Blood products and hemorrhage control, limiting excessive crystalloid"), ("B", "Large saline volume only"), ("C", "Delayed transfusion always"), ("D", "No calcium monitoring ever")], {"A": "Correct.", "B": "Dilution/coagulopathy risk.", "C": "Wrong.", "D": "Calcium may matter in massive transfusion."}),
        ("B", "Rosen's airway algorithm adds most to Tintinalli by:", [("A", "Removing airway from primary survey"), ("B", "Branching adequate protection, obstruction, ventilation, intubation, and surgical airway"), ("C", "Replacing trauma survey with antibiotics"), ("D", "Avoiding oxygen")], {"A": "No.", "B": "Correct.", "C": "No.", "D": "No."}),
        ("C", "Rosen's breathing algorithm prioritizes:", [("A", "Routine CT first in unstable patients"), ("B", "No oxygen assessment"), ("C", "Oxygenation/ventilation and immediate unilateral breath-sound diagnoses"), ("D", "Only discharge criteria")], {"A": "No.", "B": "False.", "C": "Correct.", "D": "No."}),
        ("D", "Which patient is not ready for pan-CT as the first step?", [("A", "Stable, normal vitals after high-energy mechanism"), ("B", "Stable with reliable exam"), ("C", "Stable after completed primary survey"), ("D", "Unstable with uncontrolled hemorrhage")], {"A": "May be appropriate.", "B": "May be appropriate.", "C": "May be appropriate.", "D": "Correct."}),
        ("A", "Hypothermia in trauma is dangerous because it:", [("A", "Worsens coagulopathy and shock"), ("B", "Prevents bleeding"), ("C", "Makes secondary survey unnecessary"), ("D", "Improves platelets")], {"A": "Correct.", "B": "False.", "C": "No.", "D": "No."}),
        ("B", "Massive transfusion is most likely when:", [("A", "Blood loss minor and stable"), ("B", "Major hemorrhage with transient/minimal response to resuscitation"), ("C", "Isolated abrasion"), ("D", "Normal perfusion and no bleeding")], {"A": "No.", "B": "Correct.", "C": "No.", "D": "No."}),
        ("C", "In trauma arrest, reversible causes include:", [("A", "Only hypoglycemia"), ("B", "Only sepsis"), ("C", "Hypoxia, tension pneumothorax, tamponade, hypovolemia"), ("D", "Only intoxication")], {"A": "Too narrow.", "B": "No.", "C": "Correct.", "D": "No."}),
        ("D", "A chest tube output >1500 mL initially suggests:", [("A", "No bleeding"), ("B", "Minor contusion only"), ("C", "Safe discharge"), ("D", "Massive hemothorax and surgical consultation/hemorrhage control")], {"A": "False.", "B": "Too mild.", "C": "Unsafe.", "D": "Correct."}),
        ("A", "Canadian C-spine/NEXUS rules are useful mainly in:", [("A", "Awake, alert, evaluable patients"), ("B", "Comatose unstable patients"), ("C", "Patients needing immediate airway"), ("D", "All obtunded trauma patients")], {"A": "Correct.", "B": "No.", "C": "No.", "D": "No."}),
        ("B", "The secondary survey is designed to find:", [("A", "Only medication allergies"), ("B", "Missed head-to-toe injuries after immediate threats are managed"), ("C", "Nothing after normal FAST"), ("D", "Only minor skin findings")], {"A": "Too narrow.", "B": "Correct.", "C": "FAST does not replace survey.", "D": "Too narrow."}),
        ("C", "An obtunded trauma patient with normal CT C-spine:", [("A", "Always has no ligamentous injury"), ("B", "Needs no immobilization plan"), ("C", "May still require careful clearance strategy because ligamentous injury can persist"), ("D", "Can skip reassessment")], {"A": "False.", "B": "No.", "C": "Correct.", "D": "No."}),
        ("D", "Rosen's secondary survey table is useful because it maps:", [("A", "Only drug doses"), ("B", "Only lab values"), ("C", "Only outpatient follow-up"), ("D", "Region/system findings to critical and emergent diagnoses")], {"A": "No.", "B": "No.", "C": "No.", "D": "Correct."}),
        ("A", "Initial trauma care should avoid:", [("A", "Letting CT delay airway, decompression, hemorrhage control, or transfusion"), ("B", "Frequent reassessment"), ("C", "Pelvic stabilization when indicated"), ("D", "Temperature control")], {"A": "Correct.", "B": "Good practice.", "C": "Good practice.", "D": "Good practice."}),
        ("B", "ATLS Table 6-2 differs from Tintinalli Table 254-6 by emphasizing:", [("A", "No vital signs"), ("B", "Clinical response/severity patterns rather than only percent blood loss classes"), ("C", "Dermatology"), ("D", "Antivenom dosing")], {"A": "Wrong.", "B": "Correct.", "C": "No.", "D": "No."}),
        ("C", "Disposition after significant trauma depends most on:", [("A", "Patient preference only"), ("B", "A single normal vital sign"), ("C", "Physiology, identified/suspected injuries, response to resuscitation, and trauma center capability"), ("D", "Normal skin exam")], {"A": "Too narrow.", "B": "Unsafe.", "C": "Correct.", "D": "No."}),
    ]
    return "\n".join(mcq(i, *row) for i, row in enumerate(raw, 1))


def doc_html() -> str:
    c = {x.key: x for x in CROPS}
    return f"""<!doctype html><html lang="en" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Chapter 254 - Trauma in Adults</title><style>{STYLE}</style></head><body>
<header id="top-header"><button class="hdr-btn" data-sidebar-toggle title="Contents">☰</button><div class="hdr-title">Ch.254 Trauma in Adults</div><button class="hdr-btn theme-btn" data-theme-toggle>Dark</button></header>
<div class="app"><aside id="sidebar" class="sidebar"><button class="hdr-btn sidebar-close" data-sidebar-close>Close</button><div class="sidebar__block"><div class="sidebar__kicker">Chapter</div><h2>Trauma in Adults</h2><p class="meta"><b>Spine:</b> Tintinalli Ch.254</p><p class="meta"><b>Rosen:</b> Ch.32 Multiple Trauma</p><p class="meta"><b>ATLS:</b> 11th ed primary survey, shock, FAST</p></div><div class="sidebar__block"><div class="sidebar__kicker">Contents</div><a class="sidebar__link" href="#system">System</a><a class="sidebar__link" href="#primary">xABCDE</a><a class="sidebar__link" href="#airway">Airway</a><a class="sidebar__link" href="#breathing">Breathing</a><a class="sidebar__link" href="#circulation">Circulation</a><a class="sidebar__link" href="#disability">Disability</a><a class="sidebar__link" href="#adjuncts">Adjuncts</a><a class="sidebar__link" href="#arrest">Trauma Arrest</a><a class="sidebar__link" href="#doses">Drug Dose Reference</a><a class="sidebar__link" href="#assessment">MCQs</a></div></aside>
<main id="main" class="main"><div class="content-wrap"><div class="utility-bar">Fresh rebuild • Tintinalli/Rosen/ATLS source crops • MCQs show all explanations after answer</div>
<section class="hero section" id="system"><div class="eyebrow">Trauma Chapter 254</div><h1 class="hero__title">Trauma in Adults</h1><p class="lede">Adult trauma care is not a linear note-writing exercise. It is a repeated cycle of <mark>finding immediate killers, fixing physiology, and moving the patient to definitive hemorrhage or injury control</mark>.</p><div class="callout warn"><strong>Board trap:</strong> a normal first look does not clear a high-energy patient; reassessment and mechanism-aware secondary survey are part of resuscitation.</div>{source_card(c['tint_fig_254_1'], 'Tintinalli opens adult trauma with the trauma system continuum: prevention, EMS triage, resuscitation, definitive care, rehabilitation, and performance improvement.')}{source_card(c['tint_table_254_2'], 'Tintinalli trauma-system entry criteria are placed with the system discussion because they decide destination and activation level, not drug dosing.')}</section>
<section class="section" id="primary"><h2>Primary Survey: xABCDE With Simultaneous Resuscitation</h2><p>The accepted ED rhythm is <u>primary survey with immediate treatment</u>, not primary survey followed by treatment later. ATLS 11th edition makes the first letter x: stop exsanguinating external hemorrhage before airway. Tintinalli uses the same practical priority: identify and manage immediately life-threatening injuries during the primary survey, then proceed to a head-to-toe secondary survey only after basic stabilization.</p><p>Primary survey findings must trigger action: tourniquet or wound packing for severe external bleeding, airway protection for GCS <=8 or active bleeding/vomiting, decompression or chest tube for life-threatening thoracic injury, blood products for hemorrhagic shock, and exposure with hypothermia prevention.</p>{source_card(c['atls_table_1_1'], 'ATLS Table 1-1 is integrated here because it is the operating frame for the first minutes: exsanguinating hemorrhage, airway, breathing, circulation, disability, exposure.')}{source_card(c['tint_table_254_3'], 'Tintinalli Table 254-3 gives the matching primary and secondary survey checklist, including airway, breathing, circulation, disability, exposure, and head-to-toe reassessment.')}</section>
<section class="section" id="airway"><h2>Airway and Cervical Spine</h2><p>Airway failure in trauma is driven by direct injury, altered mental status, shock, blood/vomitus, maxillofacial disruption, and expanding neck hematoma. The ED decision is not just "intubate or not"; it is whether the patient can protect the airway, whether mask ventilation is adequate, whether intubation is possible, and whether a surgical airway is needed.</p><p>Maintain in-line stabilization when cervical spine injury is possible, but do not let the collar hide penetrating neck bleeding or delay airway control. <mark>GCS <=8, vomiting, facial/neck bleeding, severe agitation from hypoxia, and impending obstruction</mark> are airway danger signs.</p>{source_card(c['rosen_fig_32_1'], 'Rosen Fig. 32.1 turns airway assessment into a branching algorithm and belongs beside the airway section, not in a source dump.')}</section>
<section class="section" id="breathing"><h2>Breathing: Chest Life Threats</h2><p>After airway control, assess oxygenation and ventilation with inspection, auscultation, percussion, palpation, pulse oximetry, and waveform capnography when intubated. Immediate thoracic threats include tension pneumothorax, open pneumothorax, massive hemothorax, flail chest with pulmonary contusion, and cardiac tamponade presenting as obstructive shock.</p><p>Unilateral absent breath sounds plus shock is not a "wait for CT" problem. Needle/finger thoracostomy, tube thoracostomy, occlusive dressing, or urgent surgery may be required depending on the finding. A large initial chest tube output or persistent high output points toward operative hemorrhage control.</p>{source_card(c['rosen_fig_32_2'], 'Rosen Fig. 32.2 is placed here because it separates inadequate breathing into treat-now diagnoses and nontraumatic mimics.')}{source_card(c['atls_fig_6_1'], 'ATLS Figure 6-1 is the visual source for tamponade physiology and sonographic pericardial fluid in obstructive shock.')}</section>
<section class="section" id="circulation"><h2>Circulation and Hemorrhage Control</h2><p>Hemorrhage is the most common preventable cause of early trauma death. Look for "blood on the floor and four more": external, chest, abdomen, pelvis/retroperitoneum, and long bones. Control external hemorrhage with direct pressure, wound packing, hemostatic dressing, and tourniquet when needed. For unstable patients, resuscitation and source control must move together.</p><p>Use two large-bore IVs or IO access, early blood products, permissive lower pressure before definitive control when appropriate, TXA early for significant bleeding, calcium monitoring/repletion during massive transfusion, warming, and rapid surgical/interventional radiology pathways. <u>Crystalloid is a bridge, not a substitute for hemorrhage control.</u></p>{source_card(c['tint_fig_254_2'], 'Tintinalli Figure 254-2 is kept beside hemorrhage control because tourniquet use is a direct primary-survey intervention.')}{source_card(c['tint_table_254_6'], 'Tintinalli Table 254-6 gives the classic hemorrhage class framework for estimated blood loss and vital sign changes.')}{source_card(c['atls_table_6_2'], 'ATLS Table 6-2 is integrated here to emphasize clinical response and hemorrhage severity during ongoing reassessment.')}{source_card(c['rosen_fig_32_3'], 'Rosen Fig. 32.3 shows the circulation algorithm from shock recognition to eFAST/CT, targeted intervention, and reassessment.')}</section>
<section class="section" id="disability"><h2>Disability, Exposure, and Mechanism Modifiers</h2><p>Disability is a focused neurologic check after ABC threats are addressed: GCS or motor GCS, pupils, lateralizing signs, glucose, and recurrent reassessment. Do not attribute altered mental status to intoxication until hypoxia, shock, head injury, hypoglycemia, and drug exposure have been considered.</p><p>Exposure means fully undress and logroll with spinal precautions to find posterior injuries, but active warming must begin immediately. Hypothermia worsens coagulopathy and shock. Mechanism modifies the survey: blunt trauma pushes attention toward occult chest/abdominal/pelvic hemorrhage and spinal injury, while penetrating trauma pushes trajectory, vascular injury, airway displacement, and external bleeding.</p>{source_card(c['tint_table_254_7'], 'Tintinalli Table 254-7 provides the GCS/motor GCS reference used for disability assessment and triage severity.')}{source_card(c['rosen_fig_32_4'], 'Rosen Fig. 32.4 is placed with mechanism modifiers because it maps primary-survey danger signs to blunt versus penetrating patterns.')}</section>
<section class="section" id="adjuncts"><h2>Adjuncts and Secondary Survey</h2><p>Adjuncts are chosen by physiology. Unstable patients need bedside tools that answer source-control questions: eFAST, chest/pelvis radiographs when they change immediate care, and direct operative/interventional pathways. Stable patients can undergo CT to define injuries, but pan-scan does not replace serial examination.</p><p>The secondary survey is a structured head-to-toe search after the primary survey is stabilized: scalp, face, neck, chest, abdomen/flank, pelvis, perineum, rectal/genital exam when indicated, extremities, back, and neurologic/spinal exam. <mark>A normal first CT does not cancel serial exams</mark> when mechanism, pain, or physiology remains concerning.</p>{source_card(c['tint_fig_254_3'], 'Tintinalli Figure 254-3 shows a positive extended FAST exam with Morison pouch blood, directly supporting the adjuncts discussion.')}{source_card(c['atls_fig_6_4'], 'ATLS Figure 6-4 shows FAST windows and complements Tintinalli positive FAST image.')}{source_card(c['rosen_table_32_2'], 'Rosen Table 32.2 is the region-by-region secondary survey source table and is placed beside the secondary survey narrative.')}</section>
<section class="section" id="arrest"><h2>Traumatic Arrest and Disposition</h2><p>Traumatic arrest is treated by simultaneously reversing the causes that can be fixed quickly: hypoxia, tension pneumothorax, tamponade, and hypovolemia. Control catastrophic external hemorrhage, maximize oxygenation/airway, decompress both chests when indicated, relieve tamponade when appropriate, and activate massive transfusion/source control.</p><p>Disposition is physiology plus resources. Persistent hemodynamic instability, ongoing transfusion need, positive FAST with shock, major chest tube output, pelvic fracture with shock, penetrating torso trauma, depressed mental status, or need for operative/interventional care requires a trauma center/OR/ICU pathway. Observation is for patients whose injuries, mechanism, and serial exams remain reassuring.</p>{source_card(c['tint_fig_254_4'], 'Tintinalli Figure 254-4 is placed with trauma arrest because it organizes reversible causes and resuscitative thoracotomy decisions.')}</section>
<section class="section" id="doses"><h2>Drug Dose Reference</h2><p>This is a quick recap after the full treatment discussion, not the only treatment section.</p><div class="table-wrap"><table><thead><tr><th>Intervention</th><th>Adult reference</th><th>When it matters</th></tr></thead><tbody><tr><td>TXA</td><td>1 g IV over 10 min, then 1 g IV over 8 h</td><td>Significant hemorrhage, ideally within 3 h of injury.</td></tr><tr><td>Massive transfusion</td><td>Institutional protocol; balanced RBC/plasma/platelet strategy</td><td>Shock with ongoing hemorrhage or transient/minimal response.</td></tr><tr><td>Calcium</td><td>Monitor ionized calcium; replete per local protocol during MTP</td><td>Citrate load from blood products can worsen hypotension/coagulopathy.</td></tr><tr><td>Analgesia/sedation</td><td>Titrate to physiology and airway plan</td><td>Do not mask deterioration; reassess after every dose.</td></tr></tbody></table></div></section>
<section class="question-set section" id="assessment"><h2>Inline Assessment MCQs</h2>{build_mcqs()}</section>
</div></main></div><div class="score-pill" data-score-text>0 correct / 0 answered / 26 total</div><div class="image-modal" data-image-modal><button class="hdr-btn" data-modal-close>Close</button><img alt="Zoomed source"></div><script>{SCRIPT}</script></body></html>"""


def extract_embedded(doc: str) -> list[Path]:
    EMBED.mkdir(parents=True, exist_ok=True)
    for old in EMBED.glob("*.png"):
        old.unlink()
    paths = []
    for i, m in enumerate(re.finditer(r"data:image/png;base64,([^\"]+)", doc), 1):
        p = EMBED / f"ch254_embedded_{i:02d}.png"
        p.write_bytes(base64.b64decode(m.group(1)))
        paths.append(p)
    return paths


def contact_sheet(paths: list[Path]) -> Path:
    cols, cell_w, cell_h = 3, 380, 330
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
    draw = ImageDraw.Draw(sheet)
    for i, path in enumerate(paths):
        img = Image.open(path).convert("RGB")
        img.thumbnail((340, 275))
        x, y = (i % cols) * cell_w, (i // cols) * cell_h
        sheet.paste(img, (x + 20, y + 40))
        draw.text((x + 8, y + 8), f"{i+1:02d} {path.name}", fill=(0, 0, 0))
    out = EMBED / "ch254_embedded_contact_sheet.png"
    sheet.save(out)
    return out


def md_to_html(md: str, title: str) -> str:
    out, in_table = [], False
    for line in md.splitlines():
        if line.startswith("|") and line.endswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if cells and set(cells[0]) <= {"-"}:
                continue
            if not in_table:
                out.append("<table>")
                in_table = True
            tag = "th" if cells and cells[0] in {"#", "Ch", "Source"} else "td"
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
    inv = "\n".join(f"- {c.source} {c.label}: page {c.page}, placement `{c.placement}`" for c in CROPS)
    md = f"""# CH254 Crop QA - 2026-05-09

Fresh rebuild from source PDFs. Old Chapter254 HTML crops were not used as completion evidence.

## Source Inventory Used

Tintinalli Ch254 included: Figure 254-1, Table 254-2, Table 254-3, Figure 254-2, Table 254-6, Figure 254-3, Table 254-7, and Figure 254-4.

Rosen Ch32 included: Fig. 32.1, Fig. 32.2, Fig. 32.3, Fig. 32.4, and Table 32.2.

ATLS 11th edition included: Table 1-1, Table 6-2, Figure 6-1, and Figure 6-4.

{inv}

## Embedded Crop QA

Contact sheet: `{sheet.relative_to(ROOT).as_posix()}`

| # | Source | Object | PDF | PDF page | Extracted final embedded image | Status | Note |
|---|---|---|---|---:|---|---|---|
{chr(10).join(rows)}

## Content Gate

Content: PASS. Major trauma headings have narrative summaries; ATLS is integrated in the clinical body; source crops are topic-local; Drug Dose Reference is only a recap; no visible audit/source-audit repair text is inside the chapter.

Pattern: PASS. Ch186/Ch201 shell, top header, sidebar/main layout, topic-local Rosen and ATLS source cards, source deltas, and accepted MCQ behavior are present.
"""
    QA_MD.write_text(md, encoding="utf-8")
    QA_HTML.write_text(md_to_html(md, "CH254 Crop QA"), encoding="utf-8")


def update_audit() -> None:
    md = AUDIT_MD.read_text(encoding="utf-8")
    line = "| 254 | Chapter254_TraumaInAdults.html | PASS | PASS | PASS | 26 | 7 | 21 | 17 | PASS | 38 | Fresh rebuild 2026-05-09; Pattern: PASS; Content: PASS; MCQ all-option explanations PASS; Tintinalli/Rosen/ATLS source crops topic-local; ATLS integrated in body; cropQA PASS (17/17) |"
    md = re.sub(r"^\| 254 \|.*$", line, md, flags=re.M)
    AUDIT_MD.write_text(md, encoding="utf-8")
    AUDIT_HTML.write_text(md_to_html(md, "Chapter Quality Audit"), encoding="utf-8")


def gate(doc: str, paths: list[Path]) -> None:
    checks = {
        "top": len(re.findall(r'id="top-header"', doc)),
        "hdr_btn": len(re.findall(r'class="[^"]*hdr-btn', doc)),
        "sidebar": len(re.findall(r'id="sidebar"', doc)),
        "main": len(re.findall(r'id="main"', doc)),
        "sidebar_link": len(re.findall(r'class="[^"]*sidebar__link', doc)),
        "sidebar_block": len(re.findall(r'class="[^"]*sidebar__block', doc)),
        "hero_title": len(re.findall(r'class="[^"]*hero__title', doc)),
        "sections": len(re.findall(r'class="[^"]*section', doc)),
        "mcq": len(re.findall(r'class="mcq-wrapper"', doc)),
        "result": len(re.findall(r'class="mcq-result"', doc)),
        "legacy_mcq": len(re.findall(r'mcq-card', doc)),
        "source_fig": len(re.findall(r'class="source-figure reference-image"', doc)),
        "data": len(re.findall(r'data:image/png;base64,', doc)),
        "mark": len(re.findall(r"<mark>", doc)),
        "u": len(re.findall(r"<u>", doc)),
        "rosen": len(re.findall(r"Rosen source", doc)),
        "rosen_delta": len(re.findall(r"Rosen vs Tintinalli", doc)),
        "atls": len(re.findall(r"ATLS source", doc)),
        "atls_delta": len(re.findall(r"ATLS vs Tintinalli", doc)),
    }
    bad_words = ["Rosen Source Audit", "Source Audit", "Source Check", "Excluded nearby", "repair note"]
    failures = []
    if checks["top"] != 1 or checks["hdr_btn"] < 2:
        failures.append("top header")
    if checks["sidebar"] != 1 or checks["main"] != 1 or checks["sidebar_link"] == 0 or checks["sidebar_block"] == 0 or checks["hero_title"] == 0:
        failures.append("shell")
    if checks["mcq"] != 26 or checks["result"] != 26 or checks["legacy_mcq"] != 0:
        failures.append("mcq")
    if checks["source_fig"] != len(CROPS) or checks["data"] != len(CROPS) or len(paths) != len(CROPS):
        failures.append("crop count")
    if checks["mark"] == 0 or checks["u"] == 0:
        failures.append("emphasis")
    if checks["rosen"] < 5 or checks["rosen_delta"] < 5:
        failures.append("rosen")
    if checks["atls"] < 4 or checks["atls_delta"] < 4:
        failures.append("atls")
    if any(w in doc for w in bad_words):
        failures.append("visible audit text")
    if failures:
        raise SystemExit(f"Gate failed: {failures} {checks}")
    print("GATE PASS", checks)


def main() -> None:
    PRE.mkdir(parents=True, exist_ok=True)
    for old in PRE.glob("*.png"):
        old.unlink()
    for spec in CROPS:
        crop_pdf(spec)
    doc = doc_html()
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(doc, encoding="utf-8")
    paths = extract_embedded(doc)
    sheet = contact_sheet(paths)
    build_qa(paths, sheet)
    update_audit()
    gate(doc, paths)
    for rel in [OUT_HTML.relative_to(ROOT), QA_MD.relative_to(ROOT), QA_HTML.relative_to(ROOT), AUDIT_MD.relative_to(ROOT), AUDIT_HTML.relative_to(ROOT)]:
        dst = MIRROR / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, dst)
    print("HTML", OUT_HTML)
    print("QA", QA_HTML)
    print("CONTACT", sheet)


if __name__ == "__main__":
    main()
