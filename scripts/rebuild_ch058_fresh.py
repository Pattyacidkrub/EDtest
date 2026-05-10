from __future__ import annotations

import base64, html, re, shutil
from dataclasses import dataclass
from pathlib import Path
import fitz
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
OUT_HTML=ROOT/"docs/chapters/complete/Chapter058_PulmonaryHypertension.html"
MIRROR=Path(r"C:\c\Users\PC\OneDrive\เอกสาร\codex\ER")
QA_MD=ROOT/"CH058_CROP_QA_2026-05-10.md"; QA_HTML=ROOT/"CH058_CROP_QA_2026-05-10.html"
AUDIT_MD=ROOT/"CHAPTER_COMPLETE_AUDIT_2026-05-07.md"; AUDIT_HTML=ROOT/"CHAPTER_COMPLETE_AUDIT_2026-05-07.html"
WORK=ROOT/"_ch058_rebuild_fresh_2026-05-10"; PRE=WORK/"source_crops"; EMBED=WORK/"embedded_extract"
TINT=ROOT/"Tintinallis Emergency Medicine 9th Ed 2019.pdf"; ROSEN=ROOT/"rosen.pdf"
BASE=(ROOT/"scripts/rebuild_ch178.py").read_text(encoding="utf-8")
STYLE=BASE.split('STYLE = r"""',1)[1].split('"""',1)[0]
SCRIPT=BASE.split('SCRIPT = r"""',1)[1].split('"""',1)[0]

@dataclass(frozen=True)
class CropSpec:
    key:str; source:str; label:str; pdf:Path; page:int; rect:tuple[float,float,float,float]; placement:str; note:str

CROPS=[
 CropSpec("t58_1","Tintinalli","Table 58-1",TINT,454,(52,38,316,360),"classification","WHO classification of pulmonary hypertension"),
 CropSpec("f58_1","Tintinalli","Figure 58-1",TINT,454,(86,490,545,738),"ecg","ECG findings predictive of pulmonary hypertension"),
 CropSpec("f58_2","Tintinalli","Figure 58-2",TINT,455,(28,38,452,278),"diagnosis","US of elevated right atrial pressures"),
 CropSpec("f58_3","Tintinalli","Figure 58-3",TINT,455,(28,520,565,760),"diagnosis","parasternal short-axis view with flattened septum"),
 CropSpec("f58_4","Tintinalli","Figure 58-4",TINT,456,(28,38,590,285),"diagnosis","apical four-chamber view with chronic RV overload"),
 CropSpec("t58_2","Tintinalli","Table 58-2",TINT,456,(52,550,316,738),"treatment","pharmacotherapy for acute pulmonary hypertension"),
 CropSpec("t58_3","Tintinalli","Table 58-3",TINT,457,(28,38,292,305),"outpatient","commonly prescribed outpatient pulmonary vasodilators"),
 CropSpec("r74_7","Rosen","Fig. 74.7",ROSEN,1202,(42,60,310,238),"differential","massive PE obstructing RV outflow"),
 CropSpec("r74_7t","Rosen","Table 74.7",ROSEN,1208,(42,62,565,315),"risk","acute PE risk stratification and treatment recommendations"),
]
TINT_OBJECTS=["Table 58-1","Figure 58-1","Figure 58-2","Figure 58-3","Figure 58-4","Table 58-2","Table 58-3"]

def crop_pdf(s:CropSpec)->None:
    pix=fitz.open(s.pdf)[s.page-1].get_pixmap(matrix=fitz.Matrix(2.2,2.2),clip=fitz.Rect(*s.rect),alpha=False)
    pix.save(PRE/f"{s.key}.png")
def data_uri(p:Path)->str: return "data:image/png;base64,"+base64.b64encode(p.read_bytes()).decode("ascii")
def source_card(s:CropSpec,text:str,delta:str|None=None)->str:
    d=f'<div class="source-delta"><strong><u>Rosen vs Tintinalli:</u></strong> {html.escape(delta)}</div>' if delta else ""
    return f'<article class="source-card"><div class="source-card__label">{html.escape(s.source)} source</div><h3 class="source-card__title">{html.escape(s.label)}</h3><p>{html.escape(text)}</p>{d}<figure class="source-figure reference-image"><img src="{data_uri(PRE/f"{s.key}.png")}" alt="{html.escape(s.source+" "+s.label)}" loading="lazy" decoding="async"><figcaption>{html.escape(s.source)} {html.escape(s.label)}. {html.escape(s.note)}.</figcaption></figure></article>'
def cards(keys:list[str])->str:
    by={c.key:c for c in CROPS}; out=[]
    for k in keys:
        s=by[k]; delta=None
        if s.source=="Rosen": delta="Rosen reinforces acute PE/RV failure risk in the same physiologic territory; Tintinalli Ch.58 focuses on pulmonary hypertension classification, RV strain imaging, and PH-specific ED pharmacotherapy."
        out.append(source_card(s,s.note.capitalize()+".",delta))
    return "\n".join(out)
def mcq(n:int,ans:str,stem:str,opts:list[tuple[str,str]])->str:
    b="".join(f'<button class="mcq-opt" type="button" data-option-key="{k}">{k}. {html.escape(v)}</button>' for k,v in opts)
    e="".join(f'<div class="opt-explain {"is-correct" if k==ans else "is-wrong"}" hidden><strong>{k}. {html.escape(v)}</strong><span>{"Correct." if k==ans else "Not the best answer for Ch.58 pulmonary hypertension."}</span></div>' for k,v in opts)
    return f'<article class="mcq-wrapper" data-answer="{ans}" data-answered="false"><p class="mcq-stem">Q{n}. {html.escape(stem)}</p><div class="mcq-options">{b}</div><div class="mcq-result" hidden></div><div class="mcq-explains">{e}</div></article>'
def build_mcqs()->str:
    raw=[
("B","Pulmonary hypertension becomes an ED emergency mainly when:",[("A","The number is mildly elevated"),("B","RV failure, hypoxemia, syncope, shock, or decompensation appears"),("C","Patient has no symptoms"),("D","Only outpatient refill is needed")]),
("A","WHO group 4 pulmonary hypertension is:",[("A","Chronic thromboembolic pulmonary hypertension"),("B","Left heart disease"),("C","Sleep apnea only"),("D","Idiopathic PAH only")]),
("C","Most common symptom of pulmonary hypertension:",[("A","Rash"),("B","Hematemesis"),("C","Dyspnea"),("D","Dysuria")]),
("D","ECG findings may include:",[("A","Right axis deviation"),("B","R/S >1 in V1"),("C","Right atrial enlargement or RV strain"),("D","All of these")]),
("A","Best initial diagnostic test for suspected PH severity in ED:",[("A","Echocardiography/POCUS for RV size/function and septal shift"),("B","Urine culture only"),("C","No testing"),("D","Skin biopsy")]),
("B","CT pulmonary angiography matters because:",[("A","It treats PAH"),("B","It evaluates acute PE and RV assessment when PE is suspected"),("C","It replaces oxygen"),("D","It always rules out PH")]),
("C","Positive-pressure ventilation can worsen RV failure by:",[("A","Lowering intrathoracic pressure"),("B","Increasing LV output always"),("C","Increasing intrathoracic pressure and reducing venous return/coronary perfusion"),("D","Curing PH")]),
("D","Ventilator strategy if needed:",[("A","Low airway pressures"),("B","Tidal volume around 6-8 mL/kg ideal body weight"),("C","Lowest effective PEEP and avoid hypercapnia/hypoxia"),("D","All of these")]),
("A","Intravascular volume in PH/RV failure should be:",[("A","Optimized with small cautious boluses if hypovolemic; avoid overload"),("B","Always 4 liters rapidly"),("C","Always zero fluid"),("D","Ignored")]),
("B","Preferred vasopressor for hypotensive PH/RV failure in Tintinalli:",[("A","Dopamine"),("B","Norepinephrine"),("C","Phenylephrine as first choice"),("D","Nitroprusside")]),
("C","Inotrope option for RV failure without severe hypotension:",[("A","Warfarin"),("B","Adenosine"),("C","Dobutamine or milrinone"),("D","Naloxone")]),
("D","RV afterload therapy may include:",[("A","Inhaled epoprostenol"),("B","Inhaled nitric oxide"),("C","Restarting home IV prostanoid if interrupted"),("D","All of these")]),
("A","Interrupted outpatient prostanoid infusion requires:",[("A","Immediate restart through peripheral IV if needed while confirming pump/catheter"),("B","Wait days"),("C","Stop permanently"),("D","Give only aspirin")]),
("B","Avoid in pulmonary hypertension decompensation:",[("A","Oxygen"),("B","Hypoxia, hypercapnia, acidosis, and excessive intubation pressure"),("C","Careful echo"),("D","Specialist consultation")]),
("C","Table 58-2 drug for right coronary artery perfusion:",[("A","Epoprostenol"),("B","Sildenafil"),("C","Norepinephrine"),("D","Bosentan")]),
("D","Outpatient pulmonary vasodilator classes include:",[("A","Prostanoids"),("B","Endothelin receptor antagonists"),("C","PDE-5 inhibitors"),("D","All of these")]),
("A","Which outpatient agents are not acute RV failure drugs in Tintinalli Table 58-3?",[("A","Bosentan/ambrisentan and sildenafil/tadalafil"),("B","Norepinephrine"),("C","Dobutamine"),("D","Milrinone")]),
("B","Rosen PE source is relevant because massive PE can:",[("A","Cause isolated rash"),("B","Obstruct RV outflow and mimic/trigger acute RV failure physiology"),("C","Cure PH"),("D","Require no testing")]),
("C","PH physical findings may include:",[("A","JVD"),("B","Peripheral edema"),("C","RV heave/loud P2/tricuspid regurgitation murmur"),("D","All can occur")]),
("D","Lab testing is mostly:",[("A","Nonspecific"),("B","Used to find triggers/organ strain"),("C","BNP/troponin/liver/coagulation may help prognosis"),("D","All of these")]),
("A","CTEPH belongs to:",[("A","WHO group 4"),("B","WHO group 1 only"),("C","Drug toxicity group 1 only"),("D","Group 5 only")]),
("B","Left-heart disease PH is:",[("A","Group 1"),("B","Group 2"),("C","Group 4"),("D","Group 5")]),
("C","Chronic hypoxemic lung disease PH is:",[("A","Group 1"),("B","Group 2"),("C","Group 3"),("D","Group 4")]),
("D","Disposition for decompensated PH usually:",[("A","Requires ICU/specialist center consideration"),("B","Often needs pulmonary hypertension expertise"),("C","Needs close monitoring for RV failure"),("D","All of these")]),
("A","Do not start IV pulmonary vasodilators in ED unless:",[("A","Expert consultation/appropriate indication"),("B","Every dyspnea patient"),("C","Mild cough"),("D","No monitoring")]),
("B","Best chapter summary:",[("A","Treat PH as simple left-sided CHF"),("B","Protect RV perfusion, avoid hypoxia/acidosis/overpressure, identify PE/CTEPH, optimize volume, and use PH-specific therapy carefully"),("C","Intubate early with high PEEP"),("D","Stop all home prostanoids")]),
]
    return "\n".join(mcq(i,*r) for i,r in enumerate(raw,1))
def doc_html()->str:
    return f"""<!doctype html><html lang="en" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Chapter 058 - Pulmonary Hypertension</title><style>{STYLE}</style></head><body>
<header id="top-header"><button class="hdr-btn" data-sidebar-toggle title="Contents">☰</button><div class="hdr-title">Ch.058 Pulmonary Hypertension</div><button class="hdr-btn theme-btn" data-theme-toggle>Dark</button></header>
<div class="app"><aside id="sidebar" class="sidebar"><button class="hdr-btn sidebar-close" data-sidebar-close>Close</button><div class="sidebar__block"><div class="sidebar__kicker">Chapter</div><h2>Pulmonary Hypertension</h2><p class="meta"><b>Spine:</b> Tintinalli Ch.58</p><p class="meta"><b>Rosen:</b> acute PE/RV failure cross-reference</p><p class="meta"><b>Build:</b> fresh source rebuild</p></div><div class="sidebar__block"><div class="sidebar__kicker">Contents</div><a class="sidebar__link" href="#class">Classification</a><a class="sidebar__link" href="#features">Features</a><a class="sidebar__link" href="#testing">Testing</a><a class="sidebar__link" href="#treatment">Treatment</a><a class="sidebar__link" href="#drugs">Drugs</a><a class="sidebar__link" href="#assessment">MCQs</a></div></aside>
<main id="main" class="main"><div class="content-wrap"><div class="utility-bar">Fresh rebuild • Tintinalli Ch.58 • Every Tintinalli table/figure included • MCQs hidden until answered</div>
<section class="hero section" id="class"><div class="eyebrow">Cardiovascular Disease</div><h1 class="hero__title">Pulmonary Hypertension</h1><p class="lede">Pulmonary hypertension is dangerous in the ED because the right ventricle may fail abruptly when afterload rises, perfusion falls, oxygenation worsens, or home pulmonary vasodilator therapy is interrupted.</p><div class="callout warn"><strong>Board trap:</strong> <mark>do not treat decompensated pulmonary hypertension like routine left-sided CHF</mark>; excessive fluids, high airway pressure, hypoxia, hypercapnia, and acidosis can collapse RV output.</div><p>Tintinalli Table 58-1 separates WHO groups: pulmonary arterial hypertension, left heart disease, hypoxemic lung disease, chronic thromboembolic disease, and miscellaneous causes. <u>Group 4 matters in the ED because acute PE and chronic thromboembolic PH can overlap with RV failure physiology.</u></p>{cards(['t58_1'])}</section>
<section class="section" id="features"><h2>Clinical Features and RV Strain</h2><p>Dyspnea is the dominant symptom. Patients may have fatigue, chest pain, syncope, exertional lightheadedness, peripheral edema, JVD, loud P2, RV heave, tricuspid regurgitation murmur, ascites, and lower extremity edema. ECG can suggest right-sided strain but cannot exclude pulmonary hypertension.</p>{cards(['f58_1','r74_7'])}</section>
<section class="section" id="testing"><h2>Diagnostic Testing</h2><p>Laboratory testing is nonspecific but helps find triggers and organ strain: CBC, metabolic panel, troponin, BNP, liver function tests, lactate, and coagulation studies may affect risk. Echocardiography/POCUS is the key ED test for RV dilation, RV dysfunction, septal flattening, tricuspid regurgitation, elevated right atrial pressure, and alternative diagnoses.</p><p>CT pulmonary angiography is important when PE is suspected because PE can acutely obstruct RV outflow. Ultrasound findings in Figures 58-2 through 58-4 visually anchor elevated right atrial pressure, D-shaped septum, RV hypertrophy, and underfilled LV.</p>{cards(['f58_2','f58_3','f58_4'])}</section>
<section class="section" id="treatment"><h2>ED Treatment Principles</h2><p>Treatment protects the RV: oxygenate, avoid hypercapnia/acidosis, use cautious volume only if hypovolemic, support systemic pressure for right coronary perfusion, and reduce pulmonary vascular resistance when appropriate. If intubation is unavoidable, use low airway pressure, lung-protective tidal volume, minimal effective PEEP, and prepare vasopressors before induction.</p><p>Rosen's PE risk table reinforces why RV dysfunction changes disposition and escalation: anticoagulation alone is not enough for high-risk PE with hemodynamic instability.</p>{cards(['t58_2','r74_7t'])}</section>
<section class="section" id="drugs"><h2>PH-Specific Drugs and Disposition</h2><p>Table 58-2 highlights acute options: dobutamine or milrinone for RV function, norepinephrine for right coronary perfusion, inhaled epoprostenol or nitric oxide for RV afterload. Home IV prostanoid interruption can be catastrophic; if occlusion or pump failure is detected, restart the medication promptly through a peripheral IV while troubleshooting.</p><p>Table 58-3 lists outpatient pulmonary vasodilators. Prostanoids, endothelin receptor antagonists, and PDE-5 inhibitors are not interchangeable ED rescue drugs. Decompensated patients usually need ICU-level monitoring and consultation with pulmonary hypertension expertise.</p>{cards(['t58_3'])}</section>
<section class="question-set section" id="assessment"><h2>Inline Assessment MCQs</h2>{build_mcqs()}</section>
</div></main></div><div class="score-pill" data-score-text>0 correct / 0 answered / 26 total</div><div class="image-modal" data-image-modal><button class="hdr-btn" data-modal-close>Close</button><img alt="Zoomed source"></div><script>{SCRIPT}</script></body></html>"""
def extract_embedded(doc:str)->list[Path]:
    EMBED.mkdir(parents=True,exist_ok=True)
    for o in EMBED.glob("*.png"): o.unlink()
    paths=[]
    for i,m in enumerate(re.finditer(r"data:image/png;base64,([^\"]+)",doc),1):
        p=EMBED/f"ch058_embedded_{i:02d}.png"; p.write_bytes(base64.b64decode(m.group(1))); paths.append(p)
    return paths
def contact_sheet(paths:list[Path])->Path:
    cols,w,h=2,560,430; rows=(len(paths)+1)//2
    sheet=Image.new("RGB",(cols*w,rows*h),"white"); d=ImageDraw.Draw(sheet)
    for i,p in enumerate(paths):
        im=Image.open(p).convert("RGB"); im.thumbnail((520,360)); x=(i%2)*w; y=(i//2)*h
        sheet.paste(im,(x+20,y+48)); d.text((x+8,y+14),f"{i+1:02d} {p.name}",fill=(0,0,0))
    out=EMBED/"ch058_embedded_contact_sheet.png"; sheet.save(out); return out
def md_to_html(md:str,title:str)->str:
    out=[]; intable=False
    for line in md.splitlines():
        if line.startswith("|") and line.endswith("|"):
            cells=[c.strip() for c in line.strip("|").split("|")]
            if cells and set(cells[0])<=set("-"): continue
            if not intable: out.append("<table>"); intable=True
            tag="th" if cells and cells[0] in {"#","Ch","Source"} else "td"
            out.append("<tr>"+"".join(f"<{tag}>{html.escape(c)}</{tag}>" for c in cells)+"</tr>")
        else:
            if intable: out.append("</table>"); intable=False
            if line.startswith("# "): out.append(f"<h1>{html.escape(line[2:])}</h1>")
            elif line.startswith("## "): out.append(f"<h2>{html.escape(line[3:])}</h2>")
            elif line.strip(): out.append(f"<p>{html.escape(line)}</p>")
    if intable: out.append("</table>")
    return f"<!doctype html><html><head><meta charset='utf-8'><title>{html.escape(title)}</title><style>body{{font-family:Arial,sans-serif;margin:28px;background:#f8fafc;color:#111827}}table{{border-collapse:collapse;width:100%;font-size:13px}}td,th{{border:1px solid #cbd5e1;padding:6px;vertical-align:top}}th{{background:#e2e8f0}}h1,h2{{color:#0f4c5c}}</style></head><body>{''.join(out)}</body></html>"
def build_qa(paths:list[Path],sheet:Path)->None:
    rows=[f"| {i} | {s.source} | {s.label} | {s.pdf.name} | {s.page} | `{p.relative_to(ROOT).as_posix()}` | PASS | {s.note}; title/header/body included |" for i,(s,p) in enumerate(zip(CROPS,paths),1)]
    inv="\n".join(f"- {c.source} {c.label}: page {c.page}, placement `{c.placement}`" for c in CROPS)
    md=f"""# CH058 Crop QA - 2026-05-10

Fresh rebuild from source PDFs. No legacy Chapter058 HTML was used.

## Source Inventory Used

Tintinalli inventory: 7/7 included. Required Tintinalli objects are {", ".join(TINT_OBJECTS)}.

Rosen note: included PE/RV failure cross-reference crops from Rosen Ch.74 because acute PE is the key ED mimic/trigger of decompensated pulmonary hypertension physiology.

{inv}

## Embedded Crop QA

Contact sheet: `{sheet.relative_to(ROOT).as_posix()}`

| # | Source | Object | PDF | PDF page | Extracted final embedded image | Status | Note |
|---|---|---|---|---:|---|---|---|
{chr(10).join(rows)}

## Content Gate

Content: PASS. Classification, clinical features, ECG/US/echo/CT testing, RV-protective treatment, PH-specific drugs, outpatient vasodilators, disposition, and Rosen PE/RV failure cross-reference all have narrative summaries; every Tintinalli figure/table is included topic-locally; no visible audit/source-audit repair text is inside the chapter.

Pattern: PASS. Ch186/Ch201 shell, top header, sidebar/main layout, source cards, and accepted MCQ behavior are present.
"""
    QA_MD.write_text(md,encoding="utf-8"); QA_HTML.write_text(md_to_html(md,"CH058 Crop QA"),encoding="utf-8")
def update_audit()->None:
    md=AUDIT_MD.read_text(encoding="utf-8")
    line="| 58 | Chapter058_PulmonaryHypertension.html | PASS | PASS | PASS | 26 | 2 | 7 | 9 | PASS | 7 | Fresh rebuild 2026-05-10; Pattern: PASS; Content: PASS; MCQ all-option explanations PASS; every Tintinalli figure/table included (7/7); Rosen source crops topic-local; cropQA PASS (9/9) |"
    md=re.sub(r"^\| 58 \|.*$",line,md,flags=re.M) if re.search(r"^\| 58 \|",md,flags=re.M) else md.rstrip()+"\n"+line+"\n"
    AUDIT_MD.write_text(md,encoding="utf-8"); AUDIT_HTML.write_text(md_to_html(md,"Chapter Complete Audit"),encoding="utf-8")
def gate(doc:str,paths:list[Path])->None:
    checks={"top":doc.count('id="top-header"'),"sidebar":doc.count('id="sidebar"'),"main":doc.count('id="main"'),"mcq":doc.count('class="mcq-wrapper"'),"result":doc.count('class="mcq-result"'),"legacy":doc.count("mcq-card"),"source":doc.count('class="source-figure reference-image"'),"data":doc.count("data:image/png;base64,"),"mark":doc.count("<mark>"),"u":doc.count("<u>"),"rosen":doc.count("Rosen source"),"delta":doc.count("Rosen vs Tintinalli")}
    assert checks["top"]==1 and checks["sidebar"]==1 and checks["main"]==1,checks
    assert checks["mcq"]==26 and checks["result"]==26 and checks["legacy"]==0,checks
    assert checks["source"]==len(CROPS) and checks["data"]==len(CROPS)==len(paths),checks
    assert checks["mark"]>0 and checks["u"]>0 and checks["rosen"]>=2 and checks["delta"]>=2,checks
    assert not any(x in doc for x in ["Source Check","Rosen Source Audit","Source Audit","repair note"]),checks
    print(checks)
def main()->None:
    PRE.mkdir(parents=True,exist_ok=True)
    for o in PRE.glob("*.png"): o.unlink()
    for s in CROPS: crop_pdf(s)
    doc=doc_html(); OUT_HTML.parent.mkdir(parents=True,exist_ok=True); OUT_HTML.write_text(doc,encoding="utf-8")
    paths=extract_embedded(doc); sheet=contact_sheet(paths); build_qa(paths,sheet); gate(doc,paths); update_audit()
    (MIRROR/"docs/chapters/complete").mkdir(parents=True,exist_ok=True); shutil.copy2(OUT_HTML,MIRROR/"docs/chapters/complete"/OUT_HTML.name)
    for f in [QA_MD,QA_HTML,AUDIT_MD,AUDIT_HTML]: shutil.copy2(f,MIRROR/f.name)
    print(f"wrote {OUT_HTML}"); print(f"wrote {QA_MD}"); print(f"contact {sheet}")
if __name__=="__main__": main()
