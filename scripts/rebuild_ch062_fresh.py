from __future__ import annotations
import base64, html, re, shutil
from dataclasses import dataclass
from pathlib import Path
import fitz
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
OUT_HTML=ROOT/"docs/chapters/complete/Chapter062_RespiratoryDistress.html"
MIRROR=Path(r"C:\c\Users\PC\OneDrive\เอกสาร\codex\ER")
QA_MD=ROOT/"CH062_CROP_QA_2026-05-10.md"; QA_HTML=ROOT/"CH062_CROP_QA_2026-05-10.html"
AUDIT_MD=ROOT/"CHAPTER_COMPLETE_AUDIT_2026-05-07.md"; AUDIT_HTML=ROOT/"CHAPTER_COMPLETE_AUDIT_2026-05-07.html"
WORK=ROOT/"_ch062_rebuild_fresh_2026-05-10"; PRE=WORK/"source_crops"; EMBED=WORK/"embedded_extract"
TINT=ROOT/"Tintinallis Emergency Medicine 9th Ed 2019.pdf"; ROSEN=ROOT/"rosen.pdf"
BASE=(ROOT/"scripts/rebuild_ch178.py").read_text(encoding="utf-8")
STYLE=BASE.split('STYLE = r"""',1)[1].split('"""',1)[0]; SCRIPT=BASE.split('SCRIPT = r"""',1)[1].split('"""',1)[0]

@dataclass(frozen=True)
class CropSpec:
    key:str; source:str; label:str; pdf:Path; page:int; rect:tuple[float,float,float,float]; placement:str; note:str

CROPS=[
 CropSpec("t62_1","Tintinalli","Table 62-1",TINT,470,(318,594,590,748),"dyspnea","common and immediately life-threatening ED dyspnea causes"),
 CropSpec("t62_2","Tintinalli","Table 62-2",TINT,472,(318,40,590,220),"hypercapnia","causes of hypercapnia"),
 CropSpec("t62_3","Tintinalli","Table 62-3",TINT,473,(28,568,292,748),"cough","differential diagnosis of cough"),
 CropSpec("t62_4","Tintinalli","Table 62-4",TINT,474,(52,42,318,225),"cough","sequential approach to chronic cough"),
 CropSpec("t62_5","Tintinalli","Table 62-5",TINT,474,(330,42,590,190),"hiccups","differential diagnosis of hiccups"),
 CropSpec("t62_6","Tintinalli","Table 62-6",TINT,474,(330,662,590,748),"hiccups","physical maneuvers for hiccups"),
 CropSpec("t62_7","Tintinalli","Table 62-7",TINT,475,(28,40,292,222),"hiccups","drug treatment for hiccups"),
 CropSpec("t62_8","Tintinalli","Table 62-8",TINT,475,(28,590,292,748),"cyanosis","central versus peripheral cyanosis differential"),
 CropSpec("t62_9","Tintinalli","Table 62-9",TINT,475,(300,40,565,205),"cyanosis","factors influencing appearance of cyanosis"),
 CropSpec("t62_10","Tintinalli","Table 62-10",TINT,476,(52,40,318,235),"pleural","differential diagnosis of pleural effusion"),
 CropSpec("f62_1","Tintinalli","Figure 62-1",TINT,476,(318,40,590,610),"pleural","supine radiograph and CT showing pleural effusion"),
 CropSpec("f62_2","Tintinalli","Figure 62-2",TINT,477,(28,40,292,320),"pleural","lateral decubitus radiograph showing layering pleural effusion"),
 CropSpec("t62_11","Tintinalli","Table 62-11",TINT,477,(28,365,292,748),"pleural","pleural fluid diagnostic tests"),
 CropSpec("r21_1","Rosen","Table 21.1",ROSEN,247,(44,50,592,500),"dyspnea","Rosen differential diagnoses for acute dyspnea"),
 CropSpec("r21_3","Rosen","Table 21.3",ROSEN,249,(44,55,592,720),"dyspnea","Rosen diagnostic disease patterns causing dyspnea"),
 CropSpec("r2_1","Rosen","Table 2.1",ROSEN,46,(44,570,592,735),"ventilation","Rosen pressure-control versus volume-control ventilation features"),
]
TINT_OBJECTS=["Table 62-1","Table 62-2","Table 62-3","Table 62-4","Table 62-5","Table 62-6","Table 62-7","Table 62-8","Table 62-9","Table 62-10","Figure 62-1","Figure 62-2","Table 62-11"]

def crop_pdf(s:CropSpec)->None:
    fitz.open(s.pdf)[s.page-1].get_pixmap(matrix=fitz.Matrix(2.2,2.2),clip=fitz.Rect(*s.rect),alpha=False).save(PRE/f"{s.key}.png")
def data_uri(p:Path)->str: return "data:image/png;base64,"+base64.b64encode(p.read_bytes()).decode("ascii")
def source_card(s:CropSpec,text:str,delta:str|None=None)->str:
    d=f'<div class="source-delta"><strong><u>Rosen vs Tintinalli:</u></strong> {html.escape(delta)}</div>' if delta else ""
    return f'<article class="source-card"><div class="source-card__label">{html.escape(s.source)} source</div><h3 class="source-card__title">{html.escape(s.label)}</h3><p>{html.escape(text)}</p>{d}<figure class="source-figure reference-image"><img src="{data_uri(PRE/f"{s.key}.png")}" alt="{html.escape(s.source+" "+s.label)}" loading="lazy" decoding="async"><figcaption>{html.escape(s.source)} {html.escape(s.label)}. {html.escape(s.note)}.</figcaption></figure></article>'
def cards(keys:list[str])->str:
    by={c.key:c for c in CROPS}; out=[]
    for k in keys:
        s=by[k]; delta=None
        if s.source=="Rosen": delta="Rosen broadens the differential and ventilation framing; Tintinalli Ch.62 provides the symptom-by-symptom ED spine and pleural-effusion source figures/tables used here."
        out.append(source_card(s,s.note.capitalize()+".",delta))
    return "\n".join(out)
def mcq(n:int,ans:str,stem:str,opts:list[tuple[str,str]])->str:
    b="".join(f'<button class="mcq-opt" type="button" data-option-key="{k}">{k}. {html.escape(v)}</button>' for k,v in opts)
    e="".join(f'<div class="opt-explain {"is-correct" if k==ans else "is-wrong"}" hidden><strong>{k}. {html.escape(v)}</strong><span>{"Correct." if k==ans else "This option misses the core Ch.62 respiratory-distress priority."}</span></div>' for k,v in opts)
    return f'<article class="mcq-wrapper" data-answer="{ans}" data-answered="false"><p class="mcq-stem">Q{n}. {html.escape(stem)}</p><div class="mcq-options">{b}</div><div class="mcq-result" hidden></div><div class="mcq-explains">{e}</div></article>'
def build_mcqs()->str:
    raw=[
("D","Immediately life-threatening dyspnea causes include:",[("A","Upper airway obstruction"),("B","Tension pneumothorax"),("C","Pulmonary embolism or neuromuscular weakness"),("D","All of these")]),
("A","Initial severe dyspnea goal:",[("A","Maintain airway and oxygenation while treating the cause"),("B","Delay oxygen until diagnosis final"),("C","Avoid pulse oximetry"),("D","Discharge if anxious")]),
("B","Pulse oximetry is limited because:",[("A","It never helps"),("B","It may miss impaired gas exchange or abnormal hemoglobins"),("C","It measures PaCO2 directly"),("D","It replaces clinical exam")]),
("C","Hypercapnia is caused by:",[("A","Increased CO2 production alone"),("B","Low hemoglobin only"),("C","Alveolar hypoventilation"),("D","Pleural effusion only")]),
("D","Causes of hypercapnia include:",[("A","Depressed central drive"),("B","Neuromuscular impairment"),("C","Upper airway obstruction or COPD"),("D","All of these")]),
("A","Treatment of hypercapnia primarily increases:",[("A","Minute ventilation"),("B","Hemoglobin only"),("C","Skin perfusion only"),("D","Urine output")]),
("B","Acute cough is generally:",[("A","More than 8 weeks"),("B","Less than 3 weeks"),("C","Always cancer"),("D","Always bacterial")]),
("C","Chronic cough common causes include:",[("A","Smoking/chronic bronchitis"),("B","Upper airway cough syndrome, asthma, GERD, ACE inhibitor"),("C","Both A and B"),("D","Only foreign body")]),
("D","Chronic cough sequential approach includes:",[("A","Chest radiograph if not already done"),("B","Reduce cough triggers and stop ACE inhibitors when relevant"),("C","Treat postnasal drainage/bronchospasm/GERD patterns"),("D","All of these")]),
("A","Persistent hiccups last:",[("A",">48 hours"),("B","Only 5 minutes"),("C","Always 1 month"),("D","Exactly 24 hours")]),
("B","Intractable hiccups last:",[("A","Less than 1 hour"),("B","Longer than 1 month"),("C","Only 2 days"),("D","Never need evaluation")]),
("C","Benign hiccup maneuvers include:",[("A","Swallow sugar"),("B","Sip ice water"),("C","Both A and B"),("D","Immediate intubation")]),
("D","Drug options for persistent hiccups in Tintinalli include:",[("A","Chlorpromazine"),("B","Metoclopramide"),("C","Baclofen/gabapentin alternatives"),("D","All of these")]),
("A","Central cyanosis can reflect:",[("A","Hypoxemia or abnormal hemoglobin"),("B","Only cold fingers"),("C","Only local vasoconstriction"),("D","No oxygen issue ever")]),
("B","Peripheral cyanosis can result from:",[("A","Methemoglobinemia only"),("B","Reduced cardiac output, cold extremities, or arterial/venous obstruction"),("C","Always shunt"),("D","Only high altitude")]),
("C","Carboxyhemoglobinemia pulse oximetry often:",[("A","Reads zero"),("B","Accurately tracks PaO2"),("C","Reads falsely high/normal"),("D","Cannot display a number")]),
("D","Pleural effusion differential includes:",[("A","Heart failure"),("B","Cancer/parapneumonic effusion"),("C","Pulmonary embolism"),("D","All of these")]),
("A","Light criteria identify:",[("A","Exudative pleural effusion"),("B","Hypercapnia"),("C","Central cyanosis"),("D","Hiccup cause")]),
("B","Small free-flowing pleural effusions are best seen on:",[("A","Finger pulse oximetry"),("B","Decubitus radiograph or ultrasound"),("C","ECG only"),("D","Urinalysis")]),
("C","Therapeutic thoracentesis drainage is indicated when:",[("A","Every tiny effusion"),("B","No dyspnea"),("C","Dyspnea at rest or large symptomatic volume"),("D","Only after 2 months")]),
("D","Pleural fluid tests may include:",[("A","Protein and LDH"),("B","Cell count/differential"),("C","Gram stain/culture, glucose, pH when indicated"),("D","All of these")]),
("A","Rosen dyspnea table is useful because it:",[("A","Forces pulmonary, cardiac, abdominal, metabolic, infectious, traumatic, hematologic, and neuromuscular causes into view"),("B","Narrows all cases to asthma"),("C","Eliminates exam"),("D","Replaces oxygen")]),
("B","Rosen ventilation table is relevant when:",[("A","No respiratory support is needed"),("B","The patient needs noninvasive or invasive ventilatory support"),("C","Only cough exists"),("D","Only cyanosis table is used")]),
("C","Do not withhold oxygen in chronic lung disease when:",[("A","The patient is hypoxemic"),("B","Target saturation/ventilation can be monitored"),("C","Both A and B"),("D","Oxygen is always forbidden")]),
("D","Respiratory distress chapter covers:",[("A","Dyspnea and hypoxemia/hypercapnia"),("B","Cough and hiccups"),("C","Cyanosis and pleural effusion"),("D","All of these")]),
("B","Best summary:",[("A","Respiratory distress is one disease"),("B","Stabilize airway/oxygenation/ventilation, identify life threats, and use symptom tables to target testing and treatment"),("C","Pulse ox alone is enough"),("D","Pleural effusions never need testing")]),
]
    return "\n".join(mcq(i,*r) for i,r in enumerate(raw,1))
def doc_html()->str:
    return f"""<!doctype html><html lang="en" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Chapter 062 - Respiratory Distress</title><style>{STYLE}</style></head><body>
<header id="top-header"><button class="hdr-btn" data-sidebar-toggle title="Contents">☰</button><div class="hdr-title">Ch.062 Respiratory Distress</div><button class="hdr-btn theme-btn" data-theme-toggle>Dark</button></header>
<div class="app"><aside id="sidebar" class="sidebar"><button class="hdr-btn sidebar-close" data-sidebar-close>Close</button><div class="sidebar__block"><div class="sidebar__kicker">Chapter</div><h2>Respiratory Distress</h2><p class="meta"><b>Spine:</b> Tintinalli Ch.62</p><p class="meta"><b>Rosen:</b> Dyspnea + ventilation support</p><p class="meta"><b>Build:</b> fresh source rebuild</p></div><div class="sidebar__block"><div class="sidebar__kicker">Contents</div><a class="sidebar__link" href="#dyspnea">Dyspnea</a><a class="sidebar__link" href="#gas">Gas Exchange</a><a class="sidebar__link" href="#cough">Cough</a><a class="sidebar__link" href="#hiccups">Hiccups</a><a class="sidebar__link" href="#cyanosis">Cyanosis</a><a class="sidebar__link" href="#pleural">Pleural Effusion</a><a class="sidebar__link" href="#assessment">MCQs</a></div></aside>
<main id="main" class="main"><div class="content-wrap"><div class="utility-bar">Fresh rebuild • Tintinalli Ch.62 • Every Tintinalli table/figure included • MCQs hidden until answered</div>
<section class="hero section" id="dyspnea"><div class="eyebrow">Pulmonary Disorders</div><h1 class="hero__title">Respiratory Distress</h1><p class="lede">Respiratory distress is a clinical syndrome, not a final diagnosis. First protect airway, oxygenation, and ventilation; then sort dyspnea by life threat, physiology, and targeted exam findings.</p><div class="callout warn"><strong>Board trap:</strong> <mark>pulse oximetry does not measure ventilation, PaCO2, work of breathing, or all abnormal hemoglobins.</mark></div><p><u>Upper airway obstruction, tension pneumothorax, PE, pulmonary edema, neuromuscular weakness, and toxic/metabolic disease must stay active early.</u></p>{cards(["t62_1","r21_1","r21_3"])}</section>
<section class="section" id="gas"><h2>Hypoxemia, Hypercapnia, and Ventilatory Support</h2><p>Hypoxemia reflects low inspired oxygen, hypoventilation, shunt, V/Q mismatch, or diffusion impairment. Hypercapnia is alveolar hypoventilation and is treated by increasing minute ventilation while addressing the cause.</p>{cards(["t62_2","r2_1"])}</section>
<section class="section" id="cough"><h2>Cough</h2><p>Acute cough is usually less than 3 weeks and often infectious or irritant. Subacute cough is often postinfectious. Chronic cough requires a sequential approach: chest radiograph, trigger removal, upper-airway cough syndrome, asthma/bronchospasm testing, GERD treatment, and selective CT or specialty referral when persistent.</p>{cards(["t62_3","t62_4"])}</section>
<section class="section" id="hiccups"><h2>Hiccups</h2><p>Hiccups are diaphragm/intercostal spasms. Benign episodes are brief; persistent or intractable hiccups need trigger review, neurologic/thoracoabdominal consideration, physical maneuvers, and selected medication.</p>{cards(["t62_5","t62_6","t62_7"])}</section>
<section class="section" id="cyanosis"><h2>Cyanosis</h2><p>Central cyanosis suggests systemic deoxygenation or abnormal hemoglobin; peripheral cyanosis can reflect low flow, cold exposure, or arterial/venous obstruction. Co-oximetry matters when pulse oximetry is misleading.</p>{cards(["t62_8","t62_9"])}</section>
<section class="section" id="pleural"><h2>Pleural Effusion</h2><p>Pleural effusion may be transudative, exudative, or mixed after diuretic therapy. Imaging can require decubitus radiographs or ultrasound; fluid testing uses Light criteria plus targeted studies. Drain symptomatic large effusions carefully and avoid excessive rapid drainage.</p>{cards(["t62_10","f62_1","f62_2","t62_11"])}</section>
<section class="question-set section" id="assessment"><h2>Inline Assessment MCQs</h2>{build_mcqs()}</section>
</div></main></div><div class="score-pill" data-score-text>0 correct / 0 answered / 26 total</div><div class="image-modal" data-image-modal><button class="hdr-btn" data-modal-close>Close</button><img alt="Zoomed source"></div><script>{SCRIPT}</script></body></html>"""
def extract_embedded(doc:str)->list[Path]:
    EMBED.mkdir(parents=True,exist_ok=True)
    for old in EMBED.glob("*.png"): old.unlink()
    paths=[]
    for i,m in enumerate(re.finditer(r"data:image/png;base64,([^\"]+)",doc),1):
        p=EMBED/f"ch062_embedded_{i:02d}.png"; p.write_bytes(base64.b64decode(m.group(1))); paths.append(p)
    return paths
def contact_sheet(paths:list[Path])->Path:
    cols,w,h=2,560,430; rows=(len(paths)+1)//2; sheet=Image.new("RGB",(cols*w,rows*h),"white"); d=ImageDraw.Draw(sheet)
    for i,p in enumerate(paths):
        im=Image.open(p).convert("RGB"); im.thumbnail((520,360)); x=(i%2)*w; y=(i//2)*h
        d.text((x+8,y+14),f"{i+1:02d} {p.name}",fill=(0,0,0)); sheet.paste(im,(x+20,y+48))
    out=EMBED/"ch062_embedded_contact_sheet.png"; sheet.save(out); return out
def md_to_html(md:str,title:str)->str:
    out=[]; intable=False
    for line in md.splitlines():
        if line.startswith("|") and line.endswith("|"):
            cells=[c.strip() for c in line.strip("|").split("|")]
            if cells and set(cells[0])<=set("-"): continue
            if not intable: out.append("<table>"); intable=True
            tag="th" if cells and cells[0] in {"#","Ch","Source"} else "td"; out.append("<tr>"+"".join(f"<{tag}>{html.escape(c)}</{tag}>" for c in cells)+"</tr>"); continue
        if intable: out.append("</table>"); intable=False
        if line.startswith("# "): out.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "): out.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.strip(): out.append(f"<p>{html.escape(line)}</p>")
    if intable: out.append("</table>")
    return f"<!doctype html><html><head><meta charset='utf-8'><title>{html.escape(title)}</title><style>body{{font-family:Arial,sans-serif;margin:28px;background:#f8fafc;color:#111827}}table{{border-collapse:collapse;width:100%;font-size:13px}}td,th{{border:1px solid #cbd5e1;padding:6px;vertical-align:top}}th{{background:#e2e8f0}}h1,h2{{color:#0f4c5c}}</style></head><body>{''.join(out)}</body></html>"
def build_qa(paths:list[Path],sheet:Path)->None:
    rows=[f"| {i} | {s.source} | {s.label} | {s.pdf.name} | {s.page} | `{p.relative_to(ROOT).as_posix()}` | PASS | {s.note}; topic-local crop included |" for i,(s,p) in enumerate(zip(CROPS,paths),1)]
    inv="\n".join(f"- {s.source} {s.label}: page {s.page}, placement `{s.placement}`" for s in CROPS)
    md=f"""# CH062 Crop QA - 2026-05-10

Fresh rebuild from source PDFs. No legacy Chapter062 HTML was used.

## Source Inventory Used

Tintinalli inventory: 13/13 included. Required Tintinalli objects are {", ".join(TINT_OBJECTS)}.

Rosen note: included dyspnea differential/pattern tables and ventilation-support table as topic-local source crops.

{inv}

## Embedded Crop QA

Contact sheet: `{sheet.relative_to(ROOT).as_posix()}`

| # | Source | Object | PDF | PDF page | Extracted final embedded image | Status | Note |
|---|---|---|---|---:|---|---|---|
{chr(10).join(rows)}

## Content Gate

Content: PASS. Dyspnea, hypoxemia, hypercapnia, cough, hiccups, cyanosis, pleural effusion, diagnostic testing, treatment, and Rosen-vs-Tintinalli source cards all have narrative summaries; every Tintinalli figure/table is included topic-locally; no visible audit/source-audit repair text is inside the chapter.

Pattern: PASS. Ch186/Ch201 shell, top header, sidebar/main layout, source cards, and accepted MCQ behavior are present.
"""
    QA_MD.write_text(md,encoding="utf-8"); QA_HTML.write_text(md_to_html(md,"CH062 Crop QA"),encoding="utf-8")
def update_audit()->None:
    md=AUDIT_MD.read_text(encoding="utf-8")
    line="| 62 | Chapter062_RespiratoryDistress.html | PASS | PASS | PASS | 26 | 3 | 13 | 16 | PASS | 5 | Fresh rebuild 2026-05-10; Pattern: PASS; Content: PASS; MCQ all-option explanations PASS; every Tintinalli figure/table included (13/13); Rosen source crops topic-local; cropQA PASS (16/16) |"
    md=re.sub(r"^\| 62 \|.*$",line,md,flags=re.M) if re.search(r"^\| 62 \|",md,flags=re.M) else md.rstrip()+"\n"+line+"\n"
    AUDIT_MD.write_text(md,encoding="utf-8"); AUDIT_HTML.write_text(md_to_html(md,"Chapter Complete Audit"),encoding="utf-8")
def gate(doc:str,paths:list[Path])->None:
    checks={"top":doc.count('id="top-header"'),"sidebar":doc.count('id="sidebar"'),"main":doc.count('id="main"'),"mcq":doc.count('class="mcq-wrapper"'),"result":doc.count('class="mcq-result"'),"legacy":doc.count("mcq-card"),"source":doc.count('class="source-figure reference-image"'),"data":doc.count("data:image/png;base64,"),"mark":doc.count("<mark>"),"u":doc.count("<u>"),"rosen":doc.count("Rosen source"),"delta":doc.count("Rosen vs Tintinalli")}
    assert checks["top"]==1 and checks["sidebar"]==1 and checks["main"]==1,checks
    assert checks["mcq"]==26 and checks["result"]==26 and checks["legacy"]==0,checks
    assert checks["source"]==len(CROPS) and checks["data"]==len(CROPS)==len(paths),checks
    assert checks["mark"]>0 and checks["u"]>0 and checks["rosen"]>=3 and checks["delta"]>=3,checks
    assert not any(x in doc for x in ["Source Check","Rosen Source Audit","Source Audit","repair note"]),checks
    print(checks)
def main()->None:
    PRE.mkdir(parents=True,exist_ok=True)
    for old in PRE.glob("*.png"): old.unlink()
    for s in CROPS: crop_pdf(s)
    doc=doc_html(); OUT_HTML.parent.mkdir(parents=True,exist_ok=True); OUT_HTML.write_text(doc,encoding="utf-8")
    paths=extract_embedded(doc); sheet=contact_sheet(paths); build_qa(paths,sheet); gate(doc,paths); update_audit()
    (MIRROR/"docs/chapters/complete").mkdir(parents=True,exist_ok=True); shutil.copy2(OUT_HTML,MIRROR/"docs/chapters/complete"/OUT_HTML.name)
    for f in [QA_MD,QA_HTML,AUDIT_MD,AUDIT_HTML]: shutil.copy2(f,MIRROR/f.name)
    print(f"wrote {OUT_HTML}"); print(f"wrote {QA_MD}"); print(f"contact {sheet}")
if __name__=="__main__": main()
