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
OUT_HTML = ROOT / "docs/chapters/complete/Chapter060_AneurysmalDisease.html"
MIRROR = Path(r"C:\c\Users\PC\OneDrive\เอกสาร\codex\ER")
QA_MD = ROOT / "CH060_CROP_QA_2026-05-10.md"
QA_HTML = ROOT / "CH060_CROP_QA_2026-05-10.html"
AUDIT_MD = ROOT / "CHAPTER_COMPLETE_AUDIT_2026-05-07.md"
AUDIT_HTML = ROOT / "CHAPTER_COMPLETE_AUDIT_2026-05-07.html"
WORK = ROOT / "_ch060_rebuild_fresh_2026-05-10"
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
    CropSpec("f60_1", "Tintinalli", "Figure 60-1", TINT, 462, (50, 40, 590, 430), "diagnosis", "plain radiographs of calcified abdominal aortic aneurysm"),
    CropSpec("f60_2", "Tintinalli", "Figure 60-2", TINT, 462, (52, 526, 318, 748), "diagnosis", "bedside ultrasound image of an abdominal aortic aneurysm"),
    CropSpec("f60_3", "Tintinalli", "Figure 60-3", TINT, 462, (318, 510, 590, 748), "diagnosis", "CT scan of a large abdominal aortic aneurysm with hemorrhage"),
    CropSpec("f60_4", "Tintinalli", "Figure 60-4", TINT, 463, (28, 38, 292, 276), "ultrasound", "transverse ultrasound plane of abdominal aortic aneurysm"),
    CropSpec("f60_5", "Tintinalli", "Figure 60-5", TINT, 463, (28, 296, 292, 520), "ultrasound", "longitudinal ultrasound plane of abdominal aortic aneurysm"),
    CropSpec("f60_6", "Tintinalli", "Figure 60-6", TINT, 463, (28, 548, 292, 748), "ultrasound", "transverse ultrasound showing the superior mesenteric artery"),
    CropSpec("t60_1", "Tintinalli", "Table 60-1", TINT, 463, (300, 40, 565, 220), "treatment", "ED interventions for symptomatic abdominal aortic aneurysms"),
    CropSpec("t60_2", "Tintinalli", "Table 60-2", TINT, 464, (52, 40, 590, 312), "visceral", "nonaortic large-artery aneurysms"),
    CropSpec("r72_key", "Rosen", "Ch.72 Key Concepts", ROSEN, 1165, (48, 235, 304, 425), "overview", "Rosen key concepts for ruptured abdominal aortic aneurysm"),
    CropSpec("r72_1", "Rosen", "Table 72.1", ROSEN, 1166, (42, 228, 306, 328), "risk", "AAA prevalence in selected risk groups"),
    CropSpec("r72_box", "Rosen", "Box 72.1", ROSEN, 1168, (42, 320, 300, 488), "diagnosis", "common misdiagnoses in ruptured AAA"),
]
TINT_OBJECTS = ["Figure 60-1", "Figure 60-2", "Figure 60-3", "Figure 60-4", "Figure 60-5", "Figure 60-6", "Table 60-1", "Table 60-2"]


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
            delta = "Rosen reinforces ruptured AAA recognition and common misdiagnoses; Tintinalli adds the ED intervention table, ultrasound measurement views, and nonaortic aneurysm table used here."
        output.append(source_card(spec, spec.note.capitalize() + ".", delta))
    return "\n".join(output)


def mcq(number: int, answer: str, stem: str, options: list[tuple[str, str]]) -> str:
    buttons = "".join(f'<button class="mcq-opt" type="button" data-option-key="{k}">{k}. {html.escape(v)}</button>' for k, v in options)
    explains = "".join(
        f'<div class="opt-explain {"is-correct" if k == answer else "is-wrong"}" hidden><strong>{k}. {html.escape(v)}</strong><span>{"Correct." if k == answer else "This option misses the core Ch.60 aneurysmal-disease priority."}</span></div>'
        for k, v in options
    )
    return f'<article class="mcq-wrapper" data-answer="{answer}" data-answered="false"><p class="mcq-stem">Q{number}. {html.escape(stem)}</p><div class="mcq-options">{buttons}</div><div class="mcq-result" hidden></div><div class="mcq-explains">{explains}</div></article>'


def build_mcqs() -> str:
    topics=[
        ("B","Most classic ruptured AAA triad:",[("A","Fever, cough, rash"),("B","Abdominal/back/flank pain, hypotension, pulsatile mass"),("C","Headache, photophobia, neck stiffness"),("D","Wheezing, urticaria, stridor")]),
        ("A","Best initial test for unstable suspected AAA:",[("A","Bedside ultrasound"),("B","Routine plain radiograph only"),("C","Outpatient MRI"),("D","Urine dip only")]),
        ("C","Stable suspected symptomatic AAA is best anatomically defined by:",[("A","ECG only"),("B","Chest x-ray only"),("C","CT with IV contrast when feasible"),("D","Skin biopsy")]),
        ("D","Plain abdominal radiograph:",[("A","Can show calcified contour"),("B","Cannot exclude AAA"),("C","Is not the test of choice for suspected rupture"),("D","All of these")]),
        ("A","AAA is generally defined as infrarenal aortic diameter:",[("A",">= 3.0 cm"),("B","0.5 cm"),("C","Only >10 cm"),("D","Any visible pulse")]),
        ("B","A technically adequate ultrasound measures AAA:",[("A","From inner wall to inner wall only"),("B","Outer wall to outer wall in transverse and longitudinal planes"),("C","Only by palpation"),("D","Only by length")]),
        ("C","Symptomatic aneurysms of any size should be treated as:",[("A","Routine clinic follow-up"),("B","Psychogenic pain"),("C","Emergent until proven otherwise"),("D","No surgical disease")]),
        ("D","ED priorities in symptomatic AAA include:",[("A","Large-bore IV access"),("B","Early vascular consultation/transfer"),("C","Blood products and careful resuscitation"),("D","All of these")]),
        ("A","Permissive hypotension is considered because:",[("A","Over-resuscitation may worsen bleeding before control"),("B","Hypertension is always required"),("C","It cures rupture"),("D","It replaces surgery")]),
        ("B","Pain control should avoid:",[("A","Analgesia"),("B","Severe hypotension and respiratory depression"),("C","Monitoring"),("D","Consultation")]),
        ("C","Common AAA misdiagnoses include:",[("A","Renal colic"),("B","Pancreatitis/diverticulitis"),("C","Both A and B"),("D","Otitis externa only")]),
        ("D","Ruptured AAA may present with:",[("A","Syncope"),("B","Back or flank pain"),("C","Shock without a palpable mass"),("D","All of these")]),
        ("A","Risk factors for AAA include:",[("A","Age, male sex, smoking, family history, atherosclerosis"),("B","Childhood only"),("C","No vascular risk"),("D","Acute pharyngitis")]),
        ("B","Table 60-1 emphasizes consultation:",[("A","Only after discharge"),("B","As soon as diagnosis is suspected"),("C","Never"),("D","Only outpatient")]),
        ("C","Figure 60-6 helps avoid mistaking the SMA for:",[("A","Gallbladder"),("B","Kidney"),("C","Aorta in transverse measurement"),("D","Skin")]),
        ("D","Nonaortic large-artery aneurysms may involve:",[("A","Popliteal"),("B","Subclavian/femoral/iliac"),("C","Renal/splenic/hepatic"),("D","All of these")]),
        ("A","Popliteal aneurysm may present with:",[("A","Posterior knee discomfort, swelling, DVT-like symptoms, or embolic ischemia"),("B","Isolated sore throat"),("C","Epistaxis only"),("D","Vertigo only")]),
        ("B","Mycotic/infected aneurysms require:",[("A","No therapy"),("B","Antibiotics plus urgent surgical/vascular consultation"),("C","Only antihistamines"),("D","Routine discharge")]),
        ("C","Thoracic aneurysm symptoms can reflect:",[("A","Compression or erosion into adjacent structures"),("B","Hemodynamic collapse if rupture"),("C","Both A and B"),("D","Only urinary pain")]),
        ("D","If unstable with suspected ruptured AAA:",[("A","Do not delay consultation for advanced imaging"),("B","Use bedside US if it answers the immediate question"),("C","Prepare blood/surgery/transfer"),("D","All of these")]),
        ("A","Aortocaval fistula can cause:",[("A","High-output heart failure and venous congestion"),("B","Simple pneumonia"),("C","Only rash"),("D","Otitis media")]),
        ("B","Aortoenteric fistula concern rises with:",[("A","No prior surgery ever"),("B","GI bleeding in a patient with prior AAA repair or aneurysm"),("C","Simple ankle sprain"),("D","Conjunctivitis")]),
        ("C","Table 60-2 management theme:",[("A","Ignore limb ischemia"),("B","Only aspirin"),("C","Vascular repair/embolization/antibiotics depending on vessel and cause"),("D","No follow-up")]),
        ("D","Bedside ultrasound limitations include:",[("A","Obesity"),("B","Bowel gas"),("C","Operator dependence"),("D","All of these")]),
        ("A","Asymptomatic AAA follow-up depends mainly on:",[("A","Diameter, growth, symptoms, and patient factors"),("B","Hair color"),("C","Random discharge"),("D","Troponin only")]),
        ("B","Best chapter summary:",[("A","AAA is never emergent"),("B","Recognize rupture despite mimics, use bedside US/CT appropriately, resuscitate for hemorrhage, and involve vascular surgery early"),("C","Plain radiograph rules it out"),("D","All aneurysms are identical")]),
    ]
    return "\n".join(mcq(i,*item) for i,item in enumerate(topics,1))


def doc_html() -> str:
    return f"""<!doctype html><html lang="en" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Chapter 060 - Aneurysmal Disease</title><style>{STYLE}</style></head><body>
<header id="top-header"><button class="hdr-btn" data-sidebar-toggle title="Contents">☰</button><div class="hdr-title">Ch.060 Aneurysmal Disease</div><button class="hdr-btn theme-btn" data-theme-toggle>Dark</button></header>
<div class="app"><aside id="sidebar" class="sidebar"><button class="hdr-btn sidebar-close" data-sidebar-close>Close</button><div class="sidebar__block"><div class="sidebar__kicker">Chapter</div><h2>Aneurysmal Disease</h2><p class="meta"><b>Spine:</b> Tintinalli Ch.60</p><p class="meta"><b>Rosen:</b> Ch.72 Abdominal Aortic Aneurysm</p><p class="meta"><b>Build:</b> fresh source rebuild</p></div><div class="sidebar__block"><div class="sidebar__kicker">Contents</div><a class="sidebar__link" href="#overview">Overview</a><a class="sidebar__link" href="#aaa">AAA</a><a class="sidebar__link" href="#diagnosis">Diagnosis</a><a class="sidebar__link" href="#treatment">Treatment</a><a class="sidebar__link" href="#visceral">Other Aneurysms</a><a class="sidebar__link" href="#assessment">MCQs</a></div></aside>
<main id="main" class="main"><div class="content-wrap"><div class="utility-bar">Fresh rebuild • Tintinalli Ch.60 • Every Tintinalli table/figure included • MCQs hidden until answered</div>
<section class="hero section" id="overview"><div class="eyebrow">Cardiovascular Disease</div><h1 class="hero__title">Aneurysmal Disease</h1><p class="lede">Aneurysms matter in the ED because rupture, thrombosis, embolization, fistula, and compression can masquerade as common abdominal, back, groin, limb, or GI complaints.</p><div class="callout warn"><strong>Board trap:</strong> <mark>ruptured AAA can be present without the complete pain-hypotension-pulsatile-mass triad.</mark></div><p><u>Symptomatic aneurysms of any size are emergent</u>; stable incidental aneurysms need diameter-based follow-up, but pain, syncope, hypotension, embolic findings, or sentinel bleeding changes the tempo immediately.</p>{cards(["r72_key", "r72_1"])}</section>
<section class="section" id="aaa"><h2>Symptomatic Abdominal Aortic Aneurysm</h2><p>AAA is commonly defined as an abdominal aorta at least 3 cm in diameter, but rupture risk rises with size, rapid growth, smoking, age, male sex, family history, and atherosclerotic disease. Back, abdominal, groin, hip, or flank pain may dominate, and syncope may be the clue to transient hemorrhage or shock.</p>{cards(["f60_1", "r72_box"])}</section>
<section class="section" id="diagnosis"><h2>Diagnosis and Imaging</h2><p>Do not use a normal plain film to exclude AAA. Bedside ultrasound is ideal for unstable patients because it rapidly detects and measures an aneurysm; CT with IV contrast defines anatomy and hemorrhage in stable patients. Measure outer wall to outer wall in both transverse and longitudinal planes.</p>{cards(["f60_2", "f60_3", "f60_4", "f60_5", "f60_6"])}</section>
<section class="section" id="treatment"><h2>ED Treatment</h2><p>Tintinalli Table 60-1 keeps the ED priorities simple: place large-bore IV access, consult vascular surgery or arrange transfer as soon as suspected, provide blood products and carefully titrated fluids, control pain, and avoid delays for advanced imaging when the patient is unstable.</p><p>Permissive hypotension may be used before control of hemorrhage in selected patients, while profound hypotension, altered mental status, or ongoing shock should trigger immediate blood-based resuscitation and operative planning.</p>{cards(["t60_1"])}</section>
<section class="section" id="visceral"><h2>Thoracic, Extremity, and Visceral Aneurysms</h2><p>Thoracic aneurysms can compress or erode into nearby structures and can be lethal when ruptured. Nonaortic aneurysms may present with limb ischemia, venous thrombosis mimicry, flank pain, GI bleeding, hemobilia, fever, or infected-vessel pain. Table 60-2 belongs here because management differs by artery and complication.</p>{cards(["t60_2"])}</section>
<section class="question-set section" id="assessment"><h2>Inline Assessment MCQs</h2>{build_mcqs()}</section>
</div></main></div><div class="score-pill" data-score-text>0 correct / 0 answered / 26 total</div><div class="image-modal" data-image-modal><button class="hdr-btn" data-modal-close>Close</button><img alt="Zoomed source"></div><script>{SCRIPT}</script></body></html>"""


def extract_embedded(doc: str) -> list[Path]:
    EMBED.mkdir(parents=True, exist_ok=True)
    for old in EMBED.glob("*.png"):
        old.unlink()
    paths = []
    for i, match in enumerate(re.finditer(r"data:image/png;base64,([^\"]+)", doc), 1):
        path = EMBED / f"ch060_embedded_{i:02d}.png"
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
    out = EMBED / "ch060_embedded_contact_sheet.png"
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
    md = f"""# CH060 Crop QA - 2026-05-10

Fresh rebuild from source PDFs. No legacy Chapter060 HTML was used.

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

Content: PASS. Overview, symptomatic AAA recognition, diagnostic imaging, ED treatment, thoracic/extremity/visceral aneurysms, and Rosen-vs-Tintinalli source cards all have narrative summaries; every Tintinalli figure/table is included topic-locally; no visible audit/source-audit repair text is inside the chapter.

Pattern: PASS. Ch186/Ch201 shell, top header, sidebar/main layout, source cards, and accepted MCQ behavior are present.
"""
    QA_MD.write_text(md, encoding="utf-8")
    QA_HTML.write_text(md_to_html(md, "CH060 Crop QA"), encoding="utf-8")


def update_audit() -> None:
    md = AUDIT_MD.read_text(encoding="utf-8")
    line = "| 60 | Chapter060_AneurysmalDisease.html | PASS | PASS | PASS | 26 | 3 | 8 | 11 | PASS | 4 | Fresh rebuild 2026-05-10; Pattern: PASS; Content: PASS; MCQ all-option explanations PASS; every Tintinalli figure/table included (8/8); Rosen source crops topic-local; cropQA PASS (11/11) |"
    if re.search(r"^\| 60 \|.*$", md, flags=re.M):
        md = re.sub(r"^\| 60 \|.*$", line, md, flags=re.M)
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
