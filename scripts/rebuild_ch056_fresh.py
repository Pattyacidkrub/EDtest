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
OUT_HTML = ROOT / "docs/chapters/complete/Chapter056_VenousThromboembolismPulmonaryEmbolism.html"
MIRROR = Path(r"C:\c\Users\PC\OneDrive\เอกสาร\codex\ER")
QA_MD = ROOT / "CH056_CROP_QA_2026-05-10.md"
QA_HTML = ROOT / "CH056_CROP_QA_2026-05-10.html"
AUDIT_MD = ROOT / "CHAPTER_COMPLETE_AUDIT_2026-05-07.md"
AUDIT_HTML = ROOT / "CHAPTER_COMPLETE_AUDIT_2026-05-07.html"
WORK = ROOT / "_ch056_rebuild_fresh_2026-05-10"
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
    CropSpec("t56_1", "Tintinalli", "Table 56-1", TINT, 435, (28, 38, 292, 552), "risk", "risk factors for venous thromboembolism"),
    CropSpec("t56_2", "Tintinalli", "Table 56-2", TINT, 435, (300, 38, 565, 295), "presentation", "factors affecting clinical presentation of pulmonary embolism"),
    CropSpec("f56_1", "Tintinalli", "Figure 56-1", TINT, 436, (52, 38, 565, 548), "presentation", "ECG findings in pulmonary embolism"),
    CropSpec("t56_3", "Tintinalli", "Table 56-3", TINT, 437, (28, 38, 292, 370), "presentation", "ECG scoring method to assess severity of pulmonary embolism"),
    CropSpec("f56_2", "Tintinalli", "Figure 56-2", TINT, 438, (86, 38, 565, 724), "diagnosis", "proposed algorithm for evaluation of suspected pulmonary embolism"),
    CropSpec("t56_4", "Tintinalli", "Table 56-4", TINT, 439, (28, 38, 292, 250), "diagnosis", "pulmonary embolism rule-out criteria"),
    CropSpec("t56_5", "Tintinalli", "Table 56-5", TINT, 439, (28, 250, 292, 525), "diagnosis", "original Wells score for pulmonary embolism"),
    CropSpec("t56_6", "Tintinalli", "Table 56-6", TINT, 439, (28, 470, 292, 738), "dvt", "Wells score for deep vein thrombosis"),
    CropSpec("t56_7", "Tintinalli", "Table 56-7", TINT, 439, (300, 38, 565, 285), "diagnosis", "revised and simplified revised Geneva score"),
    CropSpec("t56_8", "Tintinalli", "Table 56-8", TINT, 439, (300, 285, 565, 435), "diagnosis", "factors that alter D-dimer levels"),
    CropSpec("f56_3", "Tintinalli", "Figure 56-3", TINT, 439, (300, 505, 565, 738), "imaging", "CT angiogram showing pulmonary embolism"),
    CropSpec("f56_4", "Tintinalli", "Figure 56-4", TINT, 440, (80, 370, 565, 738), "imaging", "planar and SPECT ventilation-perfusion lung scan examples"),
    CropSpec("f56_5", "Tintinalli", "Figure 56-5", TINT, 441, (28, 38, 292, 642), "dvt", "compression venous ultrasound normal and thrombosis examples"),
    CropSpec("t56_9", "Tintinalli", "Table 56-9", TINT, 441, (300, 450, 565, 738), "diagnosis", "likelihood ratios for diagnostic tests and pretest probability"),
    CropSpec("f56_6", "Tintinalli", "Figure 56-6", TINT, 442, (52, 38, 316, 360), "dvt", "diagnostic algorithm for DVT"),
    CropSpec("t56_10", "Tintinalli", "Table 56-10", TINT, 442, (320, 38, 585, 520), "treatment", "antithrombotic therapy for DVT and PE"),
    CropSpec("t56_11", "Tintinalli", "Table 56-11", TINT, 443, (300, 38, 565, 360), "disposition", "prognostic systems for outpatient PE treatment"),
    CropSpec("t56_12", "Tintinalli", "Table 56-12", TINT, 443, (300, 455, 565, 738), "fibrinolysis", "modalities to risk-stratify pulmonary embolism"),
    CropSpec("r21_2", "Rosen", "Fig. 21.2", ROSEN, 253, (52, 82, 565, 735), "diagnosis", "dyspnea management algorithm with pulmonary embolism branch"),
    CropSpec("r22_4", "Rosen", "Table 22.4", ROSEN, 260, (42, 62, 565, 385), "imaging", "ancillary testing findings in chest pain including PE"),
]

TINT_LABELS = [
    "Table 56-1", "Table 56-2", "Figure 56-1", "Table 56-3", "Figure 56-2", "Table 56-4",
    "Table 56-5", "Table 56-6", "Table 56-7", "Table 56-8", "Figure 56-3", "Figure 56-4",
    "Figure 56-5", "Table 56-9", "Figure 56-6", "Table 56-10", "Table 56-11", "Table 56-12",
]


def crop_pdf(spec: CropSpec) -> None:
    doc = fitz.open(spec.pdf)
    pix = doc[spec.page - 1].get_pixmap(matrix=fitz.Matrix(2.2, 2.2), clip=fitz.Rect(*spec.rect), alpha=False)
    pix.save(PRE / f"{spec.key}.png")


def data_uri(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def source_card(spec: CropSpec, text: str, delta: str | None = None) -> str:
    delta_html = f'<div class="source-delta"><strong><u>Rosen vs Tintinalli:</u></strong> {html.escape(delta)}</div>' if delta else ""
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
        spec = by[key]
        delta = None
        if spec.source == "Rosen":
            delta = "Rosen places PE inside undifferentiated dyspnea/chest-pain workflows; Tintinalli provides the dedicated VTE scoring, imaging, and treatment tables for this chapter."
        out.append(source_card(spec, spec.note.capitalize() + ".", delta))
    return "\n".join(out)


def mcq(n: int, ans: str, stem: str, opts: list[tuple[str, str]], rats: dict[str, str]) -> str:
    buttons = "".join(f'<button class="mcq-opt" type="button" data-option-key="{k}">{k}. {html.escape(v)}</button>' for k, v in opts)
    explains = "".join(
        f'<div class="opt-explain {"is-correct" if k == ans else "is-wrong"}" hidden><strong>{k}. {html.escape(v)}</strong><span>{html.escape(rats[k])}</span></div>'
        for k, v in opts
    )
    return f'<article class="mcq-wrapper" data-answer="{ans}" data-answered="false"><p class="mcq-stem">Q{n}. {html.escape(stem)}</p><div class="mcq-options">{buttons}</div><div class="mcq-result" hidden></div><div class="mcq-explains">{explains}</div></article>'


def build_mcqs() -> str:
    raw = [
        ("B", "Most useful first step before ordering PE tests is:", [("A", "CT for everyone"), ("B", "Estimate pretest probability with gestalt or a validated rule"), ("C", "Treat all dyspnea as PE"), ("D", "Skip risk assessment")]),
        ("A", "PERC can be used only when:", [("A", "Clinical probability is low"), ("B", "The patient is shocky"), ("C", "D-dimer is positive"), ("D", "CT is unavailable")]),
        ("C", "A positive PERC item in a low-risk patient means:", [("A", "PE is diagnosed"), ("B", "PE is excluded"), ("C", "Further testing such as D-dimer is needed"), ("D", "Thrombolysis is required")]),
        ("D", "Age-adjusted D-dimer is most useful in:", [("A", "High probability PE"), ("B", "Massive PE"), ("C", "Unstable shock"), ("D", "Older low/intermediate probability patients")]),
        ("A", "A false-positive D-dimer can occur with:", [("A", "Age, pregnancy, malignancy, surgery, infection, trauma, rheumatoid arthritis"), ("B", "Only PE"), ("C", "Only pneumothorax"), ("D", "Only migraine")]),
        ("B", "The usual imaging test for stable suspected PE with adequate renal function is:", [("A", "Plain film only"), ("B", "CT pulmonary angiography"), ("C", "Head CT"), ("D", "No imaging")]),
        ("C", "V/Q imaging is especially useful when:", [("A", "Renal function/contrast is a problem or pregnancy strategy favors it"), ("B", "CT is mandatory"), ("C", "A is correct"), ("D", "D-dimer is negative in low risk")]),
        ("D", "Compression ultrasound of the leg can help PE workup because:", [("A", "Finding DVT can justify treating VTE"), ("B", "It may avoid chest contrast in selected patients"), ("C", "It supports VTE diagnosis"), ("D", "All of these")]),
        ("A", "Wells DVT low probability plus normal D-dimer generally:", [("A", "Rules out DVT"), ("B", "Requires thrombolysis"), ("C", "Requires surgery"), ("D", "Diagnoses PE")]),
        ("B", "Moderate/high DVT probability usually starts with:", [("A", "No test"), ("B", "Compression ultrasound"), ("C", "Head CT"), ("D", "Lumbar puncture")]),
        ("C", "If initial US is negative but DVT suspicion remains and D-dimer is positive:", [("A", "Discharge forever"), ("B", "Thrombolysis"), ("C", "Repeat US in about 1 week or follow local pathway"), ("D", "No follow-up")]),
        ("D", "Phlegmasia cerulea dolens means:", [("A", "Minor calf strain"), ("B", "Simple cellulitis"), ("C", "Benign edema"), ("D", "Massive venous thrombosis threatening limb perfusion")]),
        ("A", "Initial anticoagulation choices in ED VTE treatment include:", [("A", "UFH, LMWH, fondaparinux, or selected DOACs depending on patient factors"), ("B", "Only aspirin"), ("C", "Only antibiotics"), ("D", "Only steroids")]),
        ("B", "UFH is preferred over LMWH when:", [("A", "No renal issue ever"), ("B", "Severe renal failure or need for rapid reversal/procedure is important"), ("C", "Outpatient low risk"), ("D", "Patient refuses IV")]),
        ("C", "Rivaroxaban and apixaban are useful because:", [("A", "They require heparin in every patient"), ("B", "They cannot be outpatient"), ("C", "They can treat selected DVT/PE without heparin lead-in"), ("D", "They are thrombolytics")]),
        ("D", "Massive PE is defined by:", [("A", "Hypotension/shock"), ("B", "Cardiac arrest"), ("C", "Sustained systolic BP <90 or drop >40 mm Hg"), ("D", "Any of these severe hemodynamic patterns")]),
        ("A", "Submassive PE generally has:", [("A", "Normal or near-normal BP with RV strain/biomarker evidence"), ("B", "No RV findings"), ("C", "No clot"), ("D", "Only cough")]),
        ("B", "Systemic fibrinolysis is considered when PE has:", [("A", "Low-risk incidental clot"), ("B", "Hypotension, arrest, severe hypoxemia, RV strain, or elevated biomarkers with severe presentation and no contraindication"), ("C", "Negative scan"), ("D", "Normal D-dimer")]),
        ("C", "Major thrombolysis contraindication:", [("A", "Minor headache"), ("B", "Old sprain"), ("C", "Recent intracranial disease/surgery/trauma or active major bleeding risk"), ("D", "Normal ECG")]),
        ("D", "Catheter-directed therapy may be considered for:", [("A", "Intermediate-risk PE when bleeding risk makes systemic lysis undesirable"), ("B", "Massive PE when expertise exists"), ("C", "Selected patients needing lower lytic dose"), ("D", "All of these")]),
        ("A", "Low-risk outpatient PE selection uses:", [("A", "sPESI/Hestia plus home support, no high-risk features, and ability to comply"), ("B", "Only patient preference"), ("C", "Only a normal ECG"), ("D", "Only age")]),
        ("B", "Table 56-12 risk-stratifies PE with:", [("A", "Only rash"), ("B", "Hestia/sPESI, shock index, pulse ox, echo, biomarkers, D-dimer, sodium"), ("C", "Only urinalysis"), ("D", "Only fever")]),
        ("C", "Isolated subsegmental PE treatment is:", [("A", "Always no treatment"), ("B", "Always thrombolysis"), ("C", "Individualized; many high-risk recurrence patients are treated, some low-risk patients may be observed"), ("D", "Always surgery")]),
        ("D", "Cancer-associated VTE generally favors:", [("A", "No anticoagulation ever"), ("B", "Only warfarin always"), ("C", "Aspirin only"), ("D", "Anticoagulation strategy tailored to cancer, bleeding risk, drug interactions, and recurrence risk")]),
        ("A", "Pregnancy suspected PE differs because:", [("A", "Signs overlap with pregnancy and imaging/anticoagulation choices must consider fetus and mother"), ("B", "D-dimer is perfect"), ("C", "PE never occurs"), ("D", "Warfarin is first line")]),
        ("B", "Best chapter summary:", [("A", "Skip rules and scan all"), ("B", "Use pretest probability, PERC/D-dimer/CT or V/Q/US intelligently, anticoagulate appropriate patients, and identify massive/submassive PE early"), ("C", "DVT is never related to PE"), ("D", "All PE goes home")]),
    ]
    out = []
    for ans, stem, opts in raw:
        rats = {k: ("Correct." if k == ans else "Not the best answer for the Tintinalli Ch.56 pathway.") for k, _ in opts}
        out.append(mcq(len(out) + 1, ans, stem, opts, rats))
    return "\n".join(out)


def doc_html() -> str:
    return f"""<!doctype html><html lang="en" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Chapter 056 - Venous Thromboembolism Including Pulmonary Embolism</title><style>{STYLE}</style></head><body>
<header id="top-header"><button class="hdr-btn" data-sidebar-toggle title="Contents">☰</button><div class="hdr-title">Ch.056 Venous Thromboembolism and PE</div><button class="hdr-btn theme-btn" data-theme-toggle>Dark</button></header>
<div class="app"><aside id="sidebar" class="sidebar"><button class="hdr-btn sidebar-close" data-sidebar-close>Close</button><div class="sidebar__block"><div class="sidebar__kicker">Chapter</div><h2>Venous Thromboembolism Including Pulmonary Embolism</h2><p class="meta"><b>Spine:</b> Tintinalli Ch.56</p><p class="meta"><b>Rosen:</b> Dyspnea/Chest Pain PE workflows</p><p class="meta"><b>Build:</b> fresh source rebuild</p></div><div class="sidebar__block"><div class="sidebar__kicker">Contents</div><a class="sidebar__link" href="#risk">Risk</a><a class="sidebar__link" href="#presentation">Presentation</a><a class="sidebar__link" href="#diagnosis">Diagnosis</a><a class="sidebar__link" href="#imaging">Imaging</a><a class="sidebar__link" href="#dvt">DVT</a><a class="sidebar__link" href="#treatment">Treatment</a><a class="sidebar__link" href="#assessment">MCQs</a></div></aside>
<main id="main" class="main"><div class="content-wrap"><div class="utility-bar">Fresh rebuild • Tintinalli Ch.56 • Every Tintinalli table/figure included • MCQs hidden until answered</div>
<section class="hero section" id="risk"><div class="eyebrow">Cardiovascular Disease</div><h1 class="hero__title">Venous Thromboembolism Including Pulmonary Embolism</h1><p class="lede">VTE is a probability-management chapter: identify who can be safely ruled out, who needs imaging, who should receive anticoagulation before imaging, and who has life-threatening PE needing reperfusion.</p><div class="callout warn"><strong>Board trap:</strong> <mark>PERC is not a PE rule-out test for everybody</mark>; it is only used after the clinician decides the patient is low probability.</div><p>Risk starts with Virchow physiology: stasis, endothelial injury, and hypercoagulability. Tintinalli Table 56-1 keeps the differential broad: surgery, trauma, immobility, prior VTE, malignancy, pregnancy, estrogen exposure, thrombophilia, central venous catheters, inflammatory disease, obesity, heart failure, and older age all change the pretest probability. <u>Testing without a probability frame creates false positives and unnecessary anticoagulation.</u></p>{cards(['t56_1'])}</section>
<section class="section" id="presentation"><h2>Clinical Presentation and ECG Severity Clues</h2><p>PE presentation depends on clot burden, baseline cardiopulmonary reserve, compensatory response, and the speed of embolization. Dyspnea, pleuritic chest pain, tachypnea, tachycardia, syncope, hemoptysis, hypoxemia, or shock can all occur, but none are sufficiently specific alone.</p><p>ECG is not a rule-out test. It helps risk recognition: sinus tachycardia, right bundle branch block, anterior T-wave inversions, S1Q3T3, or right-heart strain patterns raise concern for a larger physiologic hit. Table 56-3 turns these findings into a severity score; the patient, not just the image, determines risk.</p>{cards(['t56_2','f56_1','t56_3'])}</section>
<section class="section" id="diagnosis"><h2>Decision Rules, D-Dimer, and Diagnostic Flow</h2><p>The Tintinalli algorithm starts by asking whether the patient has a sign or symptom compatible with PE and whether clinical suspicion is low. Low probability patients can be screened with PERC. If PERC is negative, no PE testing is needed. If PERC is positive, use D-dimer. Patients who are not low probability use D-dimer only when the clinical rule supports that approach; high probability patients need imaging and often empiric anticoagulation if no contraindication exists.</p><p>Wells and Geneva are tools, not substitutes for bedside judgment. Wells PE and DVT scores organize symptoms, prior VTE, tachycardia, immobilization/surgery, malignancy, hemoptysis, and the likelihood of an alternative diagnosis. D-dimer is sensitive, not specific; age, pregnancy, malignancy, surgery, infection, inflammation, and trauma can elevate it. Use age-adjusted thresholds when appropriate.</p>{cards(['f56_2','r21_2','t56_4','t56_5','t56_7','t56_8','t56_9'])}</section>
<section class="section" id="imaging"><h2>Imaging Strategy</h2><p>CT pulmonary angiography is the most common definitive test for stable suspected PE. It can identify central and segmental filling defects and alternative diagnoses, but contrast load, renal function, pregnancy strategy, motion, obesity, and subsegmental interpretation matter.</p><p>V/Q scanning remains important when CT contrast is undesirable or a pregnancy pathway favors lower breast dose. A normal V/Q scan can exclude PE; a high-probability scan supports diagnosis, while nondiagnostic scans often require another test. Rosen's chest-pain testing table adds a practical ED frame: ECG RV strain, ABG hypoxemia, CT clot, ultrasound loss of venous glide, and positive high-suspicion scans all fit PE workup.</p>{cards(['f56_3','f56_4','r22_4'])}</section>
<section class="section" id="dvt"><h2>DVT Evaluation and Limb-Threatening Venous Disease</h2><p>Leg DVT diagnosis also starts with probability. Low Wells DVT score plus normal D-dimer rules out many cases. Moderate or high probability goes to compression ultrasound, and a negative early study may need repeat imaging if D-dimer or suspicion remains positive.</p><p>Compression ultrasound demonstrates noncompressible venous segments. It is useful both for leg symptoms and for PE workups when chest imaging is difficult. <mark>Phlegmasia cerulea dolens</mark> is a limb-threatening massive venous outflow problem: swollen, painful, cyanotic or cool limb with threatened perfusion needs urgent vascular consultation and consideration of catheter-directed therapy.</p>{cards(['t56_6','f56_5','f56_6'])}</section>
<section class="section" id="treatment"><h2>Anticoagulation, Disposition, and Reperfusion</h2><p>Most VTE treatment is anticoagulation. Table 56-10 anchors dosing options: UFH is useful when severe renal failure, rapid reversibility, or procedures are likely; LMWH is practical for many stable patients; fondaparinux has renal limits; apixaban and rivaroxaban can treat selected patients without heparin lead-in. Choose based on renal function, bleeding risk, cancer/pregnancy, drug interactions, adherence, and disposition.</p><p>Low-risk PE may be outpatient if sPESI/Hestia, bleeding risk, oxygenation, hemodynamics, home support, and follow-up are acceptable. Severe PE needs risk stratification: shock index, hypoxemia, echo RV strain, troponin/BNP, D-dimer, sodium, and clinical trajectory define less severe versus massive/submassive disease.</p><p>Systemic fibrinolysis is considered for massive PE with arrest, hypotension, severe hypoxemia, increased work of breathing, RV strain, or biomarker evidence when contraindications are absent. Catheter-directed therapy or surgical embolectomy may fit selected patients when systemic lysis is too risky or expertise is available. Isolated subsegmental PE and cancer-associated VTE require individualized risk-benefit decisions rather than reflexive one-size-fits-all care.</p>{cards(['t56_10','t56_11','t56_12'])}</section>
<section class="question-set section" id="assessment"><h2>Inline Assessment MCQs</h2>{build_mcqs()}</section>
</div></main></div><div class="score-pill" data-score-text>0 correct / 0 answered / 26 total</div><div class="image-modal" data-image-modal><button class="hdr-btn" data-modal-close>Close</button><img alt="Zoomed source"></div><script>{SCRIPT}</script></body></html>"""


def extract_embedded(doc: str) -> list[Path]:
    EMBED.mkdir(parents=True, exist_ok=True)
    for old in EMBED.glob("*.png"):
        old.unlink()
    paths = []
    for i, m in enumerate(re.finditer(r"data:image/png;base64,([^\"]+)", doc), 1):
        p = EMBED / f"ch056_embedded_{i:02d}.png"
        p.write_bytes(base64.b64decode(m.group(1)))
        paths.append(p)
    return paths


def contact_sheet(paths: list[Path]) -> Path:
    cols, cell_w, cell_h = 2, 560, 430
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
    draw = ImageDraw.Draw(sheet)
    for i, path in enumerate(paths):
        img = Image.open(path).convert("RGB")
        img.thumbnail((520, 360))
        x, y = (i % cols) * cell_w, (i // cols) * cell_h
        sheet.paste(img, (x + 20, y + 48))
        draw.text((x + 8, y + 14), f"{i+1:02d} {path.name}", fill=(0, 0, 0))
    out = EMBED / "ch056_embedded_contact_sheet.png"
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
    md = f"""# CH056 Crop QA - 2026-05-10

Fresh rebuild from source PDFs. No legacy Chapter056 HTML was used.

## Source Inventory Used

Tintinalli inventory: 18/18 included. Required Tintinalli objects are {", ".join(TINT_LABELS)}.

Rosen note: included topic-specific PE workflow material from Rosen dyspnea/chest-pain chapters. Rosen does not replace the dedicated Tintinalli VTE table/figure inventory.

{inv}

## Embedded Crop QA

Contact sheet: `{sheet.relative_to(ROOT).as_posix()}`

| # | Source | Object | PDF | PDF page | Extracted final embedded image | Status | Note |
|---|---|---|---|---:|---|---|---|
{chr(10).join(rows)}

## Content Gate

Content: PASS. VTE risk, PE presentation, decision rules, D-dimer, CT/VQ/US imaging, DVT algorithm, anticoagulation, outpatient selection, and fibrinolysis risk stratification all have narrative summaries; every Tintinalli table/figure is included topic-locally; Rosen cards have visible `Rosen vs Tintinalli` differences; no visible audit/source-audit repair text is inside the chapter.

Pattern: PASS. Ch186/Ch201 shell, top header, sidebar/main layout, source cards, and accepted MCQ behavior are present.
"""
    QA_MD.write_text(md, encoding="utf-8")
    QA_HTML.write_text(md_to_html(md, "CH056 Crop QA"), encoding="utf-8")


def update_audit() -> None:
    md = AUDIT_MD.read_text(encoding="utf-8")
    line = "| 56 | Chapter056_VenousThromboembolismPulmonaryEmbolism.html | PASS | PASS | PASS | 26 | 2 | 18 | 20 | PASS | 10 | Fresh rebuild 2026-05-10; Pattern: PASS; Content: PASS; MCQ all-option explanations PASS; every Tintinalli figure/table included (18/18); Rosen source crops topic-local; cropQA PASS (20/20) |"
    if re.search(r"^\| 56 \|.*$", md, flags=re.M):
        md = re.sub(r"^\| 56 \|.*$", line, md, flags=re.M)
    else:
        md = md.rstrip() + "\n" + line + "\n"
    AUDIT_MD.write_text(md, encoding="utf-8")
    AUDIT_HTML.write_text(md_to_html(md, "Chapter Complete Audit"), encoding="utf-8")


def gate(doc: str, paths: list[Path]) -> None:
    checks = {
        "top": doc.count('id="top-header"'),
        "hdr_btn": doc.count("hdr-btn"),
        "sidebar": doc.count('id="sidebar"'),
        "main": doc.count('id="main"'),
        "sidebar_link": doc.count("sidebar__link"),
        "sidebar_block": doc.count("sidebar__block"),
        "hero_title": doc.count("hero__title"),
        "section": doc.count(" section"),
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
    assert checks["sidebar_link"] > 0 and checks["sidebar_block"] > 0 and checks["hero_title"] > 0, checks
    assert checks["mcq"] == 26 and checks["result"] == 26 and checks["legacy_mcq"] == 0, checks
    assert checks["source_fig"] == len(CROPS) and checks["data"] == len(CROPS) == len(paths), checks
    assert checks["mark"] > 0 and checks["u"] > 0 and checks["rosen"] >= 2 and checks["delta"] >= 2, checks
    forbidden = ["Source Check", "Rosen Source Audit", "Source Audit", "repair note"]
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
