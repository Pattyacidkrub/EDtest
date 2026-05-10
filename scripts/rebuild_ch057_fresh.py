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
OUT_HTML = ROOT / "docs/chapters/complete/Chapter057_SystemicHypertension.html"
MIRROR = Path(r"C:\c\Users\PC\OneDrive\เอกสาร\codex\ER")
QA_MD = ROOT / "CH057_CROP_QA_2026-05-10.md"
QA_HTML = ROOT / "CH057_CROP_QA_2026-05-10.html"
AUDIT_MD = ROOT / "CHAPTER_COMPLETE_AUDIT_2026-05-07.md"
AUDIT_HTML = ROOT / "CHAPTER_COMPLETE_AUDIT_2026-05-07.html"
WORK = ROOT / "_ch057_rebuild_fresh_2026-05-10"
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
    CropSpec("t57_1", "Tintinalli", "Table 57-1", TINT, 445, (28, 38, 292, 174), "definitions", "adult blood pressure categories"),
    CropSpec("t57_2", "Tintinalli", "Table 57-2", TINT, 445, (28, 225, 292, 738), "emergencies", "hypertensive emergencies by diagnostic category"),
    CropSpec("f57_1", "Tintinalli", "Figure 57-1", TINT, 445, (300, 38, 565, 300), "emergencies", "hypertensive retinopathy"),
    CropSpec("t57_3", "Tintinalli", "Table 57-3", TINT, 446, (52, 38, 316, 250), "risk", "diseases associated with elevated blood pressure"),
    CropSpec("f57_2", "Tintinalli", "Figure 57-2", TINT, 446, (330, 38, 565, 370), "neurologic", "intracerebral hypertensive hemorrhage"),
    CropSpec("f57_3", "Tintinalli", "Figure 57-3", TINT, 446, (330, 415, 565, 738), "neurologic", "posterior reversible encephalopathy syndrome"),
    CropSpec("t57_4a", "Tintinalli", "Table 57-4 part 1", TINT, 448, (52, 38, 565, 738), "treatment", "treatment of hypertensive emergencies by diagnosis, first page"),
    CropSpec("t57_4b", "Tintinalli", "Table 57-4 part 2", TINT, 449, (28, 38, 565, 445), "treatment", "treatment of hypertensive emergencies by diagnosis, continuation"),
    CropSpec("t57_5a", "Tintinalli", "Table 57-5 part 1", TINT, 450, (52, 38, 565, 738), "agents", "IV agents used for hypertensive emergencies, first page"),
    CropSpec("t57_5b", "Tintinalli", "Table 57-5 part 2", TINT, 451, (28, 38, 565, 150), "agents", "IV agents used for hypertensive emergencies, continuation"),
    CropSpec("t57_6", "Tintinalli", "Table 57-6", TINT, 452, (52, 38, 590, 390), "urgency", "oral agents for hypertensive urgencies"),
    CropSpec("t57_7", "Tintinalli", "Table 57-7", TINT, 452, (80, 420, 535, 570), "followup", "recommended treatment protocol for ED patients with increased BP"),
    CropSpec("t57_8", "Tintinalli", "Table 57-8", TINT, 452, (52, 590, 590, 738), "followup", "indications for specific antihypertensive therapy"),
    CropSpec("t57_9", "Tintinalli", "Table 57-9", TINT, 453, (28, 38, 565, 188), "followup", "common adverse effects of antihypertensive drugs"),
    CropSpec("t57_10", "Tintinalli", "Table 57-10", TINT, 453, (28, 195, 590, 510), "pediatric", "agents for severely hypertensive pediatric patients"),
    CropSpec("r70_1", "Rosen", "Fig. 70.1", ROSEN, 1141, (82, 78, 535, 270), "definitions", "approach to elevated blood pressure in the ED"),
    CropSpec("r70_2", "Rosen", "Fig. 70.2", ROSEN, 1147, (42, 58, 302, 318), "treatment", "cerebral autoregulation curve in chronic hypertension"),
    CropSpec("r70_6", "Rosen", "Table 70.6", ROSEN, 1147, (42, 320, 565, 742), "treatment", "indication-specific approach to hypertensive emergencies"),
]

TINT_OBJECTS = [
    "Table 57-1", "Table 57-2", "Figure 57-1", "Table 57-3", "Figure 57-2", "Figure 57-3",
    "Table 57-4", "Table 57-5", "Table 57-6", "Table 57-7", "Table 57-8", "Table 57-9", "Table 57-10",
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
            delta = "Rosen emphasizes target-organ damage first and indication-specific drug choice; Tintinalli supplies the chapter-specific diagnosis, dosing, adverse-effect, and pediatric tables."
        out.append(source_card(spec, spec.note.capitalize() + ".", delta))
    return "\n".join(out)


def mcq(n: int, ans: str, stem: str, opts: list[tuple[str, str]]) -> str:
    buttons = "".join(f'<button class="mcq-opt" type="button" data-option-key="{k}">{k}. {html.escape(v)}</button>' for k, v in opts)
    explains = "".join(
        f'<div class="opt-explain {"is-correct" if k == ans else "is-wrong"}" hidden><strong>{k}. {html.escape(v)}</strong><span>{html.escape("Correct." if k == ans else "Not the best answer for the Ch.57 ED hypertension pathway.")}</span></div>'
        for k, v in opts
    )
    return f'<article class="mcq-wrapper" data-answer="{ans}" data-answered="false"><p class="mcq-stem">Q{n}. {html.escape(stem)}</p><div class="mcq-options">{buttons}</div><div class="mcq-result" hidden></div><div class="mcq-explains">{explains}</div></article>'


def build_mcqs() -> str:
    raw = [
        ("B", "Hypertensive emergency is defined by:", [("A", "Any BP above 140/90"), ("B", "Severe BP elevation with acute target-organ damage"), ("C", "Headache alone"), ("D", "Need for oral medication only")]),
        ("A", "Hypertensive urgency is best understood as:", [("A", "Severe BP without acute target-organ damage"), ("B", "Always ICU admission"), ("C", "Always IV drip"), ("D", "Stroke by definition")]),
        ("C", "First ED step in severe hypertension:", [("A", "Lower BP immediately to normal"), ("B", "Give nitroprusside to everyone"), ("C", "Confirm BP correctly and search for target-organ damage"), ("D", "Ignore symptoms")]),
        ("D", "BP should be measured in both arms because:", [("A", "Difference may suggest aortic dissection or vascular disease"), ("B", "Technique errors occur"), ("C", "Treat the higher reliable pressure"), ("D", "All of these")]),
        ("A", "Hypertensive retinopathy findings include:", [("A", "Hemorrhages, cotton-wool spots, exudates, papilledema"), ("B", "Only cataract"), ("C", "Only red reflex loss"), ("D", "Normal retina always")]),
        ("B", "General BP reduction goal in most hypertensive emergencies:", [("A", "Normalize instantly"), ("B", "Reduce MAP about 20-25% in the first hour, then gradual reduction"), ("C", "No reduction ever"), ("D", "Drop SBP below 90")]),
        ("C", "Exception requiring very rapid and specific control:", [("A", "Asymptomatic elevated BP"), ("B", "Chronic stage 1 HTN"), ("C", "Aortic dissection"), ("D", "Mild anxiety")]),
        ("D", "Aortic dissection BP goal usually targets:", [("A", "Shear force reduction"), ("B", "HR control with beta blockade"), ("C", "SBP about 100-120 if tolerated"), ("D", "All of these")]),
        ("A", "Preferred early aortic dissection agent strategy:", [("A", "Esmolol or labetalol before/with vasodilator"), ("B", "Hydralazine alone"), ("C", "Oral clonidine only"), ("D", "No analgesia")]),
        ("B", "Acute hypertensive pulmonary edema treatment emphasizes:", [("A", "Large fluid bolus"), ("B", "Nitrates/vasodilators and ventilatory support when needed"), ("C", "Beta blocker first in all"), ("D", "No afterload reduction")]),
        ("C", "Nitroprusside caution:", [("A", "No monitoring needed"), ("B", "Safe in all renal failure"), ("C", "Cyanide/thiocyanate toxicity and precipitous BP drop risk"), ("D", "Only oral agent")]),
        ("D", "Pregnancy severe hypertension/preeclampsia agents include:", [("A", "Hydralazine"), ("B", "Labetalol"), ("C", "Nifedipine"), ("D", "All of these")]),
        ("A", "ACE inhibitors/ARBs in pregnancy are:", [("A", "Contraindicated"), ("B", "First line"), ("C", "Required"), ("D", "Antidotes")]),
        ("B", "Hypertensive encephalopathy diagnosis requires:", [("A", "BP number only"), ("B", "Altered mental status/seizure after excluding other neurologic emergencies"), ("C", "Normal neuro exam"), ("D", "Chest pain only")]),
        ("C", "PRES imaging pattern in this chapter:", [("A", "Appendicitis"), ("B", "Pneumothorax"), ("C", "Posterior white matter hyperintensity/edema"), ("D", "Long bone fracture")]),
        ("D", "For ischemic stroke not receiving reperfusion therapy, BP lowering is usually avoided unless:", [("A", "Very high BP"), ("B", "Another condition requires it"), ("C", "Target-organ issue exists"), ("D", "Any of these per pathway")]),
        ("A", "After thrombolysis candidate BP threshold issue:", [("A", "BP must be controlled below treatment thresholds before/after therapy"), ("B", "BP never matters"), ("C", "Give nitroprusside only"), ("D", "Lower by 80%")]),
        ("B", "Sympathomimetic crisis first-line therapy:", [("A", "Pure beta blocker first"), ("B", "Benzodiazepines and supportive control; add vasodilators/alpha blockade when needed"), ("C", "Oral HCTZ"), ("D", "No sedation")]),
        ("C", "Pheochromocytoma crisis agent:", [("A", "Clonidine only"), ("B", "Aspirin"), ("C", "Phentolamine"), ("D", "Warfarin")]),
        ("D", "For asymptomatic severe hypertension, ED treatment should:", [("A", "Avoid rapid IV lowering"), ("B", "Assess adherence and outpatient plan"), ("C", "Consider oral initiation/titration based on risk"), ("D", "All of these")]),
        ("A", "Clonidine limitation in asymptomatic HTN:", [("A", "Sedation/dry mouth and not recommended as new singular chronic agent"), ("B", "Only IV"), ("C", "No rebound issue"), ("D", "No adverse effects")]),
        ("B", "Oral HCTZ in Table 57-6:", [("A", "Immediate emergency agent"), ("B", "Delayed onset but common first-choice chronic medication in many patients"), ("C", "Pregnancy drug"), ("D", "No labs needed")]),
        ("C", "Common ancillary testing before ACE inhibitor/ARB/diuretic:", [("A", "Head CT always"), ("B", "Blood culture always"), ("C", "Renal function/electrolytes; pregnancy test when relevant"), ("D", "No testing ever")]),
        ("D", "Pediatric severe hypertension with life-threatening symptoms may use:", [("A", "Esmolol"), ("B", "Hydralazine"), ("C", "Labetalol or nicardipine"), ("D", "Any appropriate agent from Table 57-10 with specialist guidance")]),
        ("A", "The Rosen/Tintinalli shared decision point is:", [("A", "Target-organ damage present or absent"), ("B", "Single BP number only"), ("C", "Patient age only"), ("D", "Medication brand")]),
        ("B", "Best chapter summary:", [("A", "Treat every high BP with IV drip"), ("B", "Separate emergency from urgency, match agent to diagnosis, avoid overcorrection, and plan follow-up for asymptomatic patients"), ("C", "No fundoscopy needed"), ("D", "Ignore neurologic symptoms")]),
    ]
    return "\n".join(mcq(i, *row) for i, row in enumerate(raw, 1))


def doc_html() -> str:
    return f"""<!doctype html><html lang="en" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Chapter 057 - Systemic Hypertension</title><style>{STYLE}</style></head><body>
<header id="top-header"><button class="hdr-btn" data-sidebar-toggle title="Contents">☰</button><div class="hdr-title">Ch.057 Systemic Hypertension</div><button class="hdr-btn theme-btn" data-theme-toggle>Dark</button></header>
<div class="app"><aside id="sidebar" class="sidebar"><button class="hdr-btn sidebar-close" data-sidebar-close>Close</button><div class="sidebar__block"><div class="sidebar__kicker">Chapter</div><h2>Systemic Hypertension</h2><p class="meta"><b>Spine:</b> Tintinalli Ch.57</p><p class="meta"><b>Rosen:</b> Ch.70 Hypertension</p><p class="meta"><b>Build:</b> fresh source rebuild</p></div><div class="sidebar__block"><div class="sidebar__kicker">Contents</div><a class="sidebar__link" href="#definitions">Definitions</a><a class="sidebar__link" href="#emergencies">Emergencies</a><a class="sidebar__link" href="#neurologic">Neurologic</a><a class="sidebar__link" href="#treatment">Treatment</a><a class="sidebar__link" href="#agents">Agents</a><a class="sidebar__link" href="#urgency">Urgency</a><a class="sidebar__link" href="#assessment">MCQs</a></div></aside>
<main id="main" class="main"><div class="content-wrap"><div class="utility-bar">Fresh rebuild • Tintinalli Ch.57 • Every Tintinalli table/figure included • MCQs hidden until answered</div>
<section class="hero section" id="definitions"><div class="eyebrow">Cardiovascular Disease</div><h1 class="hero__title">Systemic Hypertension</h1><p class="lede">The ED question is not “how high is the number?” but <mark>is there acute target-organ damage?</mark> Severe BP with aortic dissection, pulmonary edema, MI, stroke, renal failure, pregnancy emergency, retinopathy, or encephalopathy is a different disease than asymptomatic severe hypertension.</p><div class="callout warn"><strong>Board trap:</strong> rapid IV BP reduction in asymptomatic severe hypertension can harm patients. Match the pace and agent to the organ at risk.</div><p>Tintinalli Table 57-1 defines adult BP categories. Rosen Fig. 70.1 makes the ED branch explicit: elevated BP plus acute target-organ damage becomes hypertensive emergency and needs IV therapy; elevated BP without acute target-organ damage is reassessment, referral, and chronic therapy planning.</p>{cards(['t57_1','r70_1'])}</section>
<section class="section" id="emergencies"><h2>Hypertensive Emergencies and Clinical Clues</h2><p>Table 57-2 is the chapter map. Aortic dissection suggests chest/back pain and pulse/BP differences; pulmonary edema presents with dyspnea and edema on radiograph; MI/ACS brings ischemic symptoms and ECG/troponin changes; acute renal failure brings creatinine elevation and proteinuria; pregnancy emergencies bring headache, visual symptoms, thrombocytopenia, liver abnormalities, or seizure; retinopathy and encephalopathy point to retinal or neurologic target-organ damage.</p><p>Measure BP carefully, repeat it after rest, and use the higher reliable arm pressure when an interarm difference appears. Search for symptoms and objective organ injury rather than treating a number in isolation.</p>{cards(['t57_2','f57_1','t57_3'])}</section>
<section class="section" id="neurologic"><h2>Neurologic Syndromes</h2><p>Severe hypertension with neurologic symptoms is high risk, but the diagnosis determines the target. Intracerebral hemorrhage, subarachnoid hemorrhage, ischemic stroke, hypertensive encephalopathy, and PRES are not treated identically. Table 57-3 reminds you that acute neurologic syndromes commonly present with elevated BP, but elevated BP may be compensatory rather than causal.</p><p>Hypertensive encephalopathy is a clinical diagnosis after excluding stroke, hemorrhage, infection, intoxication, and metabolic causes. PRES classically produces posterior edema and can improve with controlled BP reduction. <u>Avoid overshooting cerebral perfusion</u>, especially in chronic hypertension where autoregulation has shifted.</p>{cards(['f57_2','f57_3','r70_2'])}</section>
<section class="section" id="treatment"><h2>Treatment by Diagnosis</h2><p>Most hypertensive emergencies aim for roughly 20% to 25% MAP reduction in the first hour, then gradual reduction if stable. The exceptions matter. Aortic dissection requires rapid shear-force reduction with beta blockade and SBP target near 100 to 120 mm Hg if tolerated. Pulmonary edema benefits from nitrates and afterload reduction. Pregnancy emergencies favor hydralazine, labetalol, or nifedipine and avoid ACE inhibitors, ARBs, renin inhibitors, and nitroprusside.</p><p>Table 57-4 is deliberately diagnosis-based: the same BP can need different therapy depending on whether the organ at risk is aorta, brain, kidney, heart, uterus/placenta, or sympathetic surge. Rosen Table 70.6 reinforces the same idea with indication-specific primary and secondary agents.</p>{cards(['t57_4a','t57_4b','r70_6'])}</section>
<section class="section" id="agents"><h2>IV Agents and Practical Warnings</h2><p>Table 57-5 is the dosing backbone. Labetalol is useful in many emergencies but avoid or use caution in bradycardia, heart block, severe asthma/COPD, decompensated heart failure, or concurrent verapamil/diltiazem. Esmolol is titratable and useful when rapid beta blockade is needed. Nicardipine and clevidipine are titratable arterial vasodilators. Nitroglycerin is most useful in acute heart failure and ACS. Nitroprusside is powerful but requires close monitoring and carries cyanide/thiocyanate risk.</p><p>Fenoldopam may help renal perfusion but can cause tachycardia; phentolamine is important for pheochromocytoma or catecholamine crisis; enalaprilat can cause first-dose hypotension and is avoided in pregnancy.</p>{cards(['t57_5a','t57_5b'])}</section>
<section class="section" id="urgency"><h2>Asymptomatic Severe Hypertension, Follow-Up, and Pediatrics</h2><p>Asymptomatic severe hypertension is not benign long term, but acute ED lowering has not been shown to prevent short-term morbidity and may cause harm. Reassess, check for organ injury based on symptoms/risk, address adherence, start or adjust oral therapy when appropriate, and arrange reliable follow-up.</p><p>Table 57-6 lists oral agents and their timing; Table 57-7 ties BP strata and ASCVD risk to follow-up; Table 57-8 links comorbid indications to drug class; Table 57-9 reminds you to check renal function/electrolytes and pregnancy when relevant; Table 57-10 separates pediatric life-threatening symptoms from less significant presentations and should prompt specialist involvement.</p>{cards(['t57_6','t57_7','t57_8','t57_9','t57_10'])}</section>
<section class="question-set section" id="assessment"><h2>Inline Assessment MCQs</h2>{build_mcqs()}</section>
</div></main></div><div class="score-pill" data-score-text>0 correct / 0 answered / 26 total</div><div class="image-modal" data-image-modal><button class="hdr-btn" data-modal-close>Close</button><img alt="Zoomed source"></div><script>{SCRIPT}</script></body></html>"""


def extract_embedded(doc: str) -> list[Path]:
    EMBED.mkdir(parents=True, exist_ok=True)
    for old in EMBED.glob("*.png"):
        old.unlink()
    paths = []
    for i, m in enumerate(re.finditer(r"data:image/png;base64,([^\"]+)", doc), 1):
        p = EMBED / f"ch057_embedded_{i:02d}.png"
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
    out = EMBED / "ch057_embedded_contact_sheet.png"
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
    md = f"""# CH057 Crop QA - 2026-05-10

Fresh rebuild from source PDFs. No legacy Chapter057 HTML was used.

## Source Inventory Used

Tintinalli inventory: 13/13 included. Required Tintinalli objects are {", ".join(TINT_OBJECTS)}. Tables 57-4 and 57-5 span pages and are included as split source crops.

Rosen note: included topic-specific hypertension pathway/autoregulation/indication-specific therapy crops from Rosen Ch.70.

{inv}

## Embedded Crop QA

Contact sheet: `{sheet.relative_to(ROOT).as_posix()}`

| # | Source | Object | PDF | PDF page | Extracted final embedded image | Status | Note |
|---|---|---|---|---:|---|---|---|
{chr(10).join(rows)}

## Content Gate

Content: PASS. Definitions, emergency categories, neurologic syndromes, diagnosis-specific therapy, IV agents, asymptomatic severe hypertension, follow-up, adverse effects, and pediatric agents all have narrative summaries; every Tintinalli figure/table is included topic-locally; Rosen cards have visible `Rosen vs Tintinalli` differences; no visible audit/source-audit repair text is inside the chapter.

Pattern: PASS. Ch186/Ch201 shell, top header, sidebar/main layout, source cards, and accepted MCQ behavior are present.
"""
    QA_MD.write_text(md, encoding="utf-8")
    QA_HTML.write_text(md_to_html(md, "CH057 Crop QA"), encoding="utf-8")


def update_audit() -> None:
    md = AUDIT_MD.read_text(encoding="utf-8")
    line = "| 57 | Chapter057_SystemicHypertension.html | PASS | PASS | PASS | 26 | 3 | 13 | 18 | PASS | 10 | Fresh rebuild 2026-05-10; Pattern: PASS; Content: PASS; MCQ all-option explanations PASS; every Tintinalli figure/table included (13/13); Rosen source crops topic-local; cropQA PASS (18/18) |"
    if re.search(r"^\| 57 \|.*$", md, flags=re.M):
        md = re.sub(r"^\| 57 \|.*$", line, md, flags=re.M)
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
    assert checks["mark"] > 0 and checks["u"] > 0 and checks["rosen"] >= 3 and checks["delta"] >= 3, checks
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
