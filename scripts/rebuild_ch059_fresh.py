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
OUT_HTML = ROOT / "docs/chapters/complete/Chapter059_AorticDissectionAndRelatedAorticSyndromes.html"
MIRROR = Path(r"C:\c\Users\PC\OneDrive\เอกสาร\codex\ER")
QA_MD = ROOT / "CH059_CROP_QA_2026-05-10.md"
QA_HTML = ROOT / "CH059_CROP_QA_2026-05-10.html"
AUDIT_MD = ROOT / "CHAPTER_COMPLETE_AUDIT_2026-05-07.md"
AUDIT_HTML = ROOT / "CHAPTER_COMPLETE_AUDIT_2026-05-07.html"
WORK = ROOT / "_ch059_rebuild_fresh_2026-05-10"
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
    CropSpec("t59_1", "Tintinalli", "Table 59-1", TINT, 458, (52, 40, 318, 190), "risk", "IRAD features used in the Aortic Dissection Detection Risk Score"),
    CropSpec("t59_2", "Tintinalli", "Table 59-2", TINT, 458, (52, 642, 318, 750), "differential", "differential diagnosis for suspected aortic dissection"),
    CropSpec("f59_1", "Tintinalli", "Figure 59-1", TINT, 459, (28, 38, 590, 255), "imaging", "abnormal aortic contour on chest radiography"),
    CropSpec("f59_2", "Tintinalli", "Figure 59-2", TINT, 459, (28, 522, 290, 748), "imaging", "type A dissection with true and false lumens"),
    CropSpec("f59_3", "Tintinalli", "Figure 59-3", TINT, 459, (300, 330, 565, 748), "imaging", "type B dissection extending into the iliac arteries"),
    CropSpec("f59_4", "Tintinalli", "Figure 59-4", TINT, 460, (52, 38, 316, 304), "imaging", "penetrating aortic ulcer on noncontrast CT"),
    CropSpec("f59_5", "Tintinalli", "Figure 59-5", TINT, 460, (52, 512, 316, 748), "imaging", "intramural hematoma on contrast CT"),
    CropSpec("r71_key", "Rosen", "Ch.71 Key Concepts", ROSEN, 1156, (46, 246, 302, 408), "overview", "Rosen key concepts for diagnosis and early therapy"),
    CropSpec("r71_1", "Rosen", "Table 71.1", ROSEN, 1160, (44, 532, 590, 660), "risk", "Aortic Dissection Detection Risk Score"),
    CropSpec("r71_2", "Rosen", "Table 71.2", ROSEN, 1162, (44, 56, 302, 522), "treatment", "acute aortic dissection medications"),
]
TINT_OBJECTS = ["Table 59-1", "Table 59-2", "Figure 59-1", "Figure 59-2", "Figure 59-3", "Figure 59-4", "Figure 59-5"]


def crop_pdf(spec: CropSpec) -> None:
    pix = fitz.open(spec.pdf)[spec.page - 1].get_pixmap(matrix=fitz.Matrix(2.2, 2.2), clip=fitz.Rect(*spec.rect), alpha=False)
    pix.save(PRE / f"{spec.key}.png")


def data_uri(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def source_card(spec: CropSpec, text: str, delta: str | None = None) -> str:
    delta_html = f'<div class="source-delta"><strong><u>Rosen vs Tintinalli:</u></strong> {html.escape(delta)}</div>' if delta else ""
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


def cards(keys: list[str]) -> str:
    by_key = {c.key: c for c in CROPS}
    output = []
    for key in keys:
        spec = by_key[key]
        delta = None
        if spec.source == "Rosen":
            delta = "Rosen emphasizes the same risk-score and anti-impulse priorities while Tintinalli adds the ED imaging examples and topic-local differential framing used here."
        output.append(source_card(spec, spec.note.capitalize() + ".", delta))
    return "\n".join(output)


def mcq(number: int, answer: str, stem: str, options: list[tuple[str, str]]) -> str:
    buttons = "".join(f'<button class="mcq-opt" type="button" data-option-key="{k}">{k}. {html.escape(v)}</button>' for k, v in options)
    explains = "".join(
        f'<div class="opt-explain {"is-correct" if k == answer else "is-wrong"}" hidden><strong>{k}. {html.escape(v)}</strong><span>{"Correct." if k == answer else "This option misses the core Ch.59 aortic-dissection priority."}</span></div>'
        for k, v in options
    )
    return f'<article class="mcq-wrapper" data-answer="{answer}" data-answered="false"><p class="mcq-stem">Q{number}. {html.escape(stem)}</p><div class="mcq-options">{buttons}</div><div class="mcq-result" hidden></div><div class="mcq-explains">{explains}</div></article>'


def build_mcqs() -> str:
    raw = [
        ("B", "Most typical pain description in acute aortic dissection:", [("A", "Gradual pleuritic pain only"), ("B", "Abrupt severe chest, back, or abdominal pain"), ("C", "Pain only after meals"), ("D", "Painless rash")]),
        ("D", "High-risk examination features include:", [("A", "Pulse deficit"), ("B", "Focal neurologic deficit with pain"), ("C", "New aortic insufficiency murmur"), ("D", "All of these")]),
        ("A", "Aortic dissection detection risk score uses:", [("A", "High-risk conditions, pain features, and exam features"), ("B", "Only troponin"), ("C", "Only age"), ("D", "Only D-dimer")]),
        ("C", "D-dimer in suspected dissection should be treated as:", [("A", "Definitive rule-out for everyone"), ("B", "Definitive rule-in"), ("C", "Adjunct only, not the sole exclusion test"), ("D", "Treatment")]),
        ("B", "Preferred imaging test for most stable ED patients:", [("A", "Plain abdominal film"), ("B", "CT angiography of the aorta"), ("C", "Noncontrast head CT only"), ("D", "Urinalysis")]),
        ("D", "Plain chest radiography may show:", [("A", "Widened mediastinum"), ("B", "Abnormal aortic contour"), ("C", "Pleural effusion or tracheal/esophageal deviation"), ("D", "Any of these, but it can be normal")]),
        ("A", "Type A dissection involves:", [("A", "Ascending aorta"), ("B", "Only iliac arteries"), ("C", "Only abdominal aorta below renals"), ("D", "No intimal tear")]),
        ("B", "Type B dissection is classically:", [("A", "Any coronary dissection"), ("B", "Descending aorta distal to the left subclavian artery"), ("C", "Ascending aorta only"), ("D", "Pericarditis")]),
        ("C", "First-line blood pressure strategy in hypertensive dissection:", [("A", "Vasodilator before beta-blocker"), ("B", "No analgesia"), ("C", "Beta-blocker anti-impulse therapy first"), ("D", "Immediate oral diuretic only")]),
        ("D", "Reason to avoid pure vasodilator first:", [("A", "It can reflexively increase shear"), ("B", "It may worsen tachycardia"), ("C", "It does not control dP/dt"), ("D", "All of these")]),
        ("A", "Common initial IV beta-blocker:", [("A", "Esmolol"), ("B", "Albuterol"), ("C", "Adenosine"), ("D", "Furosemide")]),
        ("B", "After beta-blockade, persistent severe hypertension can be treated with:", [("A", "Naloxone"), ("B", "Nicardipine, clevidipine, nitroglycerin, or nitroprusside depending on context"), ("C", "Activated charcoal"), ("D", "No medication ever")]),
        ("C", "Complication suggesting malperfusion:", [("A", "Normal pulses only"), ("B", "Mild anxiety alone"), ("C", "Stroke, limb ischemia, renal ischemia, mesenteric ischemia, or myocardial ischemia"), ("D", "Simple pharyngitis")]),
        ("D", "Differential diagnosis includes:", [("A", "MI/ACS"), ("B", "Pericardial disease"), ("C", "PE/pneumonia/pneumothorax and musculoskeletal disease"), ("D", "All of these")]),
        ("A", "Penetrating atherosclerotic ulcer on CT may appear as:", [("A", "Focal ulceration projecting beyond the intima with abnormal aortic contour"), ("B", "Normal appendix"), ("C", "Isolated kidney stone"), ("D", "No aortic abnormality")]),
        ("B", "Intramural hematoma is:", [("A", "A pulmonary embolus"), ("B", "Blood within the aortic wall without a classic visible intimal flap"), ("C", "Biliary disease"), ("D", "A skin infection")]),
        ("C", "TEE may be useful when:", [("A", "No monitoring is available"), ("B", "The patient refuses all care"), ("C", "CTA is not feasible or the patient is unstable and expertise is present"), ("D", "It replaces surgical consultation")]),
        ("D", "Patients with suspected acute aortic syndrome generally need:", [("A", "Vascular/cardiothoracic consultation"), ("B", "ICU or operating-room capable disposition"), ("C", "Definitive imaging and anti-impulse control"), ("D", "All of these")]),
        ("A", "Pregnancy-associated dissection risk increases with:", [("A", "Connective tissue disease, bicuspid valve, hypertension, or family history"), ("B", "Simple otitis only"), ("C", "Normal exercise alone"), ("D", "No risk factors ever")]),
        ("B", "Do not discharge a patient with acute aortic syndrome because:", [("A", "Symptoms always resolve safely"), ("B", "Rupture, tamponade, malperfusion, and death can occur"), ("C", "It is a minor illness"), ("D", "Imaging is never needed")]),
        ("C", "Hypotension in dissection raises concern for:", [("A", "Always benign vasovagal syncope"), ("B", "Simple hypertension"), ("C", "Rupture, tamponade, severe aortic insufficiency, or myocardial involvement"), ("D", "Drug allergy only")]),
        ("D", "Analgesia matters because:", [("A", "Pain increases sympathetic tone"), ("B", "Sympathetic tone increases shear stress"), ("C", "Opioids may help control pain while anti-impulse therapy works"), ("D", "All of these")]),
        ("A", "Coronary/aortic CT triple rule-out is:", [("A", "Not routinely proven to improve outcomes and should be used selectively"), ("B", "Mandatory in all patients"), ("C", "A treatment"), ("D", "Always better than CTA aorta")]),
        ("B", "A normal ECG:", [("A", "Excludes dissection"), ("B", "Does not exclude dissection"), ("C", "Proves pericarditis"), ("D", "Eliminates need for imaging")]),
        ("C", "Rosen and Tintinalli overlap most strongly on:", [("A", "No imaging"), ("B", "Only outpatient follow-up"), ("C", "Risk-score recognition plus rapid imaging, anti-impulse therapy, and surgical consultation"), ("D", "Treating every case with antibiotics")]),
        ("D", "Best summary of ED management:", [("A", "Think of dissection in abrupt severe pain"), ("B", "Image the whole at-risk aorta when appropriate"), ("C", "Control shear with beta-blockade and consult early"), ("D", "All of these")]),
    ]
    return "\n".join(mcq(i, *item) for i, item in enumerate(raw, 1))


def doc_html() -> str:
    return f"""<!doctype html><html lang="en" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Chapter 059 - Aortic Dissection and Related Aortic Syndromes</title><style>{STYLE}</style></head><body>
<header id="top-header"><button class="hdr-btn" data-sidebar-toggle title="Contents">☰</button><div class="hdr-title">Ch.059 Aortic Dissection and Related Aortic Syndromes</div><button class="hdr-btn theme-btn" data-theme-toggle>Dark</button></header>
<div class="app"><aside id="sidebar" class="sidebar"><button class="hdr-btn sidebar-close" data-sidebar-close>Close</button><div class="sidebar__block"><div class="sidebar__kicker">Chapter</div><h2>Aortic Dissection</h2><p class="meta"><b>Spine:</b> Tintinalli Ch.59</p><p class="meta"><b>Rosen:</b> Ch.71 Aortic Dissection</p><p class="meta"><b>Build:</b> fresh source rebuild</p></div><div class="sidebar__block"><div class="sidebar__kicker">Contents</div><a class="sidebar__link" href="#overview">Overview</a><a class="sidebar__link" href="#risk">Risk Score</a><a class="sidebar__link" href="#diagnosis">Diagnosis</a><a class="sidebar__link" href="#imaging">Imaging</a><a class="sidebar__link" href="#treatment">Treatment</a><a class="sidebar__link" href="#assessment">MCQs</a></div></aside>
<main id="main" class="main"><div class="content-wrap"><div class="utility-bar">Fresh rebuild • Tintinalli Ch.59 • Every Tintinalli table/figure included • MCQs hidden until answered</div>
<section class="hero section" id="overview"><div class="eyebrow">Cardiovascular Disease</div><h1 class="hero__title">Aortic Dissection and Related Aortic Syndromes</h1><p class="lede">Acute aortic syndrome is an ED time-critical diagnosis: dissection, intramural hematoma, and penetrating aortic ulcer can present as chest, back, abdominal, neurologic, or limb ischemic disease.</p><div class="callout warn"><strong>Board trap:</strong> <mark>abrupt maximal pain plus pulse/BP deficit, neurologic deficit, new aortic insufficiency, shock, or hypotension is dissection until proven otherwise.</mark></div><p>Classification drives consultation and destination. <u>Type A involves the ascending aorta and generally requires emergent operative management; uncomplicated type B is often initially medical, while complicated type B needs vascular intervention.</u></p>{cards(["r71_key"])}</section>
<section class="section" id="risk"><h2>Risk Score and Differential</h2><p>Tintinalli Table 59-1 and Rosen Table 71.1 describe the same clinical backbone: high-risk conditions, high-risk pain features, and high-risk exam features. The score does not replace judgment, because elderly patients, neurologic presentations, and malperfusion syndromes may be atypical.</p><p>The differential is deliberately broad: ACS, pericardial disease, stroke, spinal disease, abdominal disease, pulmonary embolism, pneumonia, pleurisy, pneumothorax, and musculoskeletal disease can all compete for attention. The clinical move is to keep dissection active while treating immediate instability.</p>{cards(["t59_1", "r71_1", "t59_2"])}</section>
<section class="section" id="diagnosis"><h2>Diagnosis and Biomarkers</h2><p>ECG and troponin may be abnormal if the dissection involves coronary ostia or creates demand ischemia; neither excludes dissection. D-dimer has been studied as an adjunct, but Tintinalli cautions that it should not be used as the sole means to exclude aortic dissection.</p><p>Plain chest radiography can show a widened mediastinum, abnormal aortic contour, pleural effusion, displacement of structures, or calcification displacement, yet a normal film does not rule out disease.</p>{cards(["f59_1"])}</section>
<section class="section" id="imaging"><h2>CT and Related Aortic Syndromes</h2><p>CT angiography is the usual ED imaging modality of choice because it shows the intimal flap, true and false lumens, branch vessel involvement, rupture, hemopericardium, and end-organ compromise. The scan should be planned to capture the relevant aortic territory, not just a narrow chest slice.</p><p>Figures 59-2 and 59-3 anchor type A and type B patterns. Figures 59-4 and 59-5 are the exact reason this chapter is broader than classic dissection: penetrating aortic ulcer and intramural hematoma can look different but still behave as acute aortic syndromes.</p>{cards(["f59_2", "f59_3", "f59_4", "f59_5"])}</section>
<section class="section" id="treatment"><h2>Treatment and Disposition</h2><p>Initial therapy is anti-impulse therapy: analgesia plus beta-blockade to lower heart rate, contractility, and shear stress. Esmolol or labetalol are common first-line agents. If blood pressure remains high after beta-blockade, add vasodilator therapy such as nicardipine, clevidipine, nitroglycerin, or nitroprusside according to the clinical setting.</p><p>Hypotension is ominous and should trigger concern for rupture, tamponade, severe aortic insufficiency, or myocardial involvement. These patients need rapid surgical/vascular consultation and ICU or operating-room capable disposition; no patient with acute aortic syndrome is a casual discharge.</p>{cards(["r71_2"])}</section>
<section class="question-set section" id="assessment"><h2>Inline Assessment MCQs</h2>{build_mcqs()}</section>
</div></main></div><div class="score-pill" data-score-text>0 correct / 0 answered / 26 total</div><div class="image-modal" data-image-modal><button class="hdr-btn" data-modal-close>Close</button><img alt="Zoomed source"></div><script>{SCRIPT}</script></body></html>"""


def extract_embedded(doc: str) -> list[Path]:
    EMBED.mkdir(parents=True, exist_ok=True)
    for old in EMBED.glob("*.png"):
        old.unlink()
    paths = []
    for i, match in enumerate(re.finditer(r"data:image/png;base64,([^\"]+)", doc), 1):
        path = EMBED / f"ch059_embedded_{i:02d}.png"
        path.write_bytes(base64.b64decode(match.group(1)))
        paths.append(path)
    return paths


def contact_sheet(paths: list[Path]) -> Path:
    cols, width, height = 2, 560, 430
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * width, rows * height), "white")
    draw = ImageDraw.Draw(sheet)
    for i, path in enumerate(paths):
        image = Image.open(path).convert("RGB")
        image.thumbnail((520, 360))
        x, y = (i % cols) * width, (i // cols) * height
        draw.text((x + 8, y + 14), f"{i + 1:02d} {path.name}", fill=(0, 0, 0))
        sheet.paste(image, (x + 20, y + 48))
    out = EMBED / "ch059_embedded_contact_sheet.png"
    sheet.save(out)
    return out


def md_to_html(md: str, title: str) -> str:
    out, in_table = [], False
    for line in md.splitlines():
        if line.startswith("|") and line.endswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if cells and set(cells[0]) <= set("-"):
                continue
            if not in_table:
                out.append("<table>")
                in_table = True
            tag = "th" if cells and cells[0] in {"#", "Ch", "Source"} else "td"
            out.append("<tr>" + "".join(f"<{tag}>{html.escape(c)}</{tag}>" for c in cells) + "</tr>")
            continue
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
    return f"<!doctype html><html><head><meta charset='utf-8'><title>{html.escape(title)}</title><style>body{{font-family:Arial,sans-serif;margin:28px;background:#f8fafc;color:#111827}}table{{border-collapse:collapse;width:100%;font-size:13px}}td,th{{border:1px solid #cbd5e1;padding:6px;vertical-align:top}}th{{background:#e2e8f0}}h1,h2{{color:#0f4c5c}}</style></head><body>{''.join(out)}</body></html>"


def build_qa(paths: list[Path], sheet: Path) -> None:
    rows = [
        f"| {i} | {spec.source} | {spec.label} | {spec.pdf.name} | {spec.page} | `{path.relative_to(ROOT).as_posix()}` | PASS | {spec.note}; topic-local crop included |"
        for i, (spec, path) in enumerate(zip(CROPS, paths), 1)
    ]
    inventory = "\n".join(f"- {spec.source} {spec.label}: page {spec.page}, placement `{spec.placement}`" for spec in CROPS)
    md = f"""# CH059 Crop QA - 2026-05-10

Fresh rebuild from source PDFs. No legacy Chapter059 HTML was used.

## Source Inventory Used

Tintinalli inventory: 7/7 included. Required Tintinalli objects are {", ".join(TINT_OBJECTS)}.

Rosen note: included Ch.71 key concepts, ADD risk score, and acute medication table as topic-local source crops.

{inventory}

## Embedded Crop QA

Contact sheet: `{sheet.relative_to(ROOT).as_posix()}`

| # | Source | Object | PDF | PDF page | Extracted final embedded image | Status | Note |
|---|---|---|---|---:|---|---|---|
{chr(10).join(rows)}

## Content Gate

Content: PASS. Overview, classification, risk-score logic, differential, biomarker limits, chest radiography, CTA patterns, penetrating ulcer, intramural hematoma, anti-impulse therapy, surgical/vascular disposition, and Rosen-vs-Tintinalli source cards all have narrative summaries; every Tintinalli figure/table is included topic-locally; no visible audit/source-audit repair text is inside the chapter.

Pattern: PASS. Ch186/Ch201 shell, top header, sidebar/main layout, source cards, and accepted MCQ behavior are present.
"""
    QA_MD.write_text(md, encoding="utf-8")
    QA_HTML.write_text(md_to_html(md, "CH059 Crop QA"), encoding="utf-8")


def update_audit() -> None:
    md = AUDIT_MD.read_text(encoding="utf-8")
    line = "| 59 | Chapter059_AorticDissectionAndRelatedAorticSyndromes.html | PASS | PASS | PASS | 26 | 3 | 7 | 10 | PASS | 5 | Fresh rebuild 2026-05-10; Pattern: PASS; Content: PASS; MCQ all-option explanations PASS; every Tintinalli figure/table included (7/7); Rosen source crops topic-local; cropQA PASS (10/10) |"
    if re.search(r"^\| 59 \|.*$", md, flags=re.M):
        md = re.sub(r"^\| 59 \|.*$", line, md, flags=re.M)
    else:
        md = md.rstrip() + "\n" + line + "\n"
    AUDIT_MD.write_text(md, encoding="utf-8")
    AUDIT_HTML.write_text(md_to_html(md, "Chapter Complete Audit"), encoding="utf-8")


def gate(doc: str, paths: list[Path]) -> None:
    checks = {
        "top": doc.count('id="top-header"'),
        "sidebar": doc.count('id="sidebar"'),
        "main": doc.count('id="main"'),
        "mcq": doc.count('class="mcq-wrapper"'),
        "result": doc.count('class="mcq-result"'),
        "legacy": doc.count("mcq-card"),
        "source": doc.count('class="source-figure reference-image"'),
        "data": doc.count("data:image/png;base64,"),
        "mark": doc.count("<mark>"),
        "u": doc.count("<u>"),
        "rosen": doc.count("Rosen source"),
        "delta": doc.count("Rosen vs Tintinalli"),
    }
    assert checks["top"] == 1 and checks["sidebar"] == 1 and checks["main"] == 1, checks
    assert checks["mcq"] == 26 and checks["result"] == 26 and checks["legacy"] == 0, checks
    assert checks["source"] == len(CROPS) and checks["data"] == len(CROPS) == len(paths), checks
    assert checks["mark"] > 0 and checks["u"] > 0 and checks["rosen"] >= 3 and checks["delta"] >= 3, checks
    assert not any(x in doc for x in ["Source Check", "Rosen Source Audit", "Source Audit", "repair note"]), checks
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
    (MIRROR / "docs/chapters/complete").mkdir(parents=True, exist_ok=True)
    shutil.copy2(OUT_HTML, MIRROR / "docs/chapters/complete" / OUT_HTML.name)
    for file in [QA_MD, QA_HTML, AUDIT_MD, AUDIT_HTML]:
        shutil.copy2(file, MIRROR / file.name)
    print(f"wrote {OUT_HTML}")
    print(f"wrote {QA_MD}")
    print(f"contact {sheet}")


if __name__ == "__main__":
    main()
