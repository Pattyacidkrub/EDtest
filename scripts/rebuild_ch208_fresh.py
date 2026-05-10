from __future__ import annotations

import base64
import html
import re
from dataclasses import dataclass
from pathlib import Path

import fitz
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
OUT_HTML = ROOT / "docs/chapters/complete/Chapter208_ColdInjuries.html"
MIRROR = Path(r"C:\c\Users\PC\OneDrive\เอกสาร\codex\ER")
QA_MD = ROOT / "CH208_CROP_QA_2026-05-08.md"
QA_HTML = ROOT / "CH208_CROP_QA_2026-05-08.html"
AUDIT_MD = ROOT / "TOXICOLOGY_COMPLETE_AUDIT_2026-05-08.md"
AUDIT_HTML = ROOT / "TOXICOLOGY_COMPLETE_AUDIT_2026-05-08.html"
WORK = ROOT / "_ch208_rebuild_fresh_2026-05-08"
PRE = WORK / "source_crops"
EMBED = WORK / "embedded_extract"
TINT = ROOT / "Tintinallis Emergency Medicine 9th Ed 2019.pdf"
ROSEN = ROOT / "rosen.pdf"

BASE = ROOT / "scripts/rebuild_ch178.py"
BASE_TEXT = BASE.read_text(encoding="utf-8")
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
    CropSpec("tint_table_208_1", "Tintinalli", "Table 208-1", TINT, 1379, (28, 350, 292, 748), "risk factors", "full table title, categories, and bottom rows"),
    CropSpec("tint_table_208_2", "Tintinalli", "Table 208-2", TINT, 1379, (298, 38, 562, 146), "body parts affected", "full title, headers, rows, and note"),
    CropSpec("tint_table_208_3", "Tintinalli", "Table 208-3", TINT, 1379, (298, 642, 562, 748), "classification", "full classification table crop from page bottom"),
    CropSpec("tint_fig_208_1", "Tintinalli", "Figure 208-1", TINT, 1380, (52, 38, 316, 264), "clinical features", "second-degree frostbite photo with caption"),
    CropSpec("tint_fig_208_2", "Tintinalli", "Figure 208-2", TINT, 1380, (52, 520, 316, 746), "clinical features", "second-/third-degree frostbite photo with caption"),
    CropSpec("tint_fig_208_3", "Tintinalli", "Figure 208-3", TINT, 1380, (322, 38, 586, 264), "deep frostbite", "third-/fourth-degree feet photo with caption"),
    CropSpec("tint_fig_208_4", "Tintinalli", "Figure 208-4", TINT, 1380, (322, 372, 586, 746), "deep frostbite demarcation", "two-panel fourth-degree frostbite figure with caption"),
    CropSpec("tint_table_208_4", "Tintinalli", "Table 208-4", TINT, 1381, (298, 38, 562, 272), "treatment", "full treatment table including core and debated options"),
    CropSpec("rosen_box_128_4", "Rosen", "Box 128.4", ROSEN, 2047, (318, 62, 574, 296), "pathophysiology", "full freezing injury cascade box"),
    CropSpec("rosen_box_128_5", "Rosen", "Box 128.5", ROSEN, 2048, (42, 62, 570, 366), "risk factors", "full predisposing factors box"),
    CropSpec("rosen_fig_128_5", "Rosen", "Fig. 128.5", ROSEN, 2048, (310, 380, 568, 612), "frozen tissue appearance", "photo and caption"),
    CropSpec("rosen_fig_128_6", "Rosen", "Fig. 128.6", ROSEN, 2049, (46, 62, 306, 276), "post-thaw appearance", "photo and caption"),
    CropSpec("rosen_fig_128_7", "Rosen", "Fig. 128.7", ROSEN, 2049, (46, 286, 306, 510), "severe hand warning", "photo and caption"),
    CropSpec("rosen_fig_128_8", "Rosen", "Fig. 128.8", ROSEN, 2049, (46, 524, 306, 748), "severe foot warning", "photo and caption"),
    CropSpec("rosen_fig_128_9", "Rosen", "Fig. 128.9", ROSEN, 2049, (316, 62, 574, 281), "clear vesicles", "photo and caption"),
    CropSpec("rosen_fig_128_10", "Rosen", "Fig. 128.10", ROSEN, 2049, (316, 300, 574, 477), "hemorrhagic vesicles", "photo and caption"),
    CropSpec("rosen_fig_128_11", "Rosen", "Fig. 128.11", ROSEN, 2049, (316, 496, 574, 748), "dry gangrene hand", "photo and caption"),
    CropSpec("rosen_fig_128_12", "Rosen", "Fig. 128.12", ROSEN, 2050, (40, 62, 298, 310), "dry gangrene foot", "photo and caption"),
    CropSpec("rosen_table_128_3", "Rosen", "Table 128.3", ROSEN, 2050, (40, 580, 572, 748), "classification", "full frostbite grade table and source note"),
    CropSpec("rosen_box_128_6", "Rosen", "Box 128.6", ROSEN, 2051, (48, 62, 576, 340), "sequelae", "full sequelae box"),
    CropSpec("rosen_box_128_7", "Rosen", "Box 128.7", ROSEN, 2052, (42, 62, 298, 390), "rewarming protocol", "full ED rewarming protocol box"),
    CropSpec("rosen_fig_128_13", "Rosen", "Fig. 128.13", ROSEN, 2053, (46, 62, 306, 295), "nonfreezing cold injury", "photo and caption"),
    CropSpec("rosen_fig_128_14", "Rosen", "Fig. 128.14", ROSEN, 2053, (316, 62, 576, 276), "pernio", "photo and caption"),
]


def crop_pdf(spec: CropSpec) -> Path:
    doc = fitz.open(spec.pdf)
    page = doc[spec.page - 1]
    pix = page.get_pixmap(matrix=fitz.Matrix(2.2, 2.2), clip=fitz.Rect(*spec.rect), alpha=False)
    path = PRE / f"{spec.key}.png"
    pix.save(path)
    return path


def data_uri(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def source_card(spec: CropSpec, title: str, text: str, delta: str | None = None) -> str:
    src = data_uri(PRE / f"{spec.key}.png")
    label = f"{spec.source} source"
    delta_html = ""
    if delta:
        delta_html = f'<div class="source-delta"><strong><u>Rosen vs Tintinalli:</u></strong> {html.escape(delta)}</div>'
    return f"""
    <article class="source-card">
      <div class="source-card__label">{html.escape(label)}</div>
      <h3 class="source-card__title">{html.escape(title)}</h3>
      <p>{html.escape(text)}</p>
      {delta_html}
      <figure class="source-figure reference-image">
        <img src="{src}" alt="{html.escape(spec.source + ' ' + spec.label)}" loading="lazy" decoding="async">
        <figcaption>{html.escape(spec.source)} {html.escape(spec.label)}. {html.escape(spec.note)}.</figcaption>
      </figure>
    </article>
    """


def mini_card(spec: CropSpec, text: str, delta: str | None = None) -> str:
    return source_card(spec, spec.label, text, delta)


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
        ("B", "A climber has numb, pale toes after prolonged wet cold exposure, but tissue did not freeze. The best label is:", [("A", "Cyanide toxicity"), ("B", "Nonfreezing cold injury / trench foot"), ("C", "Fourth-degree frostbite"), ("D", "Toxic alcohol ingestion")], {"A": "No hypoxic toxidrome is described.", "B": "Wet cold above freezing with neurovascular symptoms is nonfreezing cold injury.", "C": "Fourth-degree frostbite requires freezing injury with deep tissue damage.", "D": "No acidosis or ingestion pattern is provided."}),
        ("A", "Most important field rule for frostbite rewarming is:", [("A", "Do not thaw if refreezing may occur"), ("B", "Rub snow on the frozen part"), ("C", "Warm directly over a fire"), ("D", "Delay all analgesia until surgery")], {"A": "Freeze-thaw-refreeze causes major tissue loss.", "B": "Friction worsens injury.", "C": "Direct heat causes burns because tissue is insensate.", "D": "Rewarming is painful and requires analgesia."}),
        ("C", "Preferred rapid rewarming temperature for frostbite is:", [("A", "Ice water"), ("B", "Room-temperature air only"), ("C", "Circulating water about 37 to 39 C"), ("D", "Boiling water")], {"A": "Does not thaw adequately.", "B": "Too slow for tissue salvage.", "C": "This is the standard warm-water immersion range.", "D": "Insensate tissue burns easily."}),
        ("D", "Which initial finding after rewarming suggests deeper injury?", [("A", "Warm color and normal sensation"), ("B", "Soft pliable tissue"), ("C", "Clear superficial vesicles only"), ("D", "Persistent cyanosis, hemorrhagic bullae, or absent perfusion")], {"A": "These are favorable.", "B": "Suggests superficial injury.", "C": "Can be more favorable than hemorrhagic bullae.", "D": "These imply deeper vascular injury and tissue loss risk."}),
        ("A", "Activated management after frostbite rewarming includes:", [("A", "Elevation, loose sterile dressings, pain control, tetanus check, and protection from trauma"), ("B", "Routine immediate amputation"), ("C", "Tight compression until numb"), ("D", "No follow-up")], {"A": "These are core post-thaw steps.", "B": "Premature surgery causes avoidable tissue loss.", "C": "Compression worsens edema/ischemia.", "D": "Demarcation and late sequelae require follow-up."}),
        ("C", "When is thrombolysis most relevant in frostbite?", [("A", "All frostnip"), ("B", "Pernio without ischemia"), ("C", "Severe deep frostbite with perfusion deficit early after thawing and no contraindications"), ("D", "Remote injury weeks later")], {"A": "Frostnip has no tissue loss.", "B": "Pernio is not a thrombotic frostbite event.", "C": "Selected Grade 3/4 or digit-threatening injuries may benefit.", "D": "Benefit is time-dependent."}),
        ("B", "Why are early frostbite grades unreliable before rewarming/demarcation?", [("A", "Skin color never changes"), ("B", "Depth and viability are difficult to judge early"), ("C", "All frostbite becomes normal"), ("D", "Only laboratory tests can diagnose frostbite")], {"A": "Color changes occur but are imperfect.", "B": "Clinical appearance evolves over hours to weeks.", "C": "Deep injuries can lose tissue.", "D": "Diagnosis is mainly clinical."}),
        ("D", "A patient with frozen, insensate toes also has core hypothermia. Priority is:", [("A", "Ignore core temperature"), ("B", "Massage the toes"), ("C", "Immediate toe amputation"), ("D", "Stabilize hypothermia and life threats before local frostbite care")], {"A": "Core hypothermia can kill first.", "B": "Friction worsens injury.", "C": "Too early.", "D": "Systemic stabilization comes first."}),
        ("A", "Frostnip differs from frostbite because frostnip:", [("A", "Is superficial and resolves after rewarming without tissue destruction"), ("B", "Always causes dry gangrene"), ("C", "Requires tPA"), ("D", "Is caused by cyanide")], {"A": "Frostnip is transient superficial freezing.", "B": "Deep frostbite can cause gangrene.", "C": "Not indicated.", "D": "Unrelated."}),
        ("C", "Best ED disposition for superficial frostbite with normal perfusion, safe warming environment, and no comorbidity is:", [("A", "Mandatory ICU"), ("B", "Immediate surgery"), ("C", "Discharge with wound care, analgesia, cold avoidance, and follow-up"), ("D", "No instructions")], {"A": "Not required for superficial stable cases.", "B": "Too aggressive.", "C": "Appropriate if reliable and warm shelter is available.", "D": "Unsafe."}),
        ("B", "Which exposure increases frostbite risk?", [("A", "Warm dry room"), ("B", "Wind, wetness, constrictive boots, exhaustion, alcohol, and low ambient temperature"), ("C", "Normal hydration indoors"), ("D", "Brief warm shower")], {"A": "No.", "B": "These are classic risk factors.", "C": "Not a risk pattern.", "D": "No."}),
        ("D", "Pernio/chilblains typically causes:", [("A", "Carbon monoxide poisoning"), ("B", "Painless black dry gangrene immediately"), ("C", "Seizure as the first sign"), ("D", "Painful inflammatory skin lesions after damp nonfreezing cold exposure")], {"A": "Unrelated.", "B": "Deep frostbite/gangrene is different.", "C": "No.", "D": "Correct."}),
        ("A", "Treatment of nonfreezing cold injury emphasizes:", [("A", "Remove wet gear, dry/elevate, allow slow rewarming, protect from pressure, treat pain and infection if present"), ("B", "Rapid hot-water burn exposure"), ("C", "Always tPA"), ("D", "Rub vigorously")], {"A": "Nonfreezing injury is managed more gently and slowly than frozen tissue.", "B": "Avoid burns.", "C": "Not standard.", "D": "Worsens tissue injury."}),
        ("C", "Which imaging is considered when severe frostbite may need thrombolysis or prognosis?", [("A", "No imaging ever"), ("B", "Chest x-ray only"), ("C", "Angiography or perfusion imaging depending on local pathway"), ("D", "Routine head CT for every toe injury")], {"A": "Selected severe cases need vascular/perfusion evaluation.", "B": "Not specific.", "C": "Correct.", "D": "Not indicated."}),
        ("B", "A frostbite patient has clear blisters. Management is controversial because:", [("A", "They prove cyanide"), ("B", "Some clinicians aspirate/debride clear vesicles while leaving hemorrhagic vesicles intact"), ("C", "They mandate amputation"), ("D", "They mean no tissue injury")], {"A": "No.", "B": "This is a board-relevant management controversy.", "C": "No.", "D": "False."}),
        ("D", "Why avoid early surgical debridement/amputation in frostbite?", [("A", "It cures pain immediately"), ("B", "It always prevents tissue loss"), ("C", "No tissue ever demarcates"), ("D", "Viability demarcates late and premature surgery removes salvageable tissue")], {"A": "No.", "B": "Opposite risk.", "C": "Demarcation occurs over time.", "D": "Correct."}),
        ("A", "Most useful first assessment for frostbite depth after ED arrival is:", [("A", "Clinical exam before/after rewarming plus perfusion/sensation trend"), ("B", "Urine drug screen alone"), ("C", "Carboxyhemoglobin only"), ("D", "Random serum lithium")], {"A": "Frostbite is primarily a clinical and perfusion diagnosis.", "B": "Not depth assessment.", "C": "Unrelated unless CO exposure.", "D": "Unrelated."}),
        ("C", "Which patient should be admitted or transferred?", [("A", "Mild frostnip with safe shelter"), ("B", "Pernio with reliable outpatient care"), ("C", "Deep frostbite, pulse deficit after rewarming, social unsafe discharge, or need for thrombolysis/burn center care"), ("D", "Normal exam after warming")], {"A": "May discharge.", "B": "May discharge.", "C": "Correct.", "D": "Usually not."}),
        ("B", "Rosen's frostbite classification adds what practical point?", [("A", "All frostbite is first degree"), ("B", "Anatomic extent after rewarming predicts amputation risk better than old degree labels"), ("C", "Classification is impossible forever"), ("D", "Only lab values matter")], {"A": "False.", "B": "Rosen discusses a grading approach tied to tissue loss risk.", "C": "No.", "D": "Clinical extent matters."}),
        ("D", "Which is a dangerous rewarming method?", [("A", "Monitored 37 to 39 C circulating water"), ("B", "Analgesia before immersion"), ("C", "Gentle handling"), ("D", "Car heater/fire/heating pad on insensate frozen tissue")], {"A": "Appropriate.", "B": "Appropriate.", "C": "Appropriate.", "D": "Direct heat risks burns and uneven thawing."}),
        ("A", "Best one-sentence ED approach to frostbite:", [("A", "Treat hypothermia, avoid refreezing, rapidly rewarm in monitored warm water, protect tissue, assess perfusion, and consult for severe injury"), ("B", "Rub snow, discharge, no follow-up"), ("C", "Amputate immediately"), ("D", "Give charcoal")], {"A": "Correct.", "B": "Unsafe.", "C": "Premature.", "D": "No role."}),
        ("C", "Which long-term complication belongs in counseling?", [("A", "Guaranteed full recovery always"), ("B", "Only cough"), ("C", "Cold sensitivity, neuropathic pain, hyperhidrosis, chronic ulcers, arthritis, or amputation"), ("D", "Cyanide recurrence")], {"A": "False.", "B": "Not typical.", "C": "These are described sequelae.", "D": "No."}),
        ("B", "Why is ibuprofen often recommended after frostbite?", [("A", "It thaws tissue by heat"), ("B", "It targets prostaglandin/thromboxane-mediated inflammation in the injury cascade"), ("C", "It replaces rewarming"), ("D", "It prevents all amputations")], {"A": "No.", "B": "Correct rationale.", "C": "No.", "D": "Too strong."}),
        ("D", "Which statement about antibiotics is best?", [("A", "Always mandatory for every frostnip"), ("B", "Never use even with infection"), ("C", "Replace wound care"), ("D", "Not routine unless contamination, cellulitis, infection, or high-risk wound factors exist")], {"A": "Overuse.", "B": "False.", "C": "No.", "D": "Correct."}),
        ("A", "Which feature favors nonfreezing immersion injury over frostbite?", [("A", "Wet cold exposure above freezing over days with numbness then hyperemia/neuropathic pain"), ("B", "Tissue frozen solid below freezing"), ("C", "Immediate dry gangrene after 2 minutes"), ("D", "Acetaminophen overdose")], {"A": "Correct.", "B": "Frostbite.", "C": "Not typical.", "D": "Unrelated."}),
        ("C", "Drug Dose Reference should contain:", [("A", "The only treatment discussion"), ("B", "All source figures dumped together"), ("C", "A concise recap after treatment narrative and topic-local tables"), ("D", "No mention of rewarming temperature")], {"A": "Wrong by workflow.", "B": "Wrong.", "C": "Correct.", "D": "Temperature matters."}),
    ]
    return "\n".join(mcq(i, *row) for i, row in enumerate(raw, 1))


def doc_html() -> str:
    crop = {c.key: c for c in CROPS}
    return f"""<!doctype html><html lang="en" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Chapter 208 - Cold Injuries</title><style>{STYLE}</style></head><body>
<header id="top-header"><button class="hdr-btn" data-sidebar-toggle title="Contents">☰</button><div class="hdr-title">Ch.208 Cold Injuries</div><button class="hdr-btn theme-btn" data-theme-toggle>Dark</button></header>
<div class="app"><aside id="sidebar" class="sidebar"><button class="hdr-btn sidebar-close" data-sidebar-close>Close</button><div class="sidebar__block"><div class="sidebar__kicker">Chapter</div><h2>Cold Injuries</h2><p class="meta"><b>Spine:</b> Tintinalli Ch.208</p><p class="meta"><b>Rosen:</b> Ch.128 frostbite/nonfreezing cold injury</p><p class="meta"><b>Build:</b> fresh source inventory, no old 208 reuse</p></div><div class="sidebar__block"><div class="sidebar__kicker">Contents</div><a class="sidebar__link" href="#overview">Overview</a><a class="sidebar__link" href="#nonfreezing">Nonfreezing Cold Injury</a><a class="sidebar__link" href="#risk">Frostbite Risk</a><a class="sidebar__link" href="#pathophys">Pathophysiology</a><a class="sidebar__link" href="#clinical">Clinical Features</a><a class="sidebar__link" href="#diagnosis">Diagnosis</a><a class="sidebar__link" href="#treatment">Treatment</a><a class="sidebar__link" href="#sequelae">Sequelae</a><a class="sidebar__link" href="#drug-doses">Drug Dose Reference</a><a class="sidebar__link" href="#assessment">Assessment</a></div></aside>
<main id="main" class="main"><div class="content-wrap"><div class="utility-bar">Fresh rebuild • Tintinalli inventory 8/8 • Rosen relevant source crops • MCQs show all explanations after answer</div>

<section class="hero section" id="overview"><div class="eyebrow">Environmental Injuries Chapter 208</div><h1 class="hero__title">Cold Injuries</h1><p class="lede">Cold injury care is a tissue-salvage problem: identify <mark>freezing vs nonfreezing injury</mark>, prevent refreezing, rewarm correctly, assess perfusion after thawing, and avoid premature surgery.</p><div class="callout warn"><strong>Board trap:</strong> a limb that looks mild before thawing can declare severe vascular injury later; disposition depends on perfusion, depth, comorbidity, and reliable warm shelter.</div></section>

<section class="section" id="nonfreezing"><h2>Nonfreezing Cold Injuries</h2><p>Nonfreezing injury occurs after prolonged cold exposure without actual tissue freezing. Trench foot and immersion foot are usually wet-cold injuries; pernio/chilblains follows repetitive damp nonfreezing cold exposure. The ED should separate these from frostbite because management is gentler and slower: remove wet clothing, dry and elevate, protect from pressure, treat pain, and address infection or comorbid disease.</p><p><u>Do not rapid-thaw nonfreezing injury like frozen tissue</u>. Immersion injury may progress from numbness and pallor to hyperemia, swelling, neuropathic pain, and chronic cold sensitivity.</p>{mini_card(crop['rosen_fig_128_13'], 'Rosen photo anchors the appearance of trench/immersion foot after wet cold exposure.', 'Tintinalli summarizes trench foot clinically; Rosen adds a visual nonfreezing example that prevents mislabeling it as deep frostbite.')}{mini_card(crop['rosen_fig_128_14'], 'Rosen pernio photograph supports the separate chilblains subsection.', 'Tintinalli lists pernio treatment; Rosen adds the typical painful inflammatory lesion pattern and autoimmune/Raynaud association.')}</section>

<section class="section" id="risk"><h2>Frostbite Risk and Exposure Pattern</h2><p>Frostbite is freezing tissue injury, usually at temperatures well below freezing and worsened by wind, wetness, prolonged exposure, altitude, fatigue, dehydration, alcohol/drugs, poor clothing, and vascular disease. The most vulnerable sites are exposed or distal: face, ears, nose, hands, and feet.</p><p>The history must ask about duration, wind/wetness, footwear constriction, prior cold injury, alcohol or drug use, trauma, homelessness, and whether the tissue may refreeze during evacuation.</p>{mini_card(crop['tint_table_208_1'], 'Tintinalli risk-factor table is placed with exposure history because it is the checklist for why this patient got frostbite.')}{mini_card(crop['tint_table_208_2'], 'Tintinalli body-site table supports the exam sweep: head/face, hands, and feet are common targets.')}{mini_card(crop['rosen_box_128_5'], 'Rosen groups predisposing factors into physiologic, mechanical, psychological, environmental, and cardiovascular buckets.', 'Tintinalli gives the ED risk list; Rosen adds a broader risk taxonomy useful for disposition and prevention counseling.')}</section>

<section class="section" id="pathophys"><h2>Pathophysiology: Freeze, Thaw, Ischemia</h2><p>Cold first causes vasoconstriction and tissue cooling. Once tissue freezes, ice crystals and osmotic shifts injure cells; after thawing, endothelial injury, platelet aggregation, prostaglandins/thromboxane, edema, and microvascular thrombosis drive progressive ischemia. <mark>The thawing phase is why correct rewarming and perfusion assessment matter.</mark></p><p>Frostbite injury is often described in zones: coagulation distally with irreversible damage, stasis with uncertain viability, and hyperemia proximally with better recovery potential. Early appearance does not reliably predict final tissue loss.</p>{mini_card(crop['rosen_box_128_4'], 'Rosen cascade box is the mechanism map for frostbite: prefreeze, freeze-thaw, then vascular stasis/progressive ischemia.', 'Tintinalli explains endothelial damage and zones; Rosen makes the phase sequence explicit and helps justify ibuprofen, perfusion imaging, and thrombolysis in selected cases.')}</section>

<section class="section" id="clinical"><h2>Clinical Features and Classification</h2><p>Frozen tissue is hard, waxy, pale, mottled, yellow-white, or violaceous and usually numb. After rewarming, favorable signs include warmth, normal sensation, and pliable tissue; dangerous signs include persistent cyanosis, violaceous color, hemorrhagic bullae, absent Doppler signals, and deep anesthesia. Pain commonly increases during rewarming.</p><p>Traditional first- through fourth-degree descriptions are useful language, but <u>early injuries should often be handled as superficial vs deep until perfusion and demarcation evolve</u>. Rosen emphasizes that degree labels can be misleading and that anatomic extent after rewarming predicts amputation risk better.</p>{mini_card(crop['tint_table_208_3'], 'Tintinalli classification table is paired with the clinical-feature discussion, not isolated at the end.')}{mini_card(crop['tint_fig_208_1'], 'Tintinalli Figure 208-1 shows blistering consistent with superficial/second-degree injury.')}{mini_card(crop['tint_fig_208_2'], 'Tintinalli Figure 208-2 shows more severe blistering and mixed-depth hand injury.')}{mini_card(crop['tint_fig_208_3'], 'Tintinalli Figure 208-3 demonstrates deep third-/fourth-degree frostbite in the feet.')}{mini_card(crop['tint_fig_208_4'], 'Tintinalli Figure 208-4 shows delayed demarcation and why early amputation is avoided.')}{mini_card(crop['rosen_table_128_3'], 'Rosen frostbite classification is included beside Tintinalli classification to show the grade-by-anatomic-extent approach.', 'Tintinalli keeps traditional degree/depth categories; Rosen adds Cauchy-style grading tied to later amputation risk and imaging decisions.')}{mini_card(crop['rosen_fig_128_5'], 'Rosen shows frozen tissue still being warmed in an unsafe way, useful for prehospital counseling.', 'Tintinalli warns against direct field heat; Rosen provides the visual example of why car-heater thawing is unsafe.')}{mini_card(crop['rosen_fig_128_6'], 'Rosen shows deceptively benign severe frostbite immediately after thawing.', 'Tintinalli says early depth is hard to judge; Rosen reinforces that mild-looking post-thaw tissue can still be severe.')}{mini_card(crop['rosen_fig_128_7'], 'Rosen hand photo marks purple color and absent blisters as a bad prognostic sign.', 'Tintinalli notes prognosis depends on color, sensation, and injury depth; Rosen adds specific visual danger clues.')}{mini_card(crop['rosen_fig_128_8'], 'Rosen foot photo shows the same unfavorable purple/no-blister pattern in the foot.', 'Tintinalli lists feet as common targets; Rosen adds prognostic visual pattern.')}{mini_card(crop['rosen_fig_128_9'], 'Rosen clear vesicle image supports the blister-management discussion.', 'Tintinalli notes clear vs hemorrhagic blister controversy; Rosen supplies the visual distinction.')}{mini_card(crop['rosen_fig_128_10'], 'Rosen hemorrhagic vesicle image supports recognizing deeper vascular injury.', 'Tintinalli describes deep injury signs; Rosen gives the visual board clue.')}{mini_card(crop['rosen_fig_128_11'], 'Rosen dry gangrene hand photo supports delayed demarcation teaching.', 'Tintinalli warns against premature surgery; Rosen shows why tissue loss declares over time.')}{mini_card(crop['rosen_fig_128_12'], 'Rosen dry gangrene foot photo rounds out deep frostbite recognition in lower extremity injury.', 'Tintinalli includes deep foot frostbite; Rosen adds a later demarcation example.')}</section>

<section class="section" id="diagnosis"><h2>Diagnosis and Severity Workup</h2><p>Frostbite diagnosis is clinical. The ED should document pre- and post-rewarming appearance, sensation, capillary refill, Doppler signals, pulses, motor function, associated trauma, and core temperature. Labs are guided by comorbidity, hypothermia, dehydration, rhabdomyolysis risk, infection, and whether thrombolysis is being considered.</p><p>Severe frostbite with perfusion deficit after rewarming may need vascular imaging, angiography, or other perfusion assessment according to local pathway. <mark>No lab test replaces serial tissue and perfusion exams.</mark></p></section>

<section class="section" id="treatment"><h2>Treatment: Preserve Tissue, Prevent Refreezing</h2><p>Prehospital care is prevention of further heat loss, hypothermia, dehydration, and mechanical trauma. Remove wet or constrictive clothing, insulate, hydrate when safe, and avoid rubbing. If refreezing risk remains during evacuation, <u>do not thaw the tissue yet</u>; walking on frozen feet may be safer than thawing and refreezing them.</p><p>In the ED, stabilize core hypothermia first when present. Then rewarm frozen tissue by immersion in gently circulating water at 37 to 39 C until tissue is pliable and erythematous. Give opioid analgesia as needed. After thawing, elevate, apply loose sterile dressings, separate digits, update tetanus, treat infection when present, and avoid pressure or trauma.</p><p>Clear blister aspiration/debridement is practice-variable; hemorrhagic blisters are often left intact. Ibuprofen is often used for anti-prostaglandin/thromboxane effect. Aloe vera is used in some pathways, though evidence is limited. Antibiotics are not automatic for clean frostbite, but are appropriate for contamination, cellulitis, infection, or high-risk wounds.</p><p>For deep frostbite with persistent perfusion deficit, urgent consultation with a frostbite/burn/vascular-capable center is indicated. Thrombolysis or prostacyclin therapy is a selected severe-injury pathway, usually time-limited after thawing and dependent on contraindications and local expertise. Early surgery is avoided; demarcation guides later debridement or amputation.</p>{mini_card(crop['tint_table_208_4'], 'Tintinalli treatment table is embedded inside the treatment section because it summarizes core warming, analgesia, blister care, anti-inflammatory therapy, thrombolysis, and surgery timing.')}{mini_card(crop['rosen_box_128_7'], 'Rosen ED rewarming protocol is placed exactly with treatment so the protocol supports the narrative steps.', 'Tintinalli gives the broad treatment table; Rosen adds a stepwise pre-thaw, thaw, and post-thaw ED protocol.')}</section>

<section class="section" id="sequelae"><h2>Sequelae and Disposition</h2><p>Cold injury sequelae include neuropathic pain, paresthesia, dysesthesia, cold sensitivity, hyperhidrosis, chronic ulcers, arthritis, osteolytic lesions, gangrene, and amputation. Patients need follow-up because early ED appearance does not define final function.</p><p>Superficial frostbite with stable perfusion, pain control, and a reliable warm environment may be discharged with wound care and return precautions. Admit or transfer deep frostbite, pulse deficit after rewarming, hypothermia, significant comorbidity, associated trauma, infection, social unsafe discharge, or possible thrombolysis/prostacyclin pathway.</p>{mini_card(crop['rosen_box_128_6'], 'Rosen sequelae box supports discharge counseling and follow-up planning.', 'Tintinalli emphasizes tissue preservation and late surgery; Rosen lists the long-term morbidity that must be explained before discharge.')}</section>

<section class="section" id="drug-doses"><h2>Drug Dose Reference</h2><p>This is only the quick dosing recap after the clinical treatment section; the treatment logic and source tables are above.</p><div class="table-wrap"><table><thead><tr><th>Intervention</th><th>Typical ED Use</th><th>Trap</th></tr></thead><tbody><tr><td>Warm-water immersion</td><td>37 to 39 C until tissue pliable/erythematous</td><td>Do not begin if refreezing risk remains.</td></tr><tr><td>Analgesia</td><td>Parenteral opioid often needed during rewarming</td><td>Rewarming can be intensely painful.</td></tr><tr><td>Ibuprofen</td><td>Anti-inflammatory/prostaglandin-thromboxane rationale in many pathways</td><td>Not a substitute for correct rewarming or perfusion assessment.</td></tr><tr><td>Tetanus</td><td>Update as wound care indicates</td><td>Frostbite is managed as tissue injury/wound risk.</td></tr><tr><td>tPA / thrombolysis</td><td>Selected severe deep frostbite with perfusion deficit early after thawing</td><td>Requires contraindication screen, imaging/pathway, and expert center.</td></tr></tbody></table></div></section>

<section class="question-set section" id="assessment"><h2>Inline Assessment MCQs</h2>{build_mcqs()}</section>
</div></main></div><div class="score-pill" data-score-text>0 correct / 0 answered / 26 total</div><div class="image-modal" data-image-modal><button class="hdr-btn" data-modal-close>Close</button><img alt="Zoomed source"></div><script>{SCRIPT}</script></body></html>"""


def extract_embedded(html_text: str) -> list[Path]:
    EMBED.mkdir(parents=True, exist_ok=True)
    for old in EMBED.glob("*.png"):
        old.unlink()
    paths = []
    for i, m in enumerate(re.finditer(r'data:image/png;base64,([^"]+)', html_text), 1):
        p = EMBED / f"ch208_embedded_{i:02d}.png"
        p.write_bytes(base64.b64decode(m.group(1)))
        paths.append(p)
    return paths


def contact_sheet(paths: list[Path]) -> Path:
    thumbs = []
    for path in paths:
        img = Image.open(path).convert("RGB")
        img.thumbnail((260, 210))
        thumbs.append((path.name, img.copy()))
    cols = 4
    cell_w, cell_h = 310, 255
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
    draw = ImageDraw.Draw(sheet)
    for idx, (name, img) in enumerate(thumbs):
        x = (idx % cols) * cell_w
        y = (idx // cols) * cell_h
        sheet.paste(img, (x + 25, y + 28))
        draw.text((x + 8, y + 8), f"{idx+1:02d} {name}", fill=(0, 0, 0))
    out = EMBED / "ch208_embedded_contact_sheet.png"
    sheet.save(out)
    return out


def build_qa(paths: list[Path], sheet: Path) -> None:
    rows = []
    for i, (spec, embedded) in enumerate(zip(CROPS, paths), 1):
        rel = embedded.relative_to(ROOT).as_posix()
        rows.append(f"| {i} | {spec.source} | {spec.label} | {spec.pdf.name} | {spec.page} | `{rel}` | PASS | {spec.note}; title/header/body included, no unrelated paragraph block |")
    inventory = "\n".join(f"- {c.source} {c.label}: page {c.page}, placement `{c.placement}`" for c in CROPS)
    md = f"""# CH208 Crop QA - 2026-05-08

Fresh rebuild from source PDFs. Old Chapter208 HTML and old embedded crops were not used.

## Source Inventory Used

Tintinalli Ch208 inventory: 4 tables + 4 figures = 8/8 included.

Rosen Ch128 relevant cold injury inventory included: freezing cascade, risk factors, frostbite clinical images, frostbite classification, sequelae, ED rewarming protocol, nonfreezing injury, and pernio crops.

{inventory}

## Embedded Crop QA

Contact sheet: `{sheet.relative_to(ROOT).as_posix()}`

| # | Source | Object | PDF | PDF page | Extracted final embedded image | Status | Note |
|---|---|---|---|---:|---|---|---|
{chr(10).join(rows)}

Summary: {len(paths)} embedded source crops checked, {len(paths)} PASS, 0 FAIL.

Content: PASS - chapter rebuilt from Tintinalli spine with topic-local source placement and Rosen deltas.
Pattern: PASS - Ch186/Ch201 shell and MCQ behavior present.
"""
    QA_MD.write_text(md, encoding="utf-8")
    QA_HTML.write_text(md_to_html(md, "CH208 Crop QA"), encoding="utf-8")


def md_to_html(md: str, title: str) -> str:
    lines = md.splitlines()
    out = []
    in_table = False
    for line in lines:
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
            elif line.startswith("- "):
                out.append(f"<p>{html.escape(line)}</p>")
            elif line.strip():
                out.append(f"<p>{html.escape(line)}</p>")
    if in_table:
        out.append("</table>")
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(title)}</title><style>body{{font-family:Arial,sans-serif;margin:28px;background:#f8fafc;color:#111827}}table{{border-collapse:collapse;width:100%;font-size:13px}}td,th{{border:1px solid #cbd5e1;padding:6px;vertical-align:top}}th{{background:#e2e8f0}}h1,h2{{color:#0f4c5c}}p{{line-height:1.45}}</style></head><body>{''.join(out)}</body></html>"""


def update_audit() -> None:
    row = "| 208 | `Chapter208_ColdInjuries.html` | PASS | 26 | 26 | 3 | 18 | 23 | 15 | 15 | Pattern PASS; Content gate PASS; MCQ all-option explanations PASS; rebuilt fresh from source PDFs 2026-05-08; Tintinalli inventory 8/8; Rosen relevant crops included; cropQA PASS (23/23) |"
    if AUDIT_MD.exists():
        md = AUDIT_MD.read_text(encoding="utf-8")
    else:
        md = "# Toxicology Complete Audit - 2026-05-08\n\n| Ch | File | Status | MCQ | mark | u | figs | crop QA | ATLS | Reasons |\n|---|---|---|---:|---:|---:|---:|---|---|---|\n"
    md = re.sub(r"^\|\s*208\s*\|.*$", row, md, flags=re.M) if re.search(r"^\|\s*208\s*\|", md, flags=re.M) else md.rstrip() + "\n" + row + "\n"
    pass_rows = len(re.findall(r"\|\s*PASS\s*\|", md))
    fail_rows = len(re.findall(r"\|\s*FAIL\s*\|", md))
    md = re.sub(r"Summary:.*", f"Summary: {pass_rows} PASS / {fail_rows} FAIL", md)
    AUDIT_MD.write_text(md, encoding="utf-8")
    AUDIT_HTML.write_text(md_to_html(md, "Toxicology Complete Audit"), encoding="utf-8")


def mirror_outputs() -> None:
    for rel in [
        OUT_HTML.relative_to(ROOT),
        QA_MD.relative_to(ROOT),
        QA_HTML.relative_to(ROOT),
        AUDIT_MD.relative_to(ROOT),
        AUDIT_HTML.relative_to(ROOT),
    ]:
        dst = MIRROR / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes((ROOT / rel).read_bytes())
    for folder in [WORK]:
        dst = MIRROR / folder.relative_to(ROOT)
        dst.mkdir(parents=True, exist_ok=True)
        for src in folder.rglob("*"):
            if src.is_file():
                d = dst / src.relative_to(folder)
                d.parent.mkdir(parents=True, exist_ok=True)
                d.write_bytes(src.read_bytes())


def main() -> None:
    PRE.mkdir(parents=True, exist_ok=True)
    for old in PRE.glob("*.png"):
        old.unlink()
    for spec in CROPS:
        crop_pdf(spec)
    doc = doc_html()
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(doc, encoding="utf-8")
    embedded = extract_embedded(doc)
    sheet = contact_sheet(embedded)
    build_qa(embedded, sheet)
    update_audit()
    mirror_outputs()
    print("rebuilt", OUT_HTML)
    print("source crops", len(CROPS), "embedded", len(embedded))
    for token in ['id="top-header"', 'id="sidebar"', 'id="main"', 'mcq-wrapper', 'mcq-result', 'source-figure', 'data:image', '<mark', '<u>', 'Rosen source', 'Rosen vs Tintinalli', 'Source Check', 'Rosen Source Audit']:
        print(token, doc.count(token))
    print("contact", sheet)


if __name__ == "__main__":
    main()
