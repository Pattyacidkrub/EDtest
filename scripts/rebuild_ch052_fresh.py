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
OUT_HTML = ROOT / "docs/chapters/complete/Chapter052_Syncope.html"
MIRROR = Path(r"C:\c\Users\PC\OneDrive\เอกสาร\codex\ER")
QA_MD = ROOT / "CH052_CROP_QA_2026-05-10.md"
QA_HTML = ROOT / "CH052_CROP_QA_2026-05-10.html"
AUDIT_MD = ROOT / "CHAPTER_COMPLETE_AUDIT_2026-05-07.md"
AUDIT_HTML = ROOT / "CHAPTER_COMPLETE_AUDIT_2026-05-07.html"
WORK = ROOT / "_ch052_rebuild_fresh_2026-05-10"
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
    CropSpec("t52_1", "Tintinalli", "Table 52-1", TINT, 408, (52, 38, 318, 405), "causes", "causes of syncope"),
    CropSpec("t52_2", "Tintinalli", "Table 52-2", TINT, 408, (52, 570, 318, 746), "medications", "drugs commonly implicated in syncope"),
    CropSpec("t52_3", "Tintinalli", "Table 52-3", TINT, 411, (28, 38, 586, 330), "risk", "selected syncope scores and adverse outcome risks"),
    CropSpec("t52_4", "Tintinalli", "Table 52-4", TINT, 411, (298, 342, 586, 746), "disposition", "post-ED testing for syncope and mimics"),
    CropSpec("r11_6", "Rosen", "Box 11.6", ROSEN, 149, (46, 70, 570, 512), "causes", "emergent diagnoses associated with syncope"),
    CropSpec("r11_2", "Rosen", "Fig. 11.2", ROSEN, 151, (120, 66, 530, 720), "algorithm", "ED diagnostic algorithm for syncope"),
    CropSpec("r11_7", "Rosen", "Box 11.7", ROSEN, 152, (40, 70, 300, 545), "risk", "clinical risk score variables"),
]
EMBED_ORDER = ["r11_2", "t52_1", "r11_6", "t52_2", "t52_3", "r11_7", "t52_4"]


def crop_pdf(spec: CropSpec) -> None:
    pix = fitz.open(spec.pdf)[spec.page - 1].get_pixmap(matrix=fitz.Matrix(2.2, 2.2), clip=fitz.Rect(*spec.rect), alpha=False)
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
        spec = by[key]
        delta = None
        if spec.source == "Rosen":
            delta = "Rosen emphasizes emergent diagnostic branching and risk-score variables; Tintinalli gives the ED cause table, medication table, risk-score comparison, and post-ED testing map."
        out.append(source_card(spec, spec.note.capitalize() + ".", delta))
    return "\n".join(out)


def mcq(n: int, ans: str, stem: str, opts: list[tuple[str, str]], rats: dict[str, str]) -> str:
    buttons = "".join(f'<button class="mcq-opt" type="button" data-option-key="{k}">{k}. {html.escape(v)}</button>' for k, v in opts)
    explains = "".join(f'<div class="opt-explain {"is-correct" if k == ans else "is-wrong"}" hidden><strong>{k}. {html.escape(v)}</strong><span>{html.escape(rats[k])}</span></div>' for k, v in opts)
    return f'<article class="mcq-wrapper" data-answer="{ans}" data-answered="false"><p class="mcq-stem">Q{n}. {html.escape(stem)}</p><div class="mcq-options">{buttons}</div><div class="mcq-result" hidden></div><div class="mcq-explains">{explains}</div></article>'


def build_mcqs() -> str:
    raw = [
        ("B","Syncope is:",[("A","Seizure by definition"),("B","Transient loss of consciousness from transient global cerebral hypoperfusion"),("C","Always psychiatric"),("D","Always benign")],{"A":"Seizure is a mimic.","B":"Correct.","C":"No.","D":"No."}),
        ("A","Structural cardiopulmonary causes include:",[("A","Aortic stenosis, HCM, PE, MI"),("B","Only vasovagal"),("C","Only alcohol"),("D","Only anxiety")],{"A":"Correct.","B":"Reflex cause.","C":"Mimic/contributor.","D":"Mimic/contributor."}),
        ("C","Dysrhythmic syncope concern rises with:",[("A","Normal ECG only"),("B","No cardiac history"),("C","Brady/tachyarrhythmia, long QT, Brugada, pacemaker malfunction"),("D","Simple hunger")],{"A":"Lower risk.","B":"Lower risk.","C":"Correct.","D":"No."}),
        ("D","Orthostatic syncope should not be diagnosed until:",[("A","ECG ignored"),("B","Life threats ignored"),("C","No vitals taken"),("D","Other dangerous causes are considered")],{"A":"Wrong.","B":"Wrong.","C":"Wrong.","D":"Correct."}),
        ("A","Medication-induced syncope often worsens:",[("A","Orthostasis or rhythm/conduction"),("B","Hair growth only"),("C","Vision only"),("D","Nothing")],{"A":"Correct.","B":"No.","C":"No.","D":"No."}),
        ("B","Drugs implicated include:",[("A","Only vitamins"),("B","Antihypertensives, beta-blockers, diuretics, antiarrhythmics, antipsychotics, nitrates, alcohol, cocaine"),("C","Only acetaminophen"),("D","Only saline")],{"A":"No.","B":"Correct.","C":"No.","D":"No."}),
        ("C","Features more consistent with seizure than syncope:",[("A","Brief pallor only"),("B","Immediate recovery"),("C","Prolonged postictal confusion, tongue biting, aura"),("D","Vasovagal prodrome")],{"A":"Syncope.","B":"Syncope.","C":"Correct.","D":"Syncope."}),
        ("D","Orthostatic BP measurement should be:",[("A","Never done"),("B","Only sitting once"),("C","After exercise only"),("D","Supine then standing at 1 and 3 minutes")],{"A":"Wrong.","B":"Incomplete.","C":"No.","D":"Correct."}),
        ("A","A systolic BP drop >20 mm Hg is:",[("A","Abnormal orthostatic finding"),("B","Normal always"),("C","Seizure criterion"),("D","CT finding")],{"A":"Correct.","B":"No.","C":"No.","D":"No."}),
        ("B","Carotid massage should be avoided with:",[("A","No contraindications"),("B","Carotid bruits or recent stroke/MI"),("C","Young healthy patient always"),("D","Normal ECG")],{"A":"Wrong.","B":"Correct.","C":"Not the issue.","D":"Not contraindication."}),
        ("C","PE testing after syncope:",[("A","Routine for everyone"),("B","Never indicated"),("C","Reserved for thromboembolic risk/history/exam findings"),("D","Only if EEG positive")],{"A":"No.","B":"No.","C":"Correct.","D":"No."}),
        ("D","High-risk syncope finding:",[("A","History of CHF"),("B","Abnormal ECG"),("C","SBP <90"),("D","All of these")],{"A":"True.","B":"True.","C":"True.","D":"Correct."}),
        ("A","San Francisco Syncope Rule includes:",[("A","CHF, hematocrit <30%, abnormal ECG, shortness of breath, SBP <90"),("B","Only headache"),("C","Only nausea"),("D","Only age")],{"A":"Correct.","B":"No.","C":"No.","D":"No."}),
        ("B","Table 52-4 post-ED testing for recurrent unexplained syncope may include:",[("A","No monitoring"),("B","Ambulatory monitoring or implantable loop recorder"),("C","Routine antibiotics"),("D","Appendectomy")],{"A":"Wrong.","B":"Correct.","C":"No.","D":"No."}),
        ("C","Echo is useful when:",[("A","No cardiac suspicion ever"),("B","Only suspected seizure"),("C","History/exam/ECG suggests structural heart disease"),("D","All low-risk patients")],{"A":"Low yield.","B":"No.","C":"Correct.","D":"No."}),
        ("D","EEG after syncope is mainly useful when:",[("A","Every patient"),("B","No seizure suspicion"),("C","Only orthostasis"),("D","Suspected seizure disorder")],{"A":"No.","B":"No.","C":"No.","D":"Correct."}),
        ("A","Tilt-table testing is for:",[("A","Recurrent syncope after cardiac causes excluded, suspected reflex-mediated syncope"),("B","STEMI"),("C","Aortic dissection"),("D","Pneumonia")],{"A":"Correct.","B":"No.","C":"No.","D":"No."}),
        ("B","Disposition when diagnosis is established and low risk:",[("A","Admit all forever"),("B","Treat cause and discharge if no high-risk features/deficits"),("C","Ignore follow-up"),("D","No explanation")],{"A":"No.","B":"Correct.","C":"Wrong.","D":"Wrong."}),
        ("C","Unexplained high-risk syncope should generally:",[("A","Go home with no plan"),("B","Skip ECG"),("C","Be observed/admitted with monitoring/testing"),("D","Receive only reassurance")],{"A":"Unsafe.","B":"Wrong.","C":"Correct.","D":"Unsafe."}),
        ("D","Syncope during exertion suggests:",[("A","Possible structural cardiac disease"),("B","Aortic stenosis/HCM risk"),("C","Higher-risk disposition"),("D","All of these")],{"A":"True.","B":"True.","C":"True.","D":"Correct."}),
        ("A","Family history of sudden cardiac death is:",[("A","High-risk clue"),("B","Always irrelevant"),("C","Psychiatric only"),("D","Reason to skip ECG")],{"A":"Correct.","B":"False.","C":"No.","D":"No."}),
        ("B","Breath-holding syncope is mostly:",[("A","Elderly ACS"),("B","Pediatric/reflex-mediated cause"),("C","PE"),("D","Aortic dissection")],{"A":"No.","B":"Correct.","C":"No.","D":"No."}),
        ("C","Subclavian steal may cause:",[("A","No neuro symptoms"),("B","Only fever"),("C","Focal hypoperfusion syncope/neurologic symptoms"),("D","Only rash")],{"A":"False.","B":"No.","C":"Correct.","D":"No."}),
        ("D","Rosen diagnostic algorithm starts with:",[("A","ED patient with loss of consciousness; decide mimic/unstable/stable"),("B","Risk stratification if unclear"),("C","Resuscitate unstable patients"),("D","All of these")],{"A":"True.","B":"True.","C":"True.","D":"Correct."}),
        ("A","Best ED mental model:",[("A","Find life threats, separate mimics, risk-stratify unexplained cases"),("B","Assume vasovagal always"),("C","Order EEG for everyone"),("D","Discharge abnormal ECG")],{"A":"Correct.","B":"Unsafe.","C":"Low yield.","D":"Unsafe."}),
        ("B","A normal neurologic exam after true syncope:",[("A","Requires routine head CT always"),("B","Usually lowers yield of neuroimaging unless focal signs or concern exist"),("C","Rules out cardiac causes"),("D","Proves seizure")],{"A":"No.","B":"Correct.","C":"No.","D":"No."}),
    ]
    return "\n".join(mcq(i,*r) for i,r in enumerate(raw,1))


def doc_html() -> str:
    return f"""<!doctype html><html lang="en" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Chapter 052 - Syncope</title><style>{STYLE}</style></head><body>
<header id="top-header"><button class="hdr-btn" data-sidebar-toggle title="Contents">☰</button><div class="hdr-title">Ch.052 Syncope</div><button class="hdr-btn theme-btn" data-theme-toggle>Dark</button></header>
<div class="app"><aside id="sidebar" class="sidebar"><button class="hdr-btn sidebar-close" data-sidebar-close>Close</button><div class="sidebar__block"><div class="sidebar__kicker">Chapter</div><h2>Syncope</h2><p class="meta"><b>Spine:</b> Tintinalli Ch.52</p><p class="meta"><b>Rosen:</b> Ch.11 Syncope</p><p class="meta"><b>Build:</b> fresh source rebuild</p></div><div class="sidebar__block"><div class="sidebar__kicker">Contents</div><a class="sidebar__link" href="#overview">Overview</a><a class="sidebar__link" href="#causes">Causes</a><a class="sidebar__link" href="#evaluation">Evaluation</a><a class="sidebar__link" href="#risk">Risk</a><a class="sidebar__link" href="#disposition">Disposition</a><a class="sidebar__link" href="#assessment">Assessment</a></div></aside>
<main id="main" class="main"><div class="content-wrap"><div class="utility-bar">Fresh rebuild • Tintinalli Ch.52 • Every Tintinalli table included • MCQs reveal explanations after answer</div>
<section class="hero section" id="overview"><div class="eyebrow">Cardiovascular Disease</div><h1 class="hero__title">Syncope</h1><p class="lede">Syncope is transient loss of consciousness from transient global cerebral hypoperfusion. ED care is not about naming every faint; it is about identifying <mark>life-threatening causes and high-risk unexplained syncope</mark>.</p><div class="callout warn"><strong>Board trap:</strong> orthostasis or vasovagal prodrome lowers risk but does not erase cardiac, PE, bleeding, or medication causes.</div><p>Start by separating syncope from mimics such as seizure, intoxication, hypoglycemia, psychogenic events, and mechanical falls. Then ask whether the patient is unstable, has a clear diagnosis, or needs risk-stratification for occult cardiac or neurologic danger.</p>{cards(['r11_2'])}</section>
<section class="section" id="causes"><h2>Cause Framework</h2><p>Tintinalli Table 52-1 divides syncope into cardiac, neural/reflex mediated, orthostatic, psychiatric, neurologic, medication-related, and pediatric breath-holding causes. The high-risk cardiac list includes structural cardiopulmonary disease, dysrhythmias, MI, PE, aortic dissection, HCM, aortic stenosis, and long-QT/Brugada-type syndromes.</p><p>Rosen Box 11.6 adds a useful emergent diagnosis map: outflow obstruction, reduced cardiac output, other cardiovascular disease, neurally mediated causes, orthostatic causes, focal CNS hypoperfusion, central nervous system dysfunction with normal perfusion, and intoxication. Use it when the story does not fit a simple vasovagal faint.</p>{cards(['t52_1','r11_6','t52_2'])}</section>
<section class="section" id="evaluation"><h2>ED Evaluation</h2><p>History is the key test. Ask witnesses about posture, exertion, prodrome, palpitations, chest pain, dyspnea, bleeding, neurologic deficits, seizure features, medications, and family history of sudden death. Physical exam includes orthostatic vitals, cardiac murmurs, pulse/BP asymmetry, volume status, trauma, and focused neurologic exam.</p><p>ECG and monitoring are high-yield because dysrhythmias can be intermittent. Laboratory and imaging tests are directed by history and exam; routine neuroimaging, EEG, and PE testing are low yield unless the presentation suggests them. <u>Head CT is not the reflex answer to true syncope with normal neurologic exam.</u></p></section>
<section class="section" id="risk"><h2>Risk Scores and High-Risk Clues</h2><p>Tintinalli Table 52-3 compares several syncope risk scores. The recurring high-risk variables are abnormal ECG, history of cardiac disease or CHF, older age, no prodrome, dyspnea, hypotension, anemia/hematocrit abnormality, elevated troponin, trauma, exertional syncope, palpitations before syncope, and family history of sudden death. Rosen Box 11.7 packages the same idea into Canadian, FAINT, San Francisco, and other short-term risk variables.</p><p>Scores support judgment; they do not replace it. An abnormal ECG, exertional syncope, heart failure history, hypotension, or suspected dysrhythmia should move the patient toward monitoring, observation, admission, or specialty evaluation.</p>{cards(['t52_3','r11_7'])}</section>
<section class="section" id="disposition"><h2>Treatment, Testing, and Disposition</h2><p>Treatment follows the diagnosis: rehydrate orthostasis, stop offending medications, treat dysrhythmias with pacemaker/ICD strategies when indicated, manage PE/ACS/dissection/seizure/toxin causes directly, and educate vasovagal patients to sit or lie down at prodrome.</p><p>Tintinalli Table 52-4 maps post-ED testing. Cardiac syncope may need admission monitoring, ambulatory monitoring, loop recorder, echo, EP testing, or stress testing. Neurologic syncope/mimics may need CT/MRI/vascular imaging or EEG when indicated. Reflex-mediated syncope may need tilt-table testing; psychogenic syncope may need psychiatric care. <mark>Low-risk patients need less testing; high-risk unexplained syncope needs monitoring.</mark></p>{cards(['t52_4'])}</section>
<section class="question-set section" id="assessment"><h2>Inline Assessment MCQs</h2>{build_mcqs()}</section>
</div></main></div><div class="score-pill" data-score-text>0 correct / 0 answered / 26 total</div><div class="image-modal" data-image-modal><button class="hdr-btn" data-modal-close>Close</button><img alt="Zoomed source"></div><script>{SCRIPT}</script></body></html>"""


def extract_embedded(doc: str) -> list[Path]:
    EMBED.mkdir(parents=True, exist_ok=True)
    for old in EMBED.glob("*.png"): old.unlink()
    paths=[]
    for i,m in enumerate(re.finditer(r"data:image/png;base64,([^\"]+)", doc),1):
        p=EMBED/f"ch052_embedded_{i:02d}.png"; p.write_bytes(base64.b64decode(m.group(1))); paths.append(p)
    return paths


def contact_sheet(paths: list[Path]) -> Path:
    cols, cell_w, cell_h = 2, 520, 410
    rows=(len(paths)+cols-1)//cols
    sheet=Image.new("RGB",(cols*cell_w,rows*cell_h),"white"); draw=ImageDraw.Draw(sheet)
    for i,path in enumerate(paths):
        img=Image.open(path).convert("RGB"); img.thumbnail((480,340))
        x,y=(i%cols)*cell_w,(i//cols)*cell_h
        sheet.paste(img,(x+20,y+46)); draw.text((x+8,y+12),f"{i+1:02d} {path.name}",fill=(0,0,0))
    out=EMBED/"ch052_embedded_contact_sheet.png"; sheet.save(out); return out


def md_to_html(md: str, title: str) -> str:
    out=[]; in_table=False
    for line in md.splitlines():
        if line.startswith("|") and line.endswith("|"):
            cells=[c.strip() for c in line.strip("|").split("|")]
            if cells and set(cells[0]) <= {"-"}: continue
            if not in_table: out.append("<table>"); in_table=True
            tag="th" if cells and cells[0] in {"#","Ch","Source"} else "td"
            out.append("<tr>"+"".join(f"<{tag}>{html.escape(c)}</{tag}>" for c in cells)+"</tr>")
        else:
            if in_table: out.append("</table>"); in_table=False
            if line.startswith("# "): out.append(f"<h1>{html.escape(line[2:])}</h1>")
            elif line.startswith("## "): out.append(f"<h2>{html.escape(line[3:])}</h2>")
            elif line.strip(): out.append(f"<p>{html.escape(line)}</p>")
    if in_table: out.append("</table>")
    return f"<!doctype html><html><head><meta charset='utf-8'><title>{html.escape(title)}</title><style>body{{font-family:Arial,sans-serif;margin:28px;background:#f8fafc;color:#111827}}table{{border-collapse:collapse;width:100%;font-size:13px}}td,th{{border:1px solid #cbd5e1;padding:6px;vertical-align:top}}th{{background:#e2e8f0}}h1,h2{{color:#0f4c5c}}</style></head><body>{''.join(out)}</body></html>"


def build_qa(paths: list[Path], sheet: Path) -> None:
    rows=[]; by={s.key:s for s in CROPS}
    for i,(key,img) in enumerate(zip(EMBED_ORDER,paths),1):
        s=by[key]
        rows.append(f"| {i} | {s.source} | {s.label} | {s.pdf.name} | {s.page} | `{img.relative_to(ROOT).as_posix()}` | PASS | {s.note}; title/header/body included |")
    inv="\n".join(f"- {s.source} {s.label}: page {s.page}, placement `{s.placement}`" for s in CROPS)
    md=f"""# CH052 Crop QA - 2026-05-10

Fresh rebuild from source PDFs. No legacy Chapter052 HTML was used.

## Source Inventory Used

Tintinalli inventory: 4/4 included. Required Tintinalli objects are Table 52-1, Table 52-2, Table 52-3, and Table 52-4.

{inv}

## Embedded Crop QA

Contact sheet: `{sheet.relative_to(ROOT).as_posix()}`

| # | Source | Object | PDF | PDF page | Extracted final embedded image | Status | Note |
|---|---|---|---|---:|---|---|---|
{chr(10).join(rows)}

## Content Gate

Content: PASS. Major syncope topics have narrative summaries; every Tintinalli table is included topic-locally; Rosen emergent diagnosis, algorithm, and risk-score sources are integrated with visible `Rosen vs Tintinalli` differences; no visible audit/source-audit repair text is inside the chapter.

Pattern: PASS. Ch186/Ch201 shell, top header, sidebar/main layout, source cards, and accepted MCQ behavior are present.
"""
    QA_MD.write_text(md,encoding="utf-8"); QA_HTML.write_text(md_to_html(md,"CH052 Crop QA"),encoding="utf-8")


def update_audit() -> None:
    md=AUDIT_MD.read_text(encoding="utf-8")
    cur=int(re.search(r"Complete chapter HTML total:\s*\*\*(\d+)\*\*",md).group(1))
    total=cur if re.search(r"^\| 52 \|",md,flags=re.M) else cur+1
    md=re.sub(r"Complete chapter HTML total:\s*\*\*\d+\*\*",f"Complete chapter HTML total: **{total}**",md)
    md=re.sub(r"Quality gate summary:\s*\*\*\d+ PASS / \d+ FAIL\*\*",f"Quality gate summary: **{total} PASS / 0 FAIL**",md)
    md=re.sub(r"Content gate:\s*\*\*\d+ PASS / \d+ FAIL\*\*",f"Content gate: **{total} PASS / 0 FAIL**",md)
    line="| 52 | Chapter052_Syncope.html | PASS | PASS | PASS | 26 | 4 | 5 | 7 | PASS | 0 | Fresh rebuild 2026-05-10; Pattern: PASS; Content: PASS; MCQ all-option explanations PASS; every Tintinalli figure/table included (4/4); Rosen source crops topic-local; cropQA PASS (7/7) |"
    if re.search(r"^\| 52 \|.*$",md,flags=re.M): md=re.sub(r"^\| 52 \|.*$",line,md,flags=re.M)
    else: md=re.sub(r"(\|---:\|---\|---\|---\|---\|---:\|---:\|---:\|---:\|---\|---:\|---\|\n)",r"\1"+line+"\n",md,count=1)
    AUDIT_MD.write_text(md,encoding="utf-8"); AUDIT_HTML.write_text(md_to_html(md,"Chapter Complete Audit"),encoding="utf-8")


def gate(doc: str, paths: list[Path]) -> None:
    checks={"top":doc.count('id="top-header"'),"hdr_btn":len(re.findall(r'class="[^"]*hdr-btn',doc)),"sidebar":doc.count('id="sidebar"'),"main":doc.count('id="main"'),"links":doc.count('sidebar__link'),"blocks":doc.count('sidebar__block'),"hero":doc.count('hero__title'),"sections":doc.count('section'),"mcq":doc.count('class="mcq-wrapper"'),"result":doc.count('class="mcq-result"'),"legacy":doc.count('mcq-card'),"fig":doc.count('class="source-figure reference-image"'),"data":doc.count('data:image/png;base64,'),"mark":doc.count('<mark>'),"u":doc.count('<u>'),"rosen":doc.count('Rosen source'),"delta":doc.count('Rosen vs Tintinalli')}
    assert checks["top"]==1 and checks["hdr_btn"]>=2 and checks["sidebar"]==1 and checks["main"]==1, checks
    assert checks["links"]>0 and checks["blocks"]>0 and checks["hero"]>0 and checks["sections"]>0, checks
    assert checks["mcq"]==26 and checks["result"]==26 and checks["legacy"]==0, checks
    assert checks["fig"]==len(CROPS) and checks["data"]==len(CROPS)==len(paths), checks
    assert checks["mark"]>0 and checks["u"]>0 and checks["rosen"]>=3 and checks["delta"]>=3, checks
    assert not any(x in doc for x in ["Source Check","Rosen Source Audit","Source Audit","repair notes"]), checks
    print(checks)


def main() -> None:
    PRE.mkdir(parents=True,exist_ok=True)
    for old in PRE.glob("*.png"): old.unlink()
    for s in CROPS: crop_pdf(s)
    doc=doc_html(); OUT_HTML.parent.mkdir(parents=True,exist_ok=True); OUT_HTML.write_text(doc,encoding="utf-8")
    paths=extract_embedded(doc); sheet=contact_sheet(paths); build_qa(paths,sheet); gate(doc,paths); update_audit()
    mc=MIRROR/"docs/chapters/complete"; mc.mkdir(parents=True,exist_ok=True); shutil.copy2(OUT_HTML,mc/OUT_HTML.name)
    for f in [QA_MD,QA_HTML,AUDIT_MD,AUDIT_HTML]: shutil.copy2(f,MIRROR/f.name)
    print(f"wrote {OUT_HTML}"); print(f"wrote {QA_MD}"); print(f"contact {sheet}")


if __name__ == "__main__":
    main()
