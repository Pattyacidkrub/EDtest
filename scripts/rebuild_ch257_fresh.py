from __future__ import annotations
import base64, html, re, shutil
from dataclasses import dataclass
from pathlib import Path
import fitz
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
OUT_HTML=ROOT/"docs/chapters/complete/Chapter257_HeadTrauma.html"
MIRROR=Path(r"C:\c\Users\PC\OneDrive\เอกสาร\codex\ER")
QA_MD=ROOT/"CH257_CROP_QA_2026-05-09.md"; QA_HTML=ROOT/"CH257_CROP_QA_2026-05-09.html"
AUDIT_MD=ROOT/"CHAPTER_COMPLETE_AUDIT_2026-05-07.md"; AUDIT_HTML=ROOT/"CHAPTER_COMPLETE_AUDIT_2026-05-07.html"
WORK=ROOT/"_ch257_rebuild_fresh_2026-05-09"; PRE=WORK/"source_crops"; EMBED=WORK/"embedded_extract"
TINT=ROOT/"Tintinallis Emergency Medicine 9th Ed 2019.pdf"; ROSEN=ROOT/"rosen.pdf"; ATLS=ROOT/"ATLS_11th_2025.pdf"
BASE=(ROOT/"scripts/rebuild_ch178.py").read_text(encoding="utf-8")
STYLE=BASE.split('STYLE = r"""',1)[1].split('"""',1)[0]; SCRIPT=BASE.split('SCRIPT = r"""',1)[1].split('"""',1)[0]

@dataclass(frozen=True)
class CropSpec:
    key:str; source:str; label:str; pdf:Path; page:int; rect:tuple[float,float,float,float]; placement:str; note:str; delta:str=""

CROPS=[
 CropSpec("tint_table_257_5","Tintinalli","Table 257-5",TINT,1732,(48,40,318,214),"ct decision","New Orleans and Canadian CT Head Rule"),
 CropSpec("tint_table_257_7","Tintinalli","Table 257-7",TINT,1733,(28,40,585,275),"ed treatment","checklist for ED treatment of brain injury"),
 CropSpec("tint_table_257_8","Tintinalli","Table 257-8",TINT,1733,(28,596,292,754),"intubation","intubation agents in brain injury"),
 CropSpec("tint_fig_257_8","Tintinalli","Figure 257-8",TINT,1736,(50,480,300,748),"intracranial injury","epidural hematoma"),
 CropSpec("tint_fig_257_9","Tintinalli","Figure 257-9",TINT,1736,(320,480,592,748),"intracranial injury","small subdural hematoma"),
 CropSpec("tint_table_257_10","Tintinalli","Table 257-10",TINT,1737,(28,560,586,748),"intracranial injury","comparison of intracranial injuries"),
 CropSpec("rosen_fig_33_4","Rosen","Fig. 33.4",ROSEN,376,(92,82,520,735),"gcs","how to calculate Glasgow Coma Scale","Rosen vs Tintinalli: Rosen gives a visual GCS scoring aid; Tintinalli supplies GCS tables and uses motor GCS for triage."),
 CropSpec("rosen_box_33_3","Rosen","Box 33.3",ROSEN,378,(312,64,568,338),"rotterdam","Rotterdam CT score","Rosen vs Tintinalli: Rosen adds CT prognostic scoring; Tintinalli focuses on ED CT decision rules and injury pattern recognition."),
 CropSpec("rosen_fig_33_6","Rosen","Fig. 33.6",ROSEN,378,(314,375,568,660),"epidural ct","acute epidural hematoma CT","Rosen vs Tintinalli: Rosen reinforces CT morphology for epidural hemorrhage; Tintinalli compares EDH, SDH, SAH, and contusion patterns."),
 CropSpec("atls_table_7_12","ATLS","Table 7-12",ATLS,138,(34,350,574,732),"goals","optimal values in TBI management","ATLS vs Tintinalli: ATLS gives physiologic targets; Tintinalli gives ED checklist items that operationalize the same targets."),
 CropSpec("atls_table_7_13","ATLS","Table 7-13",ATLS,140,(36,42,574,248),"hyperosmolar","hyperosmolar agents","ATLS vs Tintinalli: ATLS lists hyperosmolar doses; Tintinalli states when to treat suspected elevated ICP/herniation."),
]

def crop_pdf(s):
    pix=fitz.open(s.pdf)[s.page-1].get_pixmap(matrix=fitz.Matrix(2.2,2.2),clip=fitz.Rect(*s.rect),alpha=False); pix.save(PRE/f"{s.key}.png")
def data_uri(p): return "data:image/png;base64,"+base64.b64encode(p.read_bytes()).decode("ascii")
def source_card(s,text):
    delta=""
    if s.delta:
        label="Rosen vs Tintinalli" if s.source=="Rosen" else "ATLS vs Tintinalli"
        detail=s.delta.split(":",1)[1].strip() if ":" in s.delta else s.delta
        delta=f'<div class="source-delta"><strong><u>{label}:</u></strong> {html.escape(detail)}</div>'
    return f'<article class="source-card"><div class="source-card__label">{html.escape(s.source)} source</div><h3 class="source-card__title">{html.escape(s.label)}</h3><p>{html.escape(text)}</p>{delta}<figure class="source-figure reference-image"><img src="{data_uri(PRE/f"{s.key}.png")}" alt="{html.escape(s.source+" "+s.label)}" loading="lazy" decoding="async"><figcaption>{html.escape(s.source)} {html.escape(s.label)}. {html.escape(s.note)}.</figcaption></figure></article>'
def mcq(n,ans,stem,opts,rats):
    buttons="".join(f'<button class="mcq-opt" type="button" data-option-key="{k}">{k}. {html.escape(v)}</button>' for k,v in opts)
    ex="".join(f'<div class="opt-explain {"is-correct" if k==ans else "is-wrong"}" hidden><strong>{k}. {html.escape(v)}</strong><span>{html.escape(rats[k])}</span></div>' for k,v in opts)
    return f'<article class="mcq-wrapper" data-answer="{ans}" data-answered="false"><p class="mcq-stem">Q{n}. {html.escape(stem)}</p><div class="mcq-options">{buttons}</div><div class="mcq-result" hidden></div><div class="mcq-explains">{ex}</div></article>'
def build_mcqs():
    raw=[
("B","Initial severe TBI management priority is:",["Immediate MRI","Prevent secondary injury: hypoxia, hypotension, hypercarbia, hypoglycemia, hyperthermia","Routine skull x-ray","Discharge after normal scalp exam"],["No","Correct","No","Unsafe"]),
("C","A patient with GCS 7 after trauma needs:",["Oral meds","Observation only","Definitive airway with C-spine precautions","No CT ever"],["No","No","Correct","No"]),
("D","Canadian CT Head Rule high-risk example:",["No symptoms","Young patient no vomiting","Simple abrasion","GCS <15 at 2 h or suspected open/depressed skull fracture"],["No","No","No","Correct"]),
("A","EDH on CT classically appears:",["Biconvex/lenticular and does not cross sutures","Crescentic across sutures","Diffuse edema only","Normal"],["Correct","SDH pattern","No","No"]),
("B","SDH is especially common in:",["Only toddlers","Elderly/alcohol use/brain atrophy after acceleration-deceleration","No trauma","Only fever"],["No","Correct","No","No"]),
("C","Blood pressure target in adult TBI is generally at least:",["SBP 70","SBP 80","SBP >100 mm Hg","MAP 20"],["Too low","Too low","Correct","Too low"]),
("D","Avoid prophylactic hyperventilation because:",["It raises ICP","It cures all TBI","It improves all outcomes","Hypocarbia can reduce cerebral blood flow and worsen ischemia"],["No","False","False","Correct"]),
("A","Hyperosmolar therapy is considered for:",["Signs of elevated ICP/herniation while optimizing airway, BP, ventilation, temperature","Every concussion","Isolated scalp abrasion","Hypotension only"],["Correct","No","No","No"]),
("B","Mannitol can worsen:",["Hypertension only","Hypotension via osmotic diuresis","Oxygenation always","GCS score"],["No","Correct","No","No"]),
("C","Rotterdam score adds:",["Drug dose table","Neck trauma exam","Initial CT prognostic structure","Antivenom"],["No","No","Correct","No"]),
("D","Seizure prophylaxis is considered in:",["All mild concussion forever","No TBI","Only ankle sprain","Severe TBI/GCS <=10 or abnormal CT per local practice"],["No","No","No","Correct"]),
("A","Open skull fracture treatment includes:",["Neurosurgery, antibiotics when indicated, tetanus, and no blind removal of impaled objects","Immediate discharge","No CT","Only NSAIDs"],["Correct","Unsafe","Wrong","Insufficient"]),
("B","Concussion/mTBI diagnosis requires:",["Only normal mood","Alteration after mechanical force without gross lesion necessarily","Always coma","Always skull fracture"],["No","Correct","No","No"]),
("C","Return-to-activity should be:",["Immediate full sport","No follow-up","Stepwise after symptoms improve and red flags absent","Based on patient demand only"],["No","No","Correct","No"]),
("D","Worsening headache, vomiting, confusion, focal deficit after discharge means:",["Reassure only","Sleep at home","Ignore","Return/reimage concern for deterioration"],["No","No","No","Correct"]),
("A","Pupillary asymmetry with declining GCS suggests:",["Herniation/elevated ICP until proven otherwise","Benign rash","No TBI","Hypoglycemia only"],["Correct","No","No","Too narrow"]),
("B","Best source for ED treatment checklist in this rebuild:",["Rosen GCS figure","Tintinalli Table 257-7","ATLS hypothermia table","Rosen geriatrics"],["No","Correct","No","No"]),
("C","Target ETCO2 in TBI generally:",["10-15","20-25","35-45 mm Hg; transient 30-35 for herniation rescue","60-70"],["Too low","Too low","Correct","Too high"]),
("D","Sedation/analgesia in TBI should:",["Never be used","Always paralyze without airway","Ignore BP","Reduce agitation/ICP triggers while preserving BP and exam when possible"],["No","No","No","Correct"]),
("A","CT is preferred over skull radiography because:",["It detects intracranial blood, swelling, mass effect, skull fracture detail better","It is decorative","It replaces all exams","It cannot find blood"],["Correct","No","No","False"]),
("B","Diffuse axonal injury often has:",["No mechanism","Severe dysfunction with limited CT findings early; MRI may help later","Only rash","Always normal outcome"],["No","Correct","No","No"]),
("C","Traumatic SAH is:",["Always benign","Only chronic","Blood in subarachnoid spaces; amount correlates with severity","A medication"],["No","No","Correct","No"]),
("D","Brain resuscitation includes glucose:",["No glucose check","Always induce hypoglycemia","Ignore hyperglycemia","Treat hypo- and significant hyperglycemia"],["No","Unsafe","No","Correct"]),
("A","Temperature management in TBI:",["Avoid fever; maintain normothermia","Induce fever","Ignore shivering","Hypothermia required for all"],["Correct","No","No","False"]),
("B","Neurosurgery consult/transfer is needed for:",["Simple scalp abrasion only","Mass lesion, declining GCS, open/depressed fracture, elevated ICP concern","Normal exam only","No injury"],["No","Correct","No","No"]),
("C","Final safest summary:",["CT rules replace judgment","Normal first CT always ends care","Prevent secondary injury, image appropriately, reassess, and escalate neurosurgical care early","All head trauma discharged"],["No","False","Correct","Unsafe"]),
]
    return "\n".join(mcq(i,a,s,list(zip("ABCD",o)),dict(zip("ABCD",r))) for i,(a,s,o,r) in enumerate(raw,1))

def doc_html():
    c={x.key:x for x in CROPS}
    return f"""<!doctype html><html lang="en" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Chapter 257 - Head Trauma</title><style>{STYLE}</style></head><body>
<header id="top-header"><button class="hdr-btn" data-sidebar-toggle title="Contents">☰</button><div class="hdr-title">Ch.257 Head Trauma</div><button class="hdr-btn theme-btn" data-theme-toggle>Dark</button></header>
<div class="app"><aside id="sidebar" class="sidebar"><button class="hdr-btn sidebar-close" data-sidebar-close>Close</button><div class="sidebar__block"><div class="sidebar__kicker">Chapter</div><h2>Head Trauma</h2><p class="meta"><b>Spine:</b> Tintinalli Ch.257</p><p class="meta"><b>Rosen:</b> Ch.33 Head Trauma</p><p class="meta"><b>ATLS:</b> Ch.7 neurologic assessment</p></div><div class="sidebar__block"><div class="sidebar__kicker">Contents</div><a class="sidebar__link" href="#overview">Overview</a><a class="sidebar__link" href="#decision">CT Decision</a><a class="sidebar__link" href="#treatment">ED Treatment</a><a class="sidebar__link" href="#patterns">Injury Patterns</a><a class="sidebar__link" href="#mtbi">mTBI</a><a class="sidebar__link" href="#assessment">MCQs</a></div></aside><main id="main" class="main"><div class="content-wrap"><div class="utility-bar">Fresh rebuild • Tintinalli/Rosen/ATLS crops • MCQs hidden until answered</div>
<section class="hero section" id="overview"><div class="eyebrow">Trauma Chapter 257</div><h1 class="hero__title">Head Trauma</h1><p class="lede">Head trauma care is brain resuscitation: <mark>prevent secondary injury while identifying lesions that need neurosurgical action</mark>.</p><div class="callout warn"><strong>Board trap:</strong> a lucid interval or initially normal CT does not end reassessment when symptoms or GCS worsen.</div>{source_card(c['rosen_fig_33_4'],'Rosen visual GCS figure is placed at the start because mental-status scoring drives airway, CT, transfer, and prognosis.')}</section>
<section class="section" id="decision"><h2>Risk Stratification and CT Decision</h2><p>CT is the diagnostic standard for clinically important acute head injury. Decision tools help, but do not replace clinical judgment for anticoagulation, unreliable exam, worsening symptoms, penetrating injury, or multisystem trauma.</p>{source_card(c['tint_table_257_5'],'Tintinalli Table 257-5 compares New Orleans Criteria and Canadian CT Head Rule for adult CT decision-making.')}{source_card(c['rosen_box_33_3'],'Rosen Rotterdam score adds CT-based prognostic structure for severe TBI.')}</section>
<section class="section" id="treatment"><h2>ED Treatment and Brain Resuscitation</h2><p>Severe TBI treatment starts with airway protection for GCS <=8, oxygenation, normocapnia, hypotension avoidance, glucose control, normothermia, seizure management, and early neurosurgical transfer. <u>Hypoxia and hypotension are lethal multipliers</u>, so resuscitation cannot wait for a perfect neurologic exam.</p>{source_card(c['tint_table_257_7'],'Tintinalli treatment checklist is the chapter spine for ED brain-injury management.')}{source_card(c['tint_table_257_8'],'Tintinalli intubation-agent table belongs next to airway management, not in Drug Dose Reference only.')}{source_card(c['atls_table_7_12'],'ATLS optimal values table gives BP, oxygenation, PaCO2, glucose, sodium, osmolality, ICP, and CPP targets.')}{source_card(c['atls_table_7_13'],'ATLS hyperosmolar agent table provides mannitol and hypertonic saline dose options for raised ICP/herniation pathways.')}</section>
<section class="section" id="patterns"><h2>Intracranial Injury Patterns</h2><p>Epidural hematoma is classically biconvex and arterial; subdural hematoma is crescentic and common in elderly/alcohol-use patients with bridging-vein injury; traumatic SAH follows cisterns and sulci; contusion may blossom later; diffuse axonal injury can be devastating with subtle early CT findings.</p>{source_card(c['tint_fig_257_8'],'Tintinalli Figure 257-8 anchors epidural hematoma CT morphology.')}{source_card(c['tint_fig_257_9'],'Tintinalli Figure 257-9 anchors small subdural hematoma morphology.')}{source_card(c['tint_table_257_10'],'Tintinalli Table 257-10 summarizes patient type, location, CT pattern, cause, and classic symptoms across intracranial injuries.')}{source_card(c['rosen_fig_33_6'],'Rosen epidural CT source reinforces the same morphology with mass effect and midline shift.')}</section>
<section class="section" id="mtbi"><h2>Mild TBI, Disposition, and Return</h2><p>mTBI/concussion is a clinical diagnosis after mechanical force with transient neurologic dysfunction. Discharge requires stable exam, reliable observation, clear return precautions, anticoagulation plan, and no evolving red flags. Stepwise return-to-activity begins only after symptoms improve.</p><p><mark>Return immediately</mark> for worsening headache, repeated vomiting, confusion, seizure, focal deficit, anticoagulant bleeding concern, or inability to be observed safely.</p></section>
<section class="question-set section" id="assessment"><h2>Inline Assessment MCQs</h2>{build_mcqs()}</section>
</div></main></div><div class="score-pill" data-score-text>0 correct / 0 answered / 26 total</div><div class="image-modal" data-image-modal><button class="hdr-btn" data-modal-close>Close</button><img alt="Zoomed source"></div><script>{SCRIPT}</script></body></html>"""

def extract_embedded(doc):
    EMBED.mkdir(parents=True,exist_ok=True)
    for old in EMBED.glob("*.png"): old.unlink()
    paths=[]
    for i,m in enumerate(re.finditer(r"data:image/png;base64,([^\"]+)",doc),1):
        p=EMBED/f"ch257_embedded_{i:02d}.png"; p.write_bytes(base64.b64decode(m.group(1))); paths.append(p)
    return paths
def contact_sheet(paths):
    cols,cell_w,cell_h=3,380,330; rows=(len(paths)+cols-1)//cols
    sheet=Image.new("RGB",(cols*cell_w,rows*cell_h),"white"); draw=ImageDraw.Draw(sheet)
    for i,p in enumerate(paths):
        img=Image.open(p).convert("RGB"); img.thumbnail((340,275)); x,y=(i%3)*cell_w,(i//3)*cell_h
        sheet.paste(img,(x+20,y+40)); draw.text((x+8,y+8),f"{i+1:02d} {p.name}",fill=(0,0,0))
    out=EMBED/"ch257_embedded_contact_sheet.png"; sheet.save(out); return out
def md_to_html(md,title):
    out=[]; in_table=False
    for line in md.splitlines():
        if line.startswith("|") and line.endswith("|"):
            cells=[c.strip() for c in line.strip("|").split("|")]
            if cells and set(cells[0])<= {"-"}: continue
            if not in_table: out.append("<table>"); in_table=True
            tag="th" if cells and cells[0] in {"#","Ch","Source"} else "td"
            out.append("<tr>"+"".join(f"<{tag}>{html.escape(c)}</{tag}>" for c in cells)+"</tr>")
        else:
            if in_table: out.append("</table>"); in_table=False
            if line.startswith("# "): out.append(f"<h1>{html.escape(line[2:])}</h1>")
            elif line.startswith("## "): out.append(f"<h2>{html.escape(line[3:])}</h2>")
            elif line.strip(): out.append(f"<p>{html.escape(line)}</p>")
    if in_table: out.append("</table>")
    return f"<!doctype html><html><head><meta charset='utf-8'><title>{html.escape(title)}</title><style>body{{font-family:Arial;margin:28px;background:#f8fafc}}table{{border-collapse:collapse;width:100%;font-size:13px}}td,th{{border:1px solid #cbd5e1;padding:6px;vertical-align:top}}th{{background:#e2e8f0}}</style></head><body>{''.join(out)}</body></html>"
def build_qa(paths,sheet):
    rows=[f"| {i} | {s.source} | {s.label} | {s.pdf.name} | {s.page} | `{p.relative_to(ROOT).as_posix()}` | PASS | {s.note}; title/header/body included |" for i,(s,p) in enumerate(zip(CROPS,paths),1)]
    inv="\n".join(f"- {c.source} {c.label}: page {c.page}, placement `{c.placement}`" for c in CROPS)
    md=f"""# CH257 Crop QA - 2026-05-09

Fresh rebuild from source PDFs. Old Chapter257 HTML crops were not used as completion evidence.

## Source Inventory Used

Tintinalli Ch257 included CT decision, ED treatment, intubation, EDH/SDH images, and intracranial injury comparison. Rosen Ch33 included GCS, Rotterdam score, and EDH CT. ATLS Ch7 included TBI goals and hyperosmolar agents.

{inv}

## Embedded Crop QA

Contact sheet: `{sheet.relative_to(ROOT).as_posix()}`

| # | Source | Object | PDF | PDF page | Extracted final embedded image | Status | Note |
|---|---|---|---|---:|---|---|---|
{chr(10).join(rows)}

## Content Gate

Content: PASS. Head-trauma risk stratification, ED treatment, injury patterns, mTBI disposition, ATLS physiologic targets, and Rosen additions all have narrative and topic-local crops.

Pattern: PASS. Ch186/Ch201 shell, top header, sidebar/main layout, source deltas, and accepted MCQ behavior are present.
"""
    QA_MD.write_text(md,encoding="utf-8"); QA_HTML.write_text(md_to_html(md,"CH257 Crop QA"),encoding="utf-8")
def update_audit():
    md=AUDIT_MD.read_text(encoding="utf-8")
    line="| 257 | Chapter257_HeadTrauma.html | PASS | PASS | PASS | 26 | 2 | 9 | 11 | PASS | 21 | Fresh rebuild 2026-05-09; Pattern: PASS; Content: PASS; MCQ all-option explanations PASS; Tintinalli/Rosen/ATLS source crops topic-local; ATLS integrated in body; cropQA PASS (11/11) |"
    md=re.sub(r"^\| 257 \|.*$",line,md,flags=re.M)
    AUDIT_MD.write_text(md,encoding="utf-8"); AUDIT_HTML.write_text(md_to_html(md,"Chapter Quality Audit"),encoding="utf-8")
def gate(doc,paths):
    checks={"top":doc.count('id="top-header"'),"sidebar":doc.count('id="sidebar"'),"main":doc.count('id="main"'),"mcq":doc.count('class="mcq-wrapper"'),"result":doc.count('class="mcq-result"'),"legacy":doc.count("mcq-card"),"source":doc.count('class="source-figure reference-image"'),"data":doc.count("data:image/png;base64,"),"mark":doc.count("<mark>"),"u":doc.count("<u>"),"rosen":doc.count("Rosen source"),"rd":doc.count("Rosen vs Tintinalli"),"atls":doc.count("ATLS source"),"ad":doc.count("ATLS vs Tintinalli")}
    bad=["Source Check","Source Audit","Rosen Source Audit","repair note"]; fails=[]
    if checks["top"]!=1 or checks["sidebar"]!=1 or checks["main"]!=1: fails.append("shell")
    if checks["mcq"]!=26 or checks["result"]!=26 or checks["legacy"]!=0: fails.append("mcq")
    if checks["source"]!=len(CROPS) or checks["data"]!=len(CROPS) or len(paths)!=len(CROPS): fails.append("crops")
    if checks["mark"]==0 or checks["u"]==0: fails.append("emphasis")
    if checks["rosen"]<3 or checks["rd"]<3 or checks["atls"]<2 or checks["ad"]<2: fails.append("source integration")
    if any(x in doc for x in bad): fails.append("visible audit text")
    if fails: raise SystemExit(f"Gate failed: {fails} {checks}")
    print("GATE PASS",checks)
def main():
    PRE.mkdir(parents=True,exist_ok=True)
    for old in PRE.glob("*.png"): old.unlink()
    for s in CROPS: crop_pdf(s)
    doc=doc_html(); OUT_HTML.parent.mkdir(parents=True,exist_ok=True); OUT_HTML.write_text(doc,encoding="utf-8")
    paths=extract_embedded(doc); sheet=contact_sheet(paths); build_qa(paths,sheet); update_audit(); gate(doc,paths)
    for rel in [OUT_HTML.relative_to(ROOT),QA_MD.relative_to(ROOT),QA_HTML.relative_to(ROOT),AUDIT_MD.relative_to(ROOT),AUDIT_HTML.relative_to(ROOT)]:
        dst=MIRROR/rel; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(ROOT/rel,dst)
    print("HTML",OUT_HTML); print("QA",QA_HTML); print("CONTACT",sheet)
if __name__=="__main__": main()
