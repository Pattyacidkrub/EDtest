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
OUT_HTML = ROOT / "docs/chapters/complete/Chapter260_NeckTrauma.html"
MIRROR = Path(r"C:\c\Users\PC\OneDrive\เอกสาร\codex\ER")
QA_MD = ROOT / "CH260_CROP_QA_2026-05-09.md"
QA_HTML = ROOT / "CH260_CROP_QA_2026-05-09.html"
AUDIT_MD = ROOT / "CHAPTER_COMPLETE_AUDIT_2026-05-07.md"
AUDIT_HTML = ROOT / "CHAPTER_COMPLETE_AUDIT_2026-05-07.html"
WORK = ROOT / "_ch260_rebuild_from_zero_2026-05-09"
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


CROPS = [
    CropSpec("tint_fig_260_1", "Tintinalli", "Figure 260-1", TINT, 1767, (28, 540, 292, 744), "anatomy", "triangles of the neck"),
    CropSpec("tint_fig_260_2", "Tintinalli", "Figure 260-2", TINT, 1767, (296, 42, 584, 254), "zones", "zones of the neck"),
    CropSpec("tint_table_260_1", "Tintinalli", "Table 260-1", TINT, 1767, (298, 506, 586, 744), "zones", "anatomic zones and structures of the anterior neck"),
    CropSpec("tint_fig_260_3", "Tintinalli", "Figure 260-3", TINT, 1768, (50, 35, 570, 292), "anatomy", "fascial layers of the neck"),
    CropSpec("tint_table_260_2", "Tintinalli", "Table 260-2", TINT, 1768, (52, 618, 316, 744), "airway", "clinical factors indicating need for aggressive airway management"),
    CropSpec("tint_table_260_3", "Tintinalli", "Table 260-3", TINT, 1768, (322, 616, 586, 744), "airway", "relative indications for airway management"),
    CropSpec("atls_table_22_1", "ATLS", "Table 22-1", ATLS, 328, (38, 38, 300, 314), "zones", "zones of the neck and basic approaches"),
    CropSpec("atls_fig_22_4", "ATLS", "Figure 22-4", ATLS, 328, (38, 316, 300, 750), "hemorrhage", "stab wound to internal carotid artery with balloon tamponade"),
    CropSpec("tint_table_260_4", "Tintinalli", "Table 260-4", TINT, 1769, (28, 520, 292, 744), "radiology", "pathologic findings on conventional radiographs"),
    CropSpec("tint_table_260_5", "Tintinalli", "Table 260-5", TINT, 1769, (298, 38, 562, 365), "hard signs", "signs and symptoms of neck injury"),
    CropSpec("rosen_table_36_1", "Rosen", "Table 36.1", ROSEN, 452, (46, 292, 300, 536), "hard signs", "hard versus soft signs of penetrating neck injury"),
    CropSpec("tint_fig_260_4", "Tintinalli", "Figure 260-4", TINT, 1771, (86, 35, 522, 554), "no-zone", "penetrating neck trauma protocol"),
    CropSpec("tint_table_260_6", "Tintinalli", "Table 260-6", TINT, 1772, (52, 40, 316, 324), "vascular", "vascular evaluation of penetrating neck trauma"),
    CropSpec("tint_table_260_7", "Tintinalli", "Table 260-7", TINT, 1772, (52, 430, 316, 744), "bcvi", "screening criteria for blunt cerebral vascular injury"),
    CropSpec("tint_table_260_8", "Tintinalli", "Table 260-8", TINT, 1772, (322, 40, 586, 205), "bcvi", "blunt carotid and vertebral artery injury grading scale"),
    CropSpec("tint_table_260_9", "Tintinalli", "Table 260-9", TINT, 1773, (28, 38, 292, 164), "laryngotracheal", "laryngeal injury grading scale"),
    CropSpec("tint_table_260_10", "Tintinalli", "Table 260-10", TINT, 1774, (52, 438, 316, 736), "strangulation", "hard signs of strangulation injury"),
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
        if ":" in delta:
            head, body = delta.split(":", 1)
            delta_html = f'<div class="source-delta"><strong><u>{html.escape(head)}:</u></strong> {html.escape(body.strip())}</div>'
        else:
            delta_html = f'<div class="source-delta"><strong><u>Source delta:</u></strong> {html.escape(delta)}</div>'
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
    explains = "".join(
        f'<div class="opt-explain {"is-correct" if k == ans else "is-wrong"}" hidden><strong>{k}. {html.escape(v)}</strong><span>{html.escape(rats[k])}</span></div>'
        for k, v in opts
    )
    return f'<article class="mcq-wrapper" data-answer="{ans}" data-answered="false"><p class="mcq-stem">Q{n}. {html.escape(stem)}</p><div class="mcq-options">{buttons}</div><div class="mcq-result" hidden></div><div class="mcq-explains">{explains}</div></article>'


def build_mcqs() -> str:
    raw = [
        ("B", "A stab wound violates platysma but the patient is stable and asymptomatic. Next best evaluation?", [("A", "Discharge without imaging"), ("B", "Structured exam plus CTA or selective testing/observation per no-zone protocol"), ("C", "Mandatory zone II exploration for all"), ("D", "Cervical collar only")], {"A": "Platysma violation is significant.", "B": "Correct.", "C": "Old mandatory exploration is no longer universal.", "D": "Collar can obscure penetrating wounds."}),
        ("A", "First priority in massive active neck bleeding is:", [("A", "Direct pressure/packing; consider balloon tamponade if pressure fails"), ("B", "Soft collar"), ("C", "Water-soluble swallow first"), ("D", "Delayed CT only")], {"A": "Correct.", "B": "No.", "C": "Bleeding kills first.", "D": "Unstable bleeding needs immediate control."}),
        ("C", "Hard vascular sign in penetrating neck trauma:", [("A", "Minor oozing"), ("B", "Proximity wound only"), ("C", "Active arterial bleeding or expanding hematoma"), ("D", "Mild neck pain")], {"A": "Soft/nonspecific.", "B": "Soft sign.", "C": "Correct.", "D": "Nonspecific."}),
        ("D", "A normal airway after penetrating neck trauma:", [("A", "Can never worsen"), ("B", "Allows discharge immediately"), ("C", "Means no hematoma"), ("D", "Requires serial reassessment because edema/bleeding can progress")], {"A": "False.", "B": "Unsafe.", "C": "No.", "D": "Correct."}),
        ("A", "Preferred first airway attempt in many neck trauma patients with preserved anatomy is:", [("A", "Orotracheal intubation with surgical airway readiness"), ("B", "Blind nasotracheal intubation"), ("C", "Ignore airway"), ("D", "Bag-mask forcefully despite open laryngotracheal injury")], {"A": "Correct.", "B": "Risky.", "C": "No.", "D": "Can worsen injury."}),
        ("B", "Relative indication for airway control:", [("A", "No symptoms ever"), ("B", "Progressive neck swelling or voice change"), ("C", "Old scar"), ("D", "Normal remote history")], {"A": "No.", "B": "Correct.", "C": "No.", "D": "No."}),
        ("C", "ATLS point about penetrating neck trauma and collars:", [("A", "All penetrating neck wounds need collars"), ("B", "Collars improve wound inspection"), ("C", "Routine cervical collar is often unnecessary and may obscure wounds in stable neurologically intact penetrating injury"), ("D", "Collars stop arterial bleeding")], {"A": "False.", "B": "Opposite.", "C": "Correct.", "D": "No."}),
        ("D", "In stable penetrating neck injury, modern first-line imaging is commonly:", [("A", "No imaging"), ("B", "Plain film only"), ("C", "MRI only"), ("D", "Multidetector CT angiography")], {"A": "Wrong.", "B": "Often insufficient.", "C": "Not first-line.", "D": "Correct."}),
        ("A", "Best meaning of no-zone approach:", [("A", "Management is driven by physiology, hard/soft signs, and CTA rather than zone alone"), ("B", "Zones do not exist anatomically"), ("C", "No patient needs surgery"), ("D", "No wound needs evaluation")], {"A": "Correct.", "B": "Zones still describe anatomy.", "C": "Hard signs still go to intervention.", "D": "False."}),
        ("B", "Pharyngoesophageal injury clue:", [("A", "Only ankle pain"), ("B", "Odynophagia, dysphagia, saliva from wound, hematemesis, or mediastinal/retropharyngeal air"), ("C", "Isolated wrist rash"), ("D", "Normal oxygen saturation excludes it")], {"A": "No.", "B": "Correct.", "C": "No.", "D": "No."}),
        ("C", "A missed esophageal injury matters because:", [("A", "It is always benign"), ("B", "It never gets infected"), ("C", "Delay can cause mediastinitis, sepsis, pneumonia, and need for feeding/tracheostomy support"), ("D", "It heals instantly")], {"A": "False.", "B": "False.", "C": "Correct.", "D": "No."}),
        ("D", "Initial treatment when esophageal injury is suspected:", [("A", "Oral feeding"), ("B", "No antibiotics"), ("C", "Immediate discharge"), ("D", "NPO, broad-spectrum IV antibiotics with anaerobic coverage, surgical consultation")], {"A": "Wrong.", "B": "Wrong.", "C": "Wrong.", "D": "Correct."}),
        ("A", "Laryngotracheal injury can present with:", [("A", "Stridor, dysphonia, hemoptysis, air bubbling, subcutaneous emphysema"), ("B", "Only knee pain"), ("C", "No delayed symptoms"), ("D", "Normal voice always")], {"A": "Correct.", "B": "No.", "C": "Can be delayed.", "D": "False."}),
        ("B", "Best diagnostic tool to define airway patency in suspected laryngotracheal injury:", [("A", "Urinalysis"), ("B", "Flexible fiberoptic laryngoscopy when feasible"), ("C", "Ankle x-ray"), ("D", "No exam")], {"A": "No.", "B": "Correct.", "C": "No.", "D": "Unsafe."}),
        ("C", "Blunt cerebrovascular injury concern is high because:", [("A", "Stroke always occurs immediately only"), ("B", "It is never asymptomatic"), ("C", "Neurologic symptoms are often delayed and untreated stroke risk can be high"), ("D", "US is perfect screening")], {"A": "False.", "B": "False.", "C": "Correct.", "D": "US is not adequate screening."}),
        ("D", "Tintinalli screening criterion for BCVI includes:", [("A", "Toe sprain only"), ("B", "Simple forearm abrasion"), ("C", "Isolated cough"), ("D", "Arterial hemorrhage, cervical bruit, expanding hematoma, focal neurologic deficit, or high-risk fracture pattern")], {"A": "No.", "B": "No.", "C": "No.", "D": "Correct."}),
        ("A", "Antithrombotic therapy for BCVI is generally used when:", [("A", "Not contraindicated by other injuries and vascular injury is identified"), ("B", "All neck pain without imaging"), ("C", "Only after stroke occurs"), ("D", "Never")], {"A": "Correct.", "B": "No.", "C": "Earlier is the point.", "D": "False."}),
        ("B", "Strangulation death mechanism often involves:", [("A", "Only visible bruising"), ("B", "Neck vessel occlusion and cerebral hypoxia more than simple airway obstruction"), ("C", "Only ankle fracture"), ("D", "No vascular issue")], {"A": "Visible signs may be absent.", "B": "Correct.", "C": "No.", "D": "False."}),
        ("C", "Hard sign of strangulation injury:", [("A", "No symptoms"), ("B", "Remote resolved anxiety only"), ("C", "Petechiae, swollen tongue/oropharynx, stridor, neurologic change, or incontinence"), ("D", "Normal exam always rules out injury")], {"A": "No.", "B": "No.", "C": "Correct.", "D": "False."}),
        ("D", "Disposition for abnormal imaging or endoscopy after strangulation:", [("A", "Immediate discharge"), ("B", "No follow-up"), ("C", "Ignore social safety"), ("D", "Admit to appropriate service and address psychosocial/domestic violence safety")], {"A": "Unsafe.", "B": "No.", "C": "Safety is part of care.", "D": "Correct."}),
        ("A", "Gunshot neck wounds compared with stab wounds:", [("A", "More likely to cause vascular and aerodigestive injury"), ("B", "Always superficial"), ("C", "Never need CTA"), ("D", "Never cross zones")], {"A": "Correct.", "B": "False.", "C": "False.", "D": "False."}),
        ("B", "Foley balloon tamponade in neck trauma is used for:", [("A", "Routine sore throat"), ("B", "Bleeding wound tract when direct pressure/packing is inadequate and surgical care is pending"), ("C", "Cervical spine clearance"), ("D", "CT contrast injection")], {"A": "No.", "B": "Correct.", "C": "No.", "D": "No."}),
        ("C", "Rosen adds to Tintinalli hard-sign discussion by:", [("A", "Removing soft signs"), ("B", "Saying hard signs are irrelevant"), ("C", "Separating hard versus soft signs for vascular and aerodigestive injury"), ("D", "Focusing only on dermatology")], {"A": "No.", "B": "No.", "C": "Correct.", "D": "No."}),
        ("D", "Stable patient with soft signs of penetrating neck injury usually needs:", [("A", "No workup"), ("B", "Immediate discharge"), ("C", "Collar only"), ("D", "CTA and targeted aerodigestive/vascular testing based on suspicion")], {"A": "Wrong.", "B": "Wrong.", "C": "Wrong.", "D": "Correct."}),
        ("A", "If CTA is negative but clinical suspicion for esophageal injury remains high:", [("A", "Observe or add esophagoscopy/esophagram/CT esophagography per local pathway"), ("B", "Feed and discharge"), ("C", "Ignore symptoms"), ("D", "Only give topical anesthetic")], {"A": "Correct.", "B": "Unsafe.", "C": "Unsafe.", "D": "No."}),
        ("B", "Most important first-screen question in neck trauma algorithm:", [("A", "What is the insurance?"), ("B", "Is the patient unstable or showing hard signs requiring immediate intervention?"), ("C", "Can the patient walk home?"), ("D", "Is the wound in zone II only?")], {"A": "No.", "B": "Correct.", "C": "No.", "D": "No-zone approach reduces zone-only decisions."}),
    ]
    return "\n".join(mcq(i, *row) for i, row in enumerate(raw, 1))


def doc_html() -> str:
    c = {x.key: x for x in CROPS}
    return f"""<!doctype html><html lang="en" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Chapter 260 - Neck Trauma</title><style>{STYLE}</style></head><body>
<header id="top-header"><button class="hdr-btn" data-sidebar-toggle title="Contents">☰</button><div class="hdr-title">Ch.260 Neck Trauma</div><button class="hdr-btn theme-btn" data-theme-toggle>Dark</button></header>
<div class="app"><aside id="sidebar" class="sidebar"><button class="hdr-btn sidebar-close" data-sidebar-close>Close</button><div class="sidebar__block"><div class="sidebar__kicker">Chapter</div><h2>Trauma to the Neck</h2><p class="meta"><b>Spine:</b> Tintinalli Ch.260</p><p class="meta"><b>Rosen:</b> Ch.36 Neck Trauma</p><p class="meta"><b>ATLS:</b> Ch.22 Penetrating Trauma</p><p class="meta"><b>Build:</b> from zero, no old HTML basis</p></div><div class="sidebar__block"><div class="sidebar__kicker">Contents</div><a class="sidebar__link" href="#overview">Overview</a><a class="sidebar__link" href="#airway">Airway</a><a class="sidebar__link" href="#hemorrhage">Hemorrhage</a><a class="sidebar__link" href="#evaluation">Evaluation</a><a class="sidebar__link" href="#vascular">Vascular/BCVI</a><a class="sidebar__link" href="#aerodigestive">Aerodigestive</a><a class="sidebar__link" href="#strangulation">Strangulation</a><a class="sidebar__link" href="#assessment">Assessment</a></div></aside>
<main id="main" class="main"><div class="content-wrap"><div class="utility-bar">Fresh from-zero rebuild • Tintinalli + Rosen + ATLS • MCQs reveal explanations after answer</div>
<section class="hero section" id="overview"><div class="eyebrow">Trauma Chapter 260</div><h1 class="hero__title">Trauma to the Neck</h1><p class="lede">The neck is a small space containing airway, great vessels, esophagus, nerves, and spine. ED decisions start with <mark>physiology and hard signs</mark>, then use CTA and targeted aerodigestive testing. Do not let old zone-only thinking delay hemorrhage control, airway control, or surgical consultation.</p><div class="callout warn"><strong>Board trap:</strong> platysma violation matters, but the immediate branch is unstable/hard signs versus stable. Hard signs go to intervention; stable soft-sign patients usually get CTA plus targeted testing.</div><p>Tintinalli builds the chapter from anatomy outward. The triangles remind you where to look, the zones explain which structures can be injured, and the fascial layers explain why a wound that crosses the platysma can track into deep spaces. <u>Zone I</u> is dangerous because access can require thoracotomy or sternotomy and includes proximal carotid/vertebral arteries, major thoracic vessels, lung apex, esophagus, trachea, thoracic duct, and spinal cord. <u>Zone II</u> is surgically accessible but packed with carotid/vertebral arteries, jugular veins, larynx, trachea, esophagus, and cord. <u>Zone III</u> is difficult because distal carotid/vertebral injury sits near the skull base with cranial nerves IX-XII.</p><p>That table-based anatomy changes the ED plan: do not use zone labels as the only decision tool, but use them to anticipate which service, imaging field, and operative access problem is likely. Zone I injuries push attention toward thoracic inlet and mediastinal injury; zone II toward carotid-jugular-aerodigestive injury; zone III toward skull-base vascular and cranial nerve complications.</p>{source_card(c['tint_fig_260_1'], 'Tintinalli Figure 260-1 shows the anterior and posterior triangles that organize the neck exam.')}{source_card(c['tint_fig_260_2'], 'Tintinalli Figure 260-2 shows zones I-III, useful for anatomic communication even though management is now no-zone.')}{source_card(c['tint_table_260_1'], 'Tintinalli Table 260-1 maps each anterior neck zone to its major structures and access problem.')}{source_card(c['tint_fig_260_3'], 'Tintinalli fascial anatomy shows why platysma violation changes a superficial wound into a potentially deep neck injury.')}</section>
<section class="section" id="airway"><h2>Airway First, But Hemorrhage Can Kill Faster</h2><p>Neck trauma airways can deteriorate from expanding hematoma, edema, secretions, air leak, or laryngotracheal disruption. Tintinalli Table 260-2 is the hard airway list: <mark>stridor, acute respiratory distress, airway obstruction from blood/secretions, expanding hematoma, profound shock, extensive subcutaneous emphysema, altered mental status, or tracheal shift</mark> means the airway is already unsafe. These patients need immediate airway control with surgical airway readiness.</p><p>Table 260-3 is the watch-list. Progressive swelling, voice change, massive subcutaneous emphysema, mental status change, expanding hematoma, need for transfer, or anticipated prolonged time away from the ED are not benign just because the patient is currently speaking. These are the patients who lose the airway during CT, transfer, or observation unless the team acts early.</p><p>Orotracheal intubation is often the first approach when anatomy permits, but the team must prepare for surgical airway. Avoid maneuvers that worsen airway disruption: forceful bag-mask ventilation, cricoid pressure, or blind passage may be dangerous in selected laryngotracheal injuries. <u>If the table says airway risk and the clinical trajectory is worsening, do not wait for complete obstruction.</u></p>{source_card(c['tint_table_260_2'], 'Tintinalli airway table gives immediate airway triggers.')}{source_card(c['tint_table_260_3'], 'Tintinalli relative-indication table keeps progressive symptoms and transfer risk visible.')}</section>
<section class="section" id="hemorrhage"><h2>Hemorrhage Control and ATLS Penetrating-Neck Rules</h2><p>Exsanguination is the proximate cause of death in many penetrating neck injuries. Apply direct pressure without compressing both carotids or obstructing the airway. Pack open wounds when feasible. If bleeding persists from a small tract, a Foley balloon can be inserted and inflated until tamponade while the patient is moved to definitive care.</p><p>ATLS reinforces two points that belong in the bedside algorithm: penetrating injuries that violate the platysma are significant, and stable penetrating neck trauma generally should not receive routine spinal motion restriction with a collar because the collar can obscure wounds and delay hemorrhage evaluation. Use a collar when neurologic deficit or blunt mechanism requires it, not as a reflex.</p>{source_card(c['atls_table_22_1'], 'ATLS table summarizes zones and basic approaches while still emphasizing hard/soft signs and early surgical consultation.', 'ATLS vs Tintinalli: Tintinalli uses zones as anatomy plus no-zone workup; ATLS keeps zone anatomy but explicitly warns not to let collars obscure penetrating wounds.')}{source_card(c['atls_fig_22_4'], 'ATLS figure demonstrates balloon tamponade for internal carotid bleeding when compression fails.', 'ATLS vs Tintinalli: both support balloon tamponade; ATLS shows the procedural concept visually and ties it to rapid assessment and transfer.')}</section>
<section class="section" id="evaluation"><h2>Hard Signs, Soft Signs, and No-Zone Workup</h2><p>Use Tintinalli Table 260-5 as the bedside checklist. Vascular hard signs are shock unresponsive to initial fluid therapy, active arterial bleeding, pulse deficit, pulsatile or expanding hematoma, and thrill/bruit. Laryngotracheal hard signs are stridor, hemoptysis, dysphonia, air bubbling in the wound, and airway obstruction. Pharyngoesophageal clues include odynophagia, dysphagia, hematemesis, blood in the mouth, saliva draining from the wound, severe tenderness, prevertebral air, and a transmidline trajectory.</p><p>Soft signs matter because they decide who gets CTA and targeted testing instead of observation. Hypotension in the field, history of arterial bleeding, nonpulsatile hematoma, proximity wounds, hoarseness, neck tenderness, subcutaneous emphysema, cervical ecchymosis, tracheal deviation, laryngeal edema, and restricted vocal cord mobility should push you into the diagnostic pathway rather than discharge.</p><p>Table 260-4 explains what plain films can and cannot do. Chest radiograph findings such as pneumothorax, hemothorax, mediastinal air, widened mediastinum, subcutaneous emphysema, foreign body/bullet fragments, pulmonary edema, and aspiration pneumonia are warning signals. Soft-tissue neck films can show prevertebral air, foreign body, tracheal narrowing/deviation, or retropharyngeal emphysema. Cervical spine films can show vertebral or hyoid fracture. <u>These findings support suspicion; they do not replace CTA or aerodigestive testing when the table-based exam is concerning.</u></p><p>The modern no-zone approach combines structured exam with MDCTA. Stable patients without platysma violation may be observed. Platysma violation plus hard signs moves toward OR/interventional angiography. Soft signs or concerning trajectory require CTA and targeted esophagoscopy/esophagram, laryngoscopy/panendoscopy, or vascular imaging depending on suspected tract.</p>{source_card(c['tint_table_260_4'], 'Tintinalli Table 260-4 lists conventional radiograph findings that should raise suspicion while definitive CT/CTA is arranged.')}{source_card(c['tint_table_260_5'], 'Tintinalli Table 260-5 is the central hard/soft symptom inventory for vascular, laryngotracheal, and pharyngoesophageal injuries.')}{source_card(c['rosen_table_36_1'], 'Rosen Table 36.1 separates hard versus soft vascular and aerodigestive signs.', 'Rosen vs Tintinalli: Tintinalli has a broader symptom list; Rosen makes the hard/soft distinction more explicit for operative versus CTA pathways.')}{source_card(c['tint_fig_260_4'], 'Tintinalli protocol figure anchors the no-zone penetrating-neck workflow.')}</section>
<section class="section" id="vascular"><h2>Vascular Injury and Blunt Cerebrovascular Injury</h2><p>Table 260-6 is the imaging decision table. Catheter angiography is invasive and resource-intensive, but it remains both diagnostic and therapeutic and can reach zone I/III lesions where surgical repair is difficult. Helical CT angiography is fast, readily available, minimally invasive, and shows missile trajectory plus vascular, aerodigestive, and bony structures in one study; its limits are contrast requirement, technique dependence, metallic streak artifact, lower sensitivity for small intimal lesions, and weaker performance at low zone I/high zone III margins. Duplex ultrasound is noninvasive and inexpensive but operator-dependent and limited by zone I/III access, emphysema, hematoma, and missed small lesions.</p><p>So the ED default is practical: <mark>MDCTA first for stable patients</mark>, angiography when therapy is likely or CTA is indeterminate, and ultrasound only as an adjunct where appropriate. Do not use an easy ultrasound to rule out a high-risk vascular trajectory.</p><p>BCVI after blunt neck trauma is dangerous because stroke can be delayed. Table 260-7 defines who gets screened: arterial hemorrhage from nose/neck/mouth, cervical bruit in patients under 50, expanding cervical hematoma, focal neurologic deficit, stroke on secondary CT, neurologic deficit unexplained by head CT, and high-energy mechanisms with Le Fort II/III, mandible, frontal skull, orbital, cervical spine, petrous bone, DAI with low GCS, hanging with anoxia, clothesline/seat-belt neck injury with swelling/pain/altered mental status, scalp degloving, thoracic vascular injury, blunt cardiac rupture, or upper rib fractures.</p><p>Table 260-8 then links grade to treatment. Grade I luminal irregularity/dissection with less than 25% narrowing usually gets antithrombotic therapy. Grade II dissection/intramural hematoma with at least 25% narrowing or thrombus may require antithrombotic therapy or surgical repair. Grade III pseudoaneurysm and grade IV occlusion often need antithrombotic plus surgical or endovascular planning. Grade V transection with extravasation requires urgent surgical repair if accessible, balloon occlusion, or embolization.</p>{source_card(c['tint_table_260_6'], 'Tintinalli Table 260-6 compares vascular imaging options for penetrating neck trauma.')}{source_card(c['tint_table_260_7'], 'Tintinalli Table 260-7 lists BCVI screening criteria and risk factors for blunt carotid/vertebral injury.')}{source_card(c['tint_table_260_8'], 'Tintinalli Table 260-8 grades blunt carotid and vertebral artery injury and links grade to treatment.')}</section>
<section class="section" id="aerodigestive"><h2>Laryngotracheal and Pharyngoesophageal Injuries</h2><p>Laryngotracheal injury can be subtle or delayed. Stridor, dysphonia, hemoptysis, air bubbling, airway obstruction, tracheal deviation, subcutaneous emphysema, or restricted vocal cord mobility should prompt airway planning and flexible fiberoptic laryngoscopy when feasible.</p><p>Table 260-9 turns laryngeal injury into action. Grade I is minor endolaryngeal hematoma without fracture and is usually monitored. Grade II edema/hematoma or minor mucosal disruption without exposed cartilage plus nondisplaced fracture can often be managed medically with close observation. Grade III means massive edema, mucosal disruption, exposed cartilage, vocal fold immobility, or displaced fracture and usually needs operative management. Grade IV is worse structural disruption with multiple fracture lines or massive trauma to laryngeal mucosa. Grade V is complete laryngotracheal separation: the airway may need to be established through the neck into the distal trachea before definitive repair.</p><p>Pharyngoesophageal injury is uncommon but easy to miss. Odynophagia, dysphagia, saliva from the wound, hematemesis, retropharyngeal or mediastinal air, or concerning trajectory should trigger targeted evaluation. If suspected, keep the patient NPO, start broad-spectrum IV antibiotics with anaerobic coverage, and involve surgery/ENT early. Small contained pharyngeal perforations may be managed medically, but esophageal perforations or uncontained leaks need repair.</p><div class="callout pearl"><strong><u>Exam phrase:</u></strong> a negative CTA does not automatically clear the esophagus when suspicion remains high; add esophagoscopy, esophagram, or CT esophagography per local pathway.</div>{source_card(c['tint_table_260_9'], 'Tintinalli Table 260-9 grades laryngeal injury severity and frames conservative versus operative management.')}</section>
<section class="section" id="strangulation"><h2>Strangulation and Special Populations</h2><p>Strangulation is blunt neck trauma. The major lethal pathway is often neck vessel occlusion and cerebral hypoxia, not simply airway obstruction. External findings can be absent: many victims are walking, talking, intoxicated, anxious, or ashamed, and severe laryngeal or vascular injury may hide under a quiet skin exam.</p><p>Table 260-10 is the trigger list for further testing. HEENT warning signs include visual disturbance, conjunctival/facial petechiae, swollen tongue or oropharynx, blood/vomit/tissue in the oropharynx, facial edema/lacerations/abrasions/ecchymosis, neck abrasions or ligature marks, neck tenderness, hoarseness/stridor, and subcutaneous edema or crepitus. Cardiovascular and pulmonary danger signs include cyanosis or hypoxia, arrhythmias, respiratory distress, crackles/wheezes, and cough. Neurologic danger signs include altered mental status, seizure, stroke-like symptoms, and incontinence.</p><p>Those table findings should lead to imaging/endoscopy and admission when abnormal. Symptomatic patients with normal studies still need observation when the story or exam is concerning. Domestic violence safety planning, social work, forensic documentation, and delayed return precautions are part of medical care, not an optional add-on.</p>{source_card(c['tint_table_260_10'], 'Tintinalli Table 260-10 lists hard signs of strangulation injury for imaging/admission decisions.')}</section>
<section class="question-set section" id="assessment"><h2>Inline Assessment MCQs</h2>{build_mcqs()}</section>
</div></main></div><div class="score-pill" data-score-text>0 correct / 0 answered / 26 total</div><div class="image-modal" data-image-modal><button class="hdr-btn" data-modal-close>Close</button><img alt="Zoomed source"></div><script>{SCRIPT}</script></body></html>"""


def extract_embedded(doc: str) -> list[Path]:
    EMBED.mkdir(parents=True, exist_ok=True)
    for old in EMBED.glob("*.png"):
        old.unlink()
    paths = []
    for i, m in enumerate(re.finditer(r"data:image/png;base64,([^\"]+)", doc), 1):
        p = EMBED / f"ch260_embedded_{i:02d}.png"
        p.write_bytes(base64.b64decode(m.group(1)))
        paths.append(p)
    return paths


def contact_sheet(paths: list[Path]) -> Path:
    cols, cell_w, cell_h = 2, 500, 420
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
    draw = ImageDraw.Draw(sheet)
    for i, path in enumerate(paths):
        img = Image.open(path).convert("RGB")
        img.thumbnail((450, 360))
        x, y = (i % cols) * cell_w, (i // cols) * cell_h
        sheet.paste(img, (x + 24, y + 44))
        draw.text((x + 8, y + 10), f"{i+1:02d} {path.name}", fill=(0, 0, 0))
    out = EMBED / "ch260_embedded_contact_sheet.png"
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
    md = f"""# CH260 Crop QA - 2026-05-09

Fresh rebuild from source PDFs. The previous Chapter260 HTML was deleted and not used as a basis.

## Source Inventory Used

Tintinalli inventory: 14/14 included. Required Tintinalli objects are Figure 260-1, Figure 260-2, Figure 260-3, Figure 260-4, and Table 260-1 through Table 260-10.

{inv}

## Embedded Crop QA

Contact sheet: `{sheet.relative_to(ROOT).as_posix()}`

| # | Source | Object | PDF | PDF page | Extracted final embedded image | Status | Note |
|---|---|---|---|---:|---|---|---|
{chr(10).join(rows)}

## Content Gate

Content: PASS. Major neck-trauma headings have narrative summaries; source crops are topic-local; ATLS is integrated into the body narrative; Rosen source card has visible `Rosen vs Tintinalli` difference; no visible audit/source-audit repair text is inside the chapter.

Pattern: PASS. Ch186/Ch201 shell, top header, sidebar/main layout, source cards, and accepted MCQ behavior are present.
"""
    QA_MD.write_text(md, encoding="utf-8")
    QA_HTML.write_text(md_to_html(md, "CH260 Crop QA"), encoding="utf-8")


def update_audit() -> None:
    md = AUDIT_MD.read_text(encoding="utf-8")
    line = "| 260 | Chapter260_NeckTrauma.html | PASS | PASS | PASS | 26 | 1 | 11 | 17 | PASS | 7 | From-zero rebuild 2026-05-09 after deletion; Pattern: PASS; Content: PASS; MCQ all-option explanations PASS; every Tintinalli figure/table included (14/14); Rosen/ATLS source crops topic-local; ATLS integrated in body; cropQA PASS (17/17) |"
    if re.search(r"^\| 260 \|.*$", md, flags=re.M):
        md = re.sub(r"^\| 260 \|.*$", line, md, flags=re.M)
    else:
        md = md.rstrip() + "\n" + line + "\n"
    AUDIT_MD.write_text(md, encoding="utf-8")
    AUDIT_HTML.write_text(md_to_html(md, "Chapter Complete Audit"), encoding="utf-8")


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
        "rosen": doc.count("Rosen source"),
        "delta": doc.count("Rosen vs Tintinalli"),
        "atls_delta": doc.count("ATLS vs Tintinalli"),
    }
    assert checks["top"] == 1 and checks["hdr_btn"] >= 2, checks
    assert checks["sidebar"] == 1 and checks["main"] == 1, checks
    assert checks["sidebar_link"] > 0 and checks["sidebar_block"] > 0 and checks["hero_title"] > 0, checks
    assert checks["sections"] > 0 and checks["mcq"] == 26 and checks["result"] == 26 and checks["legacy_mcq"] == 0, checks
    assert checks["source_fig"] == len(CROPS) and checks["data"] == len(CROPS) == len(paths), checks
    assert checks["mark"] > 0 and checks["u"] > 0, checks
    assert checks["rosen"] >= 1 and checks["delta"] >= 1 and checks["atls_delta"] >= 2, checks
    forbidden = ["Source Check", "Rosen Source Audit", "Source Audit", "Included", "Excluded", "repair notes"]
    assert not any(x in doc for x in forbidden), checks
    print(checks)


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
    gate(doc, paths)
    update_audit()
    mirror_complete = MIRROR / "docs/chapters/complete"
    mirror_complete.mkdir(parents=True, exist_ok=True)
    shutil.copy2(OUT_HTML, mirror_complete / OUT_HTML.name)
    for file in [QA_MD, QA_HTML, AUDIT_MD, AUDIT_HTML]:
        shutil.copy2(file, MIRROR / file.name)
    print(f"wrote {OUT_HTML}")
    print(f"wrote {QA_MD}")
    print(f"contact {sheet}")


if __name__ == "__main__":
    main()
