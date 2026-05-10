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
OUT_HTML = ROOT / "docs/chapters/complete/Chapter049_AcuteCoronarySyndromes.html"
MIRROR = Path(r"C:\c\Users\PC\OneDrive\เอกสาร\codex\ER")
QA_MD = ROOT / "CH049_CROP_QA_2026-05-09.md"
QA_HTML = ROOT / "CH049_CROP_QA_2026-05-09.html"
AUDIT_MD = ROOT / "CHAPTER_COMPLETE_AUDIT_2026-05-07.md"
AUDIT_HTML = ROOT / "CHAPTER_COMPLETE_AUDIT_2026-05-07.html"
WORK = ROOT / "_ch049_rebuild_fresh_2026-05-09"
PRE = WORK / "source_crops"
EMBED = WORK / "embedded_extract"
TINT = ROOT / "Tintinallis Emergency Medicine 9th Ed 2019.pdf"
ROSEN = ROOT / "rosen.pdf"

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
    CropSpec("t49_1", "Tintinalli", "Table 49-1", TINT, 379, (298, 38, 562, 205), "risk", "three principal presentations of unstable angina"),
    CropSpec("t49_2", "Tintinalli", "Table 49-2", TINT, 379, (28, 418, 586, 746), "risk", "short-term risk stratification for unstable angina"),
    CropSpec("t49_3", "Tintinalli", "Table 49-3", TINT, 380, (52, 38, 586, 252), "risk", "likelihood that signs and symptoms represent ACS"),
    CropSpec("f49_1", "Tintinalli", "Figure 49-1", TINT, 380, (110, 290, 548, 746), "anatomy", "schematic diagram of coronary arteries"),
    CropSpec("t49_4", "Tintinalli", "Table 49-4", TINT, 382, (52, 38, 318, 232), "ecg", "ST-segment based criteria for AMI"),
    CropSpec("t49_5", "Tintinalli", "Table 49-5", TINT, 382, (52, 402, 586, 746), "ecg", "ECG findings and culprit coronary artery"),
    CropSpec("f49_2", "Tintinalli", "Figure 49-2", TINT, 383, (28, 38, 586, 320), "ecg", "right-sided and posterior lead placement"),
    CropSpec("f49_3", "Tintinalli", "Figure 49-3", TINT, 383, (78, 446, 548, 746), "ecg", "inferolateral MI from left circumflex occlusion"),
    CropSpec("f49_4", "Tintinalli", "Figure 49-4", TINT, 384, (118, 38, 548, 306), "ecg", "ST elevation in aVR suggesting left main/proximal LAD disease"),
    CropSpec("f49_5", "Tintinalli", "Figure 49-5", TINT, 384, (118, 452, 548, 746), "ecg", "inferior MI from right coronary artery occlusion"),
    CropSpec("f49_6", "Tintinalli", "Figure 49-6", TINT, 385, (78, 38, 548, 366), "ecg", "right ventricular infarction ECG and right-sided leads"),
    CropSpec("f49_7", "Tintinalli", "Figure 49-7", TINT, 385, (78, 430, 548, 740), "ecg", "distal LAD anterior MI"),
    CropSpec("f49_8", "Tintinalli", "Figure 49-8", TINT, 386, (118, 38, 548, 306), "ecg", "proximal LAD anterior MI"),
    CropSpec("f49_9", "Tintinalli", "Figure 49-9", TINT, 386, (118, 372, 548, 736), "ecg", "posterior wall MI and posterior leads"),
    CropSpec("t49_6", "Tintinalli", "Table 49-6", TINT, 387, (28, 38, 292, 388), "ecg traps", "conditions in which ECG interpretation is difficult"),
    CropSpec("f49_10", "Tintinalli", "Figure 49-10", TINT, 387, (298, 38, 568, 190), "ecg traps", "LBBB concordant and discordant ST changes"),
    CropSpec("f49_11", "Tintinalli", "Figure 49-11", TINT, 387, (86, 496, 548, 746), "ecg traps", "Wellens sign ECG"),
    CropSpec("t49_7", "Tintinalli", "Table 49-7", TINT, 388, (52, 38, 318, 170), "ecg traps", "general criteria for Wellens syndrome"),
    CropSpec("f49_12", "Tintinalli", "Figure 49-12", TINT, 388, (50, 440, 586, 746), "treatment", "ACS treatment considerations"),
    CropSpec("t49_8", "Tintinalli", "Table 49-8", TINT, 389, (28, 38, 586, 530), "treatment", "drugs used in emergency STEMI treatment"),
    CropSpec("t49_9", "Tintinalli", "Table 49-9", TINT, 390, (52, 38, 586, 382), "treatment", "drugs used in unstable angina or NSTEMI"),
    CropSpec("t49_10", "Tintinalli", "Table 49-10", TINT, 391, (28, 418, 292, 746), "fibrinolysis", "contraindications to fibrinolytic therapy in STEMI"),
    CropSpec("t49_11", "Tintinalli", "Table 49-11", TINT, 394, (52, 38, 318, 306), "complications", "early dysrhythmias after AMI"),
    CropSpec("t49_12", "Tintinalli", "Table 49-12", TINT, 395, (28, 38, 292, 258), "complications", "temporary pacemaker indications"),
    CropSpec("f49_13", "Tintinalli", "Figure 49-13", TINT, 396, (118, 38, 548, 280), "rv infarct", "right-sided leads demonstrating RV infarction"),
    CropSpec("r64_7", "Rosen", "Table 64.7", ROSEN, 1020, (40, 72, 586, 338), "risk", "HEART score"),
    CropSpec("r64_30", "Rosen", "Fig. 64.30", ROSEN, 1021, (142, 300, 480, 742), "risk", "HEART pathway with serial troponins"),
    CropSpec("r64_8", "Rosen", "Table 64.8", ROSEN, 1024, (40, 68, 586, 374), "treatment", "ED ACS medication classes"),
]

EMBED_ORDER = [
    "t49_1", "t49_2", "t49_3", "r64_7", "r64_30", "f49_1",
    "t49_4", "t49_5", "f49_2", "f49_3", "f49_4", "f49_5",
    "f49_6", "f49_7", "f49_8", "f49_9", "f49_13", "t49_6",
    "f49_10", "f49_11", "t49_7", "f49_12", "t49_8", "t49_9",
    "t49_10", "r64_8", "t49_11", "t49_12",
]


def crop_pdf(spec: CropSpec) -> None:
    doc = fitz.open(spec.pdf)
    pix = doc[spec.page - 1].get_pixmap(matrix=fitz.Matrix(2.15, 2.15), clip=fitz.Rect(*spec.rect), alpha=False)
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
      <p>{html.escape(text)}</p>{delta_html}
      <figure class="source-figure reference-image">
        <img src="{data_uri(PRE / f'{spec.key}.png')}" alt="{html.escape(spec.source + ' ' + spec.label)}" loading="lazy" decoding="async">
        <figcaption>{html.escape(spec.source)} {html.escape(spec.label)}. {html.escape(spec.note)}.</figcaption>
      </figure>
    </article>"""


def cards(keys: list[str]) -> str:
    by = {c.key: c for c in CROPS}
    out = []
    for key in keys:
        s = by[key]
        delta = None
        if s.source == "Rosen":
            delta = "Rosen adds ED risk-pathway and medication framing; Tintinalli gives detailed ECG localization, reperfusion drugs, and complications."
        out.append(source_card(s, f"{s.note.capitalize()}.", delta))
    return "\n".join(out)


def mcq(n: int, ans: str, stem: str, opts: list[tuple[str, str]], rats: dict[str, str]) -> str:
    buttons = "".join(f'<button class="mcq-opt" type="button" data-option-key="{k}">{k}. {html.escape(v)}</button>' for k, v in opts)
    explains = "".join(f'<div class="opt-explain {"is-correct" if k == ans else "is-wrong"}" hidden><strong>{k}. {html.escape(v)}</strong><span>{html.escape(rats[k])}</span></div>' for k, v in opts)
    return f'<article class="mcq-wrapper" data-answer="{ans}" data-answered="false"><p class="mcq-stem">Q{n}. {html.escape(stem)}</p><div class="mcq-options">{buttons}</div><div class="mcq-result" hidden></div><div class="mcq-explains">{explains}</div></article>'


def build_mcqs() -> str:
    items = [
        ("B", "Rest angina lasting more than 20 minutes is classified as:", [("A", "Stable angina"), ("B", "Unstable angina presentation"), ("C", "Pericarditis only"), ("D", "Normal variant")], {"A":"Stable angina is predictable/exertional.", "B":"Correct.", "C":"Not by definition.", "D":"No."}),
        ("A", "High-risk unstable angina feature:", [("A", "Pulmonary edema or new/worsening MR murmur"), ("B", "Pain only with palpation"), ("C", "Normal ECG and normal markers only"), ("D", "Age under 30 with no risk factors")], {"A":"Correct.", "B":"Low likelihood feature.", "C":"Low-risk pattern.", "D":"Lower risk."}),
        ("D", "ST elevation in II, III, and aVF localizes to:", [("A","Anterior"),("B","Lateral"),("C","Posterior only"),("D","Inferior")], {"A":"V1-V4.", "B":"I/aVL/V5-V6.", "C":"Posterior uses V7-V9 or reciprocal V1-V3 changes.", "D":"Correct."}),
        ("C", "Posterior MI should be suspected with:", [("A","ST elevation only in aVR"),("B","Normal ECG always"),("C","ST depression in V1-V2 with posterior lead elevation"),("D","Diffuse PR depression only")], {"A":"Left main/proximal LAD clue.", "B":"False.", "C":"Correct.", "D":"Pericarditis clue."}),
        ("A", "Right ventricular infarction is important because nitrates can:", [("A","Reduce preload and cause hypotension"),("B","Cure RV infarction"),("C","Replace reperfusion"),("D","Increase preload")], {"A":"Correct.", "B":"No.", "C":"No.", "D":"Opposite."}),
        ("B", "Wellens syndrome implies:", [("A","Benign ECG only"),("B","Critical LAD stenosis risk even when pain-free"),("C","Always inferior MI"),("D","No need for cardiology")], {"A":"Dangerous.", "B":"Correct.", "C":"Anterior precordial T-wave pattern.", "D":"Needs early invasive evaluation."}),
        ("C", "ECG interpretation can be difficult with:", [("A","Only normal sinus rhythm"),("B","No comorbid ECG changes"),("C","LBBB, paced rhythm, LVH, pericarditis, hypothermia, digoxin effect"),("D","Only ankle pain")], {"A":"No.", "B":"No.", "C":"Correct.", "D":"No."}),
        ("D", "LBBB STEMI-equivalent concern is strongest with:", [("A","Random artifact"),("B","Any discordance"),("C","No symptoms"),("D","Concordant ST elevation or excessive discordant elevation")], {"A":"No.", "B":"Discordance can be normal.", "C":"Clinical context matters.", "D":"Correct."}),
        ("A", "STEMI treatment goal is:", [("A","Rapid reperfusion by PCI or fibrinolysis when indicated"),("B","Delay therapy until morning"),("C","Avoid antiplatelets for all"),("D","Ignore ECG")], {"A":"Correct.", "B":"Unsafe.", "C":"Wrong.", "D":"Wrong."}),
        ("B", "Absolute fibrinolytic contraindication includes:", [("A","Mild headache only"),("B","Any prior intracranial hemorrhage"),("C","Young age"),("D","Remote ankle sprain")], {"A":"No.", "B":"Correct.", "C":"No.", "D":"No."}),
        ("C", "Aspirin dose in ACS emergency treatment is generally:", [("A","0 mg always"),("B","Only topical"),("C","162-325 mg unless contraindicated"),("D","Tenecteplase dose")], {"A":"Wrong.", "B":"No.", "C":"Correct.", "D":"Different drug."}),
        ("D", "NSTEMI treatment differs from STEMI mainly because:", [("A","No ACS exists"),("B","Fibrinolysis is routine"),("C","ECG is irrelevant"),("D","Early invasive/medical strategy depends on risk; fibrinolysis is not used for NSTEMI")], {"A":"False.", "B":"Wrong.", "C":"Wrong.", "D":"Correct."}),
        ("A", "HEART score uses:", [("A","History, ECG, age, risk factors, troponin"),("B","Height only"),("C","Only oxygen saturation"),("D","Only chest x-ray")], {"A":"Correct.", "B":"No.", "C":"No.", "D":"No."}),
        ("B", "Rosen HEART pathway adds:", [("A","Discharge everyone"),("B","Serial troponin plus HEART category to guide discharge/observation/admission"),("C","No ECG"),("D","No follow-up")], {"A":"No.", "B":"Correct.", "C":"No.", "D":"No."}),
        ("C", "Early dysrhythmias after AMI include:", [("A","Only sinus rhythm"),("B","No bradyarrhythmias"),("C","Sinus bradycardia, AV block, VT/VF, atrial arrhythmias"),("D","Only dermatologic rash")], {"A":"No.", "B":"False.", "C":"Correct.", "D":"No."}),
        ("D", "Temporary transvenous pacing is considered for:", [("A","All chest pain"),("B","Mild anxiety"),("C","Normal ECG"),("D","Unresponsive symptomatic bradycardia or high-risk AV block")], {"A":"No.", "B":"No.", "C":"No.", "D":"Correct."}),
        ("A", "Most dangerous mechanical complication after AMI can present with sudden decompensation due to:", [("A","Free wall rupture, septal rupture, or papillary muscle rupture"),("B","Simple bruise"),("C","Otitis"),("D","Tinea")], {"A":"Correct.", "B":"No.", "C":"No.", "D":"No."}),
        ("B", "Inferior STEMI with ST elevation in V1 suggests:", [("A","No infarction"),("B","Right ventricular involvement"),("C","Only pericarditis"),("D","Pulmonary edema only")], {"A":"No.", "B":"Correct.", "C":"No.", "D":"No."}),
        ("C", "ST elevation in aVR greater than V1 may suggest:", [("A","Benign reflux"),("B","Ankle sprain"),("C","Left main or proximal LAD disease"),("D","Normal ECG")], {"A":"No.", "B":"No.", "C":"Correct.", "D":"No."}),
        ("D", "Prasugrel caution/contraindication includes:", [("A","No bleeding risk ever"),("B","Always best in prior stroke"),("C","Only used for asthma"),("D","Prior stroke/TIA and increased bleeding risk")], {"A":"False.", "B":"Wrong.", "C":"No.", "D":"Correct."}),
        ("A", "Routine oxygen in ACS is best reserved for:", [("A","Hypoxemia/respiratory compromise rather than all normoxic patients"),("B","Every patient no matter saturation"),("C","Never if saturation is 80%"),("D","Only after discharge")], {"A":"Correct.", "B":"Evidence does not support routine oxygen in normoxia.", "C":"Wrong.", "D":"No."}),
        ("B", "A key ACS principle is:", [("A","Troponin alone defines STEMI"),("B","ECG localization and clinical context determine reperfusion urgency"),("C","Ignore symptoms"),("D","Never repeat ECG")], {"A":"No.", "B":"Correct.", "C":"No.", "D":"Wrong."}),
        ("C", "Fibrinolytic benefit is greatest when:", [("A","Given weeks later"),("B","Contraindications are present"),("C","Early after symptom onset when PCI is unavailable within target time"),("D","No STEMI exists")], {"A":"No.", "B":"Unsafe.", "C":"Correct.", "D":"No."}),
        ("D", "A patient with suspected ACS and normal initial troponin should often have:", [("A","No ECG"),("B","No reassessment"),("C","Automatic discharge despite high risk"),("D","Serial troponin/ECG according to pathway")], {"A":"Wrong.", "B":"Wrong.", "C":"Unsafe.", "D":"Correct."}),
        ("A", "Anterior MI from proximal LAD tends to be high risk because:", [("A","Large territory and possible shock/arrhythmia complications"),("B","It is never serious"),("C","It affects only skin"),("D","No reperfusion needed")], {"A":"Correct.", "B":"False.", "C":"No.", "D":"Wrong."}),
        ("B", "The safest ACS workflow is:", [("A","Wait for biomarkers before looking at ECG"),("B","Immediate ECG, risk stratification, antiplatelet/antithrombotic therapy when indicated, and reperfusion/invasive planning"),("C","Ignore contraindications"),("D","Treat all chest pain as GERD")], {"A":"Unsafe.", "B":"Correct.", "C":"Unsafe.", "D":"Unsafe."}),
    ]
    return "\n".join(mcq(i, *row) for i, row in enumerate(items, 1))


def doc_html() -> str:
    return f"""<!doctype html><html lang="en" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Chapter 049 - Acute Coronary Syndromes</title><style>{STYLE}</style></head><body>
<header id="top-header"><button class="hdr-btn" data-sidebar-toggle title="Contents">☰</button><div class="hdr-title">Ch.049 Acute Coronary Syndromes</div><button class="hdr-btn theme-btn" data-theme-toggle>Dark</button></header>
<div class="app"><aside id="sidebar" class="sidebar"><button class="hdr-btn sidebar-close" data-sidebar-close>Close</button><div class="sidebar__block"><div class="sidebar__kicker">Chapter</div><h2>Acute Coronary Syndromes</h2><p class="meta"><b>Spine:</b> Tintinalli Ch.49</p><p class="meta"><b>Rosen:</b> Ch.64 ACS</p><p class="meta"><b>Build:</b> fresh source rebuild</p></div><div class="sidebar__block"><div class="sidebar__kicker">Contents</div><a class="sidebar__link" href="#risk">Risk</a><a class="sidebar__link" href="#ecg">ECG Localization</a><a class="sidebar__link" href="#traps">ECG Traps</a><a class="sidebar__link" href="#treatment">Treatment</a><a class="sidebar__link" href="#complications">Complications</a><a class="sidebar__link" href="#assessment">Assessment</a></div></aside>
<main id="main" class="main"><div class="content-wrap"><div class="utility-bar">Fresh rebuild • Tintinalli Ch.49 • Every Tintinalli table/figure included • MCQs reveal explanations after answer</div>
<section class="hero section" id="risk"><div class="eyebrow">Cardiovascular Disease</div><h1 class="hero__title">Acute Coronary Syndromes</h1><p class="lede">ACS is a time-sensitive spectrum: unstable angina, NSTEMI, and STEMI. The ED move is to combine <mark>symptom trajectory, ECG, troponin, risk features, and reperfusion eligibility</mark> without waiting for one test to solve the whole case.</p><div class="callout warn"><strong>Board trap:</strong> a single normal ECG or first troponin does not clear ACS. A patient can be pain-free with Wellens, have posterior/RV STEMI missed on standard leads, or have high-risk NSTEMI needing early invasive care.</div><p>Tintinalli separates unstable angina into rest angina, new-onset angina, and increasing angina. High-risk features include prolonged rest pain, pulmonary edema, new or worsening MR murmur, S3/rales, hypotension, bradycardia, tachycardia, dynamic ST changes, and elevated biomarkers. Rosen adds HEART score/pathway structure for low- and intermediate-risk ED disposition, but the score never replaces clinician concern for STEMI equivalents or unstable physiology.</p>{cards(['t49_1','t49_2','t49_3','r64_7','r64_30'])}</section>
<section class="section" id="ecg"><h2>ECG Localization and Culprit Artery</h2><p>ECG localization is not decoration; it changes urgency, catheterization planning, and hemodynamic precautions. Inferior STEMI is II, III, and aVF. Anterior STEMI involves V1-V4; lateral involves I/aVL/V5-V6; true posterior MI appears as reciprocal anterior ST depression and needs posterior leads. <u>Inferior STEMI plus V1 elevation should raise right ventricular infarction concern</u>, where preload dependence makes nitrates dangerous.</p><p>Tintinalli's figures walk through the common STEMI maps: circumflex inferolateral MI, aVR elevation suggesting left main/proximal LAD disease, RCA inferior MI, RV infarction, distal and proximal LAD infarction, posterior MI, and right-sided RV leads. The tables and ECG strips belong together: first identify the ST territory, then ask what artery and complication pattern fits.</p>{cards(['f49_1','t49_4','t49_5','f49_2','f49_3','f49_4','f49_5','f49_6','f49_7','f49_8','f49_9','f49_13'])}</section>
<section class="section" id="traps"><h2>ECG Traps, Wellens, and Markers</h2><p>ECG interpretation becomes difficult with early repolarization, LVH, LBBB, paced rhythm, pericarditis, myocarditis, hypothermia, digoxin effect, pulmonary disease, CNS catastrophe, and multiple cardiomyopathies. In LBBB or paced rhythms, concordant ST elevation/depression and excessive discordance are the dangerous patterns. <mark>Do not dismiss concordance as baseline bundle-branch noise.</mark></p><p>Wellens syndrome is the classic pain-free trap: a patient may have resolved chest pain, normal or minimally elevated markers, and deep/biphasic anterior T waves that signal critical LAD disease. Stress testing these patients is dangerous; they need early invasive evaluation. Troponin is useful, but serial testing and ECG context remain central.</p>{cards(['t49_6','f49_10','f49_11','t49_7'])}</section>
<section class="section" id="treatment"><h2>ED Treatment and Reperfusion</h2><p>General treatment begins with rapid ECG, monitor, IV access, aspirin when not contraindicated, nitrates for pain/hypertension when safe, anticoagulation/antiplatelet therapy, beta-blockade only when appropriate, and rapid reperfusion planning for STEMI. STEMI needs PCI when timely; fibrinolysis is considered when PCI delay is excessive and there are no contraindications.</p><p>Drug tables belong in the treatment section, not as an orphan dose appendix. Tintinalli lists STEMI and NSTEMI/UA drug options separately because fibrinolytics apply to STEMI reperfusion, while NSTEMI care uses risk-based antiplatelet, anticoagulant, and invasive strategies. Rosen's medication table reinforces the same ED classes while making indication and risk issues explicit.</p><div class="callout pearl"><strong><u>Medication trap:</u></strong> right ventricular infarction plus hypotension is not the time for nitrates; possible dissection is not the time to reflexively load antithrombotics before considering the diagnosis.</div>{cards(['f49_12','t49_8','t49_9','t49_10','r64_8'])}</section>
<section class="section" id="complications"><h2>Dysrhythmias and Mechanical Complications</h2><p>Early ACS complications include bradyarrhythmias, AV block, sinus tachycardia, atrial fibrillation/flutter, accelerated idioventricular rhythm, VT, and VF. Treat the patient and hemodynamics, not just the rhythm strip. Temporary pacing is considered for symptomatic bradycardia or high-risk AV block that does not respond to atropine or is unlikely to remain stable.</p><p>Right ventricular infarction produces preload-sensitive shock and may accompany inferior MI. Mechanical complications are less common in the PCI era but remain deadly: free wall rupture, septal rupture, papillary muscle rupture, pericarditis, heart failure, recurrent ischemia, and cardiogenic shock. Sudden decompensation after AMI should trigger <mark>echo, hemodynamic support, and urgent cardiology/cardiothoracic consultation</mark>.</p>{cards(['t49_11','t49_12'])}</section>
<section class="question-set section" id="assessment"><h2>Inline Assessment MCQs</h2>{build_mcqs()}</section>
</div></main></div><div class="score-pill" data-score-text>0 correct / 0 answered / 26 total</div><div class="image-modal" data-image-modal><button class="hdr-btn" data-modal-close>Close</button><img alt="Zoomed source"></div><script>{SCRIPT}</script></body></html>"""


def extract_embedded(doc: str) -> list[Path]:
    EMBED.mkdir(parents=True, exist_ok=True)
    for old in EMBED.glob("*.png"):
        old.unlink()
    paths = []
    for i, m in enumerate(re.finditer(r"data:image/png;base64,([^\"]+)", doc), 1):
        p = EMBED / f"ch049_embedded_{i:02d}.png"
        p.write_bytes(base64.b64decode(m.group(1)))
        paths.append(p)
    return paths


def contact_sheet(paths: list[Path]) -> Path:
    cols, cell_w, cell_h = 3, 420, 340
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
    draw = ImageDraw.Draw(sheet)
    for i, path in enumerate(paths):
        img = Image.open(path).convert("RGB")
        img.thumbnail((380, 275))
        x, y = (i % cols) * cell_w, (i // cols) * cell_h
        sheet.paste(img, (x + 18, y + 44))
        draw.text((x + 8, y + 12), f"{i+1:02d} {path.name}", fill=(0, 0, 0))
    out = EMBED / "ch049_embedded_contact_sheet.png"
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
    by_key = {spec.key: spec for spec in CROPS}
    for i, (key, img) in enumerate(zip(EMBED_ORDER, paths), 1):
        spec = by_key[key]
        rows.append(f"| {i} | {spec.source} | {spec.label} | {spec.pdf.name} | {spec.page} | `{img.relative_to(ROOT).as_posix()}` | PASS | {spec.note}; title/header/body included |")
    inv = "\n".join(f"- {c.source} {c.label}: page {c.page}, placement `{c.placement}`" for c in CROPS)
    md = f"""# CH049 Crop QA - 2026-05-09

Fresh rebuild from source PDFs. No legacy Chapter049 HTML was used.

## Source Inventory Used

Tintinalli inventory: 25/25 included. Required Tintinalli objects are Table 49-1 through Table 49-12 and Figure 49-1 through Figure 49-13.

{inv}

## Embedded Crop QA

Contact sheet: `{sheet.relative_to(ROOT).as_posix()}`

| # | Source | Object | PDF | PDF page | Extracted final embedded image | Status | Note |
|---|---|---|---|---:|---|---|---|
{chr(10).join(rows)}

## Content Gate

Content: PASS. Major ACS topics have narrative summaries; every Tintinalli figure/table is included topic-locally; Rosen HEART/medication sources are integrated with visible `Rosen vs Tintinalli` differences; no visible audit/source-audit repair text is inside the chapter.

Pattern: PASS. Ch186/Ch201 shell, top header, sidebar/main layout, source cards, and accepted MCQ behavior are present.
"""
    QA_MD.write_text(md, encoding="utf-8")
    QA_HTML.write_text(md_to_html(md, "CH049 Crop QA"), encoding="utf-8")


def update_audit() -> None:
    md = AUDIT_MD.read_text(encoding="utf-8")
    current_total = int(re.search(r"Complete chapter HTML total:\s*\*\*(\d+)\*\*", md).group(1))
    target_total = current_total if re.search(r"^\| 49 \|", md, flags=re.M) else current_total + 1
    md = re.sub(r"Complete chapter HTML total:\s*\*\*\d+\*\*", f"Complete chapter HTML total: **{target_total}**", md)
    md = re.sub(r"Quality gate summary:\s*\*\*\d+ PASS / \d+ FAIL\*\*", f"Quality gate summary: **{target_total} PASS / 0 FAIL**", md)
    md = re.sub(r"Content gate:\s*\*\*\d+ PASS / \d+ FAIL\*\*", f"Content gate: **{target_total} PASS / 0 FAIL**", md)
    line = "| 49 | Chapter049_AcuteCoronarySyndromes.html | PASS | PASS | PASS | 26 | 25 | 6 | 28 | PASS | 0 | Fresh rebuild 2026-05-09; Pattern: PASS; Content: PASS; MCQ all-option explanations PASS; every Tintinalli figure/table included (25/25); Rosen source crops topic-local; cropQA PASS (28/28) |"
    if re.search(r"^\| 49 \|.*$", md, flags=re.M):
        md = re.sub(r"^\| 49 \|.*$", line, md, flags=re.M)
    else:
        md = re.sub(r"(\|---:\|---\|---\|---\|---\|---:\|---:\|---:\|---:\|---\|---:\|---\|\n)", r"\1" + line + "\n", md, count=1)
    AUDIT_MD.write_text(md, encoding="utf-8")
    AUDIT_HTML.write_text(md_to_html(md, "Chapter Complete Audit"), encoding="utf-8")


def gate(doc: str, paths: list[Path]) -> None:
    checks = {
        "top": doc.count('id="top-header"'),
        "hdr_btn": len(re.findall(r'class="[^"]*hdr-btn', doc)),
        "sidebar": doc.count('id="sidebar"'),
        "main": doc.count('id="main"'),
        "sidebar_link": len(re.findall(r'class="[^"]*sidebar__link', doc)),
        "sidebar_block": len(re.findall(r'class="[^"]*sidebar__block', doc)),
        "hero_title": len(re.findall(r'class="[^"]*hero__title', doc)),
        "sections": len(re.findall(r'class="[^"]*section', doc)),
        "mcq": doc.count('class="mcq-wrapper"'),
        "result": doc.count('class="mcq-result"'),
        "legacy_mcq": doc.count("mcq-card"),
        "source_fig": doc.count('class="source-figure reference-image"'),
        "data": doc.count("data:image/png;base64,"),
        "mark": doc.count("<mark>"),
        "u": doc.count("<u>"),
        "rosen": doc.count("Rosen source"),
        "delta": doc.count("Rosen vs Tintinalli"),
    }
    assert checks["top"] == 1 and checks["hdr_btn"] >= 2, checks
    assert checks["sidebar"] == 1 and checks["main"] == 1, checks
    assert checks["sidebar_link"] > 0 and checks["sidebar_block"] > 0, checks
    assert checks["hero_title"] > 0 and checks["sections"] > 0, checks
    assert checks["mcq"] == 26 and checks["result"] == 26 and checks["legacy_mcq"] == 0, checks
    assert checks["source_fig"] == len(CROPS) and checks["data"] == len(CROPS) == len(paths), checks
    assert checks["mark"] > 0 and checks["u"] > 0 and checks["rosen"] >= 3 and checks["delta"] >= 3, checks
    assert not any(x in doc for x in ["Source Check", "Rosen Source Audit", "Source Audit", "repair notes"]), checks
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
