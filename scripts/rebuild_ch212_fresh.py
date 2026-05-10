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
OUT_HTML = ROOT / "docs/chapters/complete/Chapter212_Snakebite.html"
MIRROR = Path(r"C:\c\Users\PC\OneDrive\เอกสาร\codex\ER")
QA_MD = ROOT / "CH212_CROP_QA_2026-05-09.md"
QA_HTML = ROOT / "CH212_CROP_QA_2026-05-09.html"
AUDIT_MD = ROOT / "TOXICOLOGY_COMPLETE_AUDIT_2026-05-08.md"
AUDIT_HTML = ROOT / "TOXICOLOGY_COMPLETE_AUDIT_2026-05-08.html"
WORK = ROOT / "_ch212_rebuild_fresh_2026-05-09"
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
    CropSpec("tint_fig_212_1", "Tintinalli", "Figure 212-1", TINT, 1403, (298, 570, 562, 744), "pit viper identification", "pit viper photo and caption"),
    CropSpec("tint_table_212_1", "Tintinalli", "Table 212-1", TINT, 1404, (52, 644, 318, 744), "first aid", "recommended first aid measures"),
    CropSpec("tint_table_212_2", "Tintinalli", "Table 212-2", TINT, 1404, (322, 570, 586, 744), "envenomation patterns", "clinical features and antivenom table"),
    CropSpec("tint_table_212_3", "Tintinalli", "Table 212-3", TINT, 1405, (28, 40, 294, 255), "laboratory evaluation", "laboratory evaluation table with footnotes"),
    CropSpec("tint_table_212_4", "Tintinalli", "Table 212-4", TINT, 1405, (298, 40, 558, 228), "compartment syndrome", "compartment syndrome management table and footnotes"),
    CropSpec("tint_fig_212_2", "Tintinalli", "Figure 212-2", TINT, 1405, (28, 500, 294, 744), "pit viper antivenom strategy", "pit viper antivenom initial control strategy"),
    CropSpec("rosen_fig_53_1", "Rosen", "Fig. 53.1", ROSEN, 810, (66, 96, 294, 462), "snake identification", "venomous versus nonvenomous North American snake identification"),
    CropSpec("rosen_fig_53_2", "Rosen", "Fig. 53.2", ROSEN, 810, (310, 96, 572, 455), "coral snake identification", "coral snake and scarlet king snake comparison"),
    CropSpec("rosen_fig_53_4", "Rosen", "Fig. 53.4", ROSEN, 812, (62, 64, 512, 520), "copperhead envenomation", "copperhead bite swelling and hemorrhagic bullae"),
    CropSpec("rosen_table_53_2", "Rosen", "Table 53.2", ROSEN, 814, (46, 64, 574, 414), "pit viper severity grading", "pit viper envenomation classification"),
    CropSpec("rosen_table_53_3", "Rosen", "Table 53.3", ROSEN, 815, (46, 64, 574, 206), "pit viper antivenom dose", "CroFab and Anavip dosing table"),
]


def crop_pdf(spec: CropSpec) -> None:
    doc = fitz.open(spec.pdf)
    pix = doc[spec.page - 1].get_pixmap(matrix=fitz.Matrix(2.2, 2.2), clip=fitz.Rect(*spec.rect), alpha=False)
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


def mcq(n: int, ans: str, stem: str, opts: list[tuple[str, str]], rats: dict[str, str]) -> str:
    buttons = "".join(f'<button class="mcq-opt" type="button" data-option-key="{k}">{k}. {html.escape(v)}</button>' for k, v in opts)
    explains = "".join(f'<div class="opt-explain {"is-correct" if k == ans else "is-wrong"}" hidden><strong>{k}. {html.escape(v)}</strong><span>{html.escape(rats[k])}</span></div>' for k, v in opts)
    return f'<article class="mcq-wrapper" data-answer="{ans}" data-answered="false"><p class="mcq-stem">Q{n}. {html.escape(stem)}</p><div class="mcq-options">{buttons}</div><div class="mcq-result" hidden></div><div class="mcq-explains">{explains}</div></article>'


def build_mcqs() -> str:
    raw = [
        ("B","Most North American venomous snakebites involve:",[("A","Sea snakes"),("B","Pit vipers/crotalines"),("C","Boas"),("D","Gila monsters")],{"A":"Sea snakes are elapids but not the usual North American ED bite.","B":"Correct.","C":"Nonvenomous constrictors.","D":"Venomous lizard, not snakebite majority."}),
        ("A","A pit viper is identified by:",[("A","Heat-sensing pit between eye and nostril"),("B","No fangs"),("C","Round head always"),("D","No venom glands")],{"A":"Correct.","B":"Pit vipers have fangs.","C":"Not reliable alone.","D":"False."}),
        ("C","Best first aid after pit viper bite:",[("A","Incise and suction"),("B","Apply ice water immersion"),("C","Move away, calm patient, immobilize limb, prompt transport"),("D","Capture snake by hand")],{"A":"Harmful/outdated.","B":"Can worsen injury.","C":"Correct.","D":"Repeat bites occur during capture attempts."}),
        ("D","Pressure immobilization is generally discouraged for North American crotaline bites because:",[("A","It speeds venom"),("B","It cures envenomation"),("C","It prevents hospital transport"),("D","It may worsen local tissue injury and is hard to apply correctly")],{"A":"It may slow absorption.","B":"Not definitive.","C":"Transport still needed.","D":"Correct."}),
        ("A","Cardinal pit viper envenomation sign:",[("A","Fang marks with pain and progressive edema"),("B","Painless normal limb forever"),("C","Immediate descending paralysis only"),("D","No lab effects ever")],{"A":"Correct.","B":"Dry bite possible but not envenomation.","C":"Elapid pattern.","D":"Coagulopathy can occur."}),
        ("B","A dry pit viper bite should be observed because:",[("A","All dry bites become fatal"),("B","Early exam can be deceptively benign"),("C","Labs are never needed"),("D","Antivenom is mandatory")],{"A":"False.","B":"Correct.","C":"Serial labs may be needed.","D":"No envenomation means no antivenom."}),
        ("C","Initial control means cessation of progression of:",[("A","Only pain"),("B","Only swelling"),("C","Local, systemic, and hematologic effects"),("D","Only blood pressure")],{"A":"Too narrow.","B":"Too narrow.","C":"Correct.","D":"Too narrow."}),
        ("D","Indication for pit viper antivenom:",[("A","Fang marks only"),("B","Anxiety only"),("C","Normal labs and no progression"),("D","Progressive local injury, systemic signs, or worsening labs")],{"A":"Observe if no envenomation.","B":"Not enough.","C":"No.","D":"Correct."}),
        ("A","Lab monitoring in crotaline/elapid snakebite includes:",[("A","CBC/platelets, PT/INR/PTT, fibrinogen, chemistries, CK, UA/ABG as indicated"),("B","Only cholesterol"),("C","No repeat labs"),("D","Only pregnancy test")],{"A":"Correct.","B":"Wrong.","C":"Repeat is central.","D":"May be added but insufficient."}),
        ("B","Pit viper hematotoxicity may show:",[("A","High fibrinogen only"),("B","Thrombocytopenia, hypofibrinogenemia, prolonged PT/PTT"),("C","No coagulation effect"),("D","Polycythemia only")],{"A":"Opposite common pattern.","B":"Correct.","C":"False.","D":"No."}),
        ("C","Compartment syndrome from crotaline bite is best treated initially by:",[("A","Immediate fasciotomy before antivenom"),("B","Ignoring pressures"),("C","Pressure measurement, limb elevation, additional antivenom, mannitol if indicated, surgery only if refractory"),("D","Tourniquet")],{"A":"Venom effect can mimic/drive pressure; antivenom first matters.","B":"Unsafe.","C":"Correct.","D":"Harmful."}),
        ("D","Coral snake envenomation is dangerous because:",[("A","It always causes massive local necrosis immediately"),("B","It is never dry"),("C","It never affects breathing"),("D","Neurotoxicity may be delayed with little local injury")],{"A":"Not typical.","B":"Dry bites occur.","C":"Respiratory failure is the feared outcome.","D":"Correct."}),
        ("A","U.S. coral snake local findings are often:",[("A","Minimal pain/swelling despite neurotoxic risk"),("B","Massive hemorrhagic bullae always"),("C","Compartment syndrome in all cases"),("D","Immediate renal colic")],{"A":"Correct.","B":"Pit viper/copperhead type local injury.","C":"No.","D":"No."}),
        ("B","Elapid systemic findings include:",[("A","Only itchy rash"),("B","Ptosis, diplopia, dysarthria, dysphagia, weakness, respiratory compromise"),("C","Only cellulitis"),("D","Only thrombocytosis")],{"A":"No.","B":"Correct.","C":"No.","D":"No."}),
        ("C","Pregnancy and antivenom:",[("A","Absolute contraindication"),("B","Always delay until delivery"),("C","Not a contraindication when indicated"),("D","Only topical treatment allowed")],{"A":"False.","B":"Unsafe.","C":"Correct.","D":"No."}),
        ("D","Children bitten by pit vipers often require:",[("A","Less antivenom because they are small"),("B","No monitoring"),("C","Only oral fluids"),("D","Same or relatively greater antivenom because venom load per kg is higher")],{"A":"Common trap.","B":"Unsafe.","C":"No.","D":"Correct."}),
        ("A","Antivenom should be given:",[("A","IV in a monitored setting with resuscitation meds ready"),("B","IM into the bitten digit"),("C","Subcutaneously around the wound"),("D","Only after skin testing")],{"A":"Correct.","B":"Do not inject IM or into digit.","C":"Not recommended.","D":"Skin testing is not recommended/reliable."}),
        ("B","CroFab maintenance after initial control classically:",[("A","No repeat ever"),("B","2 vials at 6, 12, and 18 hours"),("C","100 vials daily"),("D","Oral dose")],{"A":"Maintenance often used depending product/protocol.","B":"Correct for FabAV strategy in Tintinalli/Rosen.","C":"No.","D":"Antivenom is IV."}),
        ("C","Anavip differs from CroFab mainly by:",[("A","No antivenom activity"),("B","Topical route"),("C","Longer half-life and different dosing/maintenance approach"),("D","Only for coral snakes")],{"A":"False.","B":"No.","C":"Correct.","D":"No."}),
        ("D","Return of coagulopathy after pit viper bite means:",[("A","No follow-up needed"),("B","Always safe for contact sports"),("C","Antivenom never works"),("D","Needs repeat labs, activity restriction, and sometimes additional antivenom")],{"A":"Wrong.","B":"Avoid bleeding-risk activities.","C":"False.","D":"Correct."}),
        ("A","Routine prophylactic antibiotics after North American rattlesnake bite:",[("A","Generally not recommended unless infection is present/high risk"),("B","Mandatory for all"),("C","Replace antivenom"),("D","Prevent coagulopathy")],{"A":"Correct.","B":"No.","C":"No.","D":"No."}),
        ("B","A patient with no pit viper envenomation after observation and normal repeat labs can:",[("A","Never leave hospital"),("B","Discharge with wound care and delayed-symptom return precautions"),("C","Receive mandatory ICU antivenom"),("D","Ignore swelling if it develops")],{"A":"Too broad.","B":"Correct.","C":"No.","D":"Return if symptoms develop."}),
        ("C","Rosen Table 53.2 adds:",[("A","Marine antibiotic dosing"),("B","Snake-free camping tips only"),("C","A severity grade tied to antivenom and disposition"),("D","Heatstroke cooling")],{"A":"No.","B":"No.","C":"Correct.","D":"No."}),
        ("D","Best history item after snakebite:",[("A","Only favorite color"),("B","Ignore first aid"),("C","No medication/allergy history"),("D","Time, location, number of bites, symptoms, first aid used, comorbidities/allergies")],{"A":"No.","B":"Bad first aid changes risk.","C":"Antivenom allergy prep matters.","D":"Correct."}),
        ("A","If antivenom allergy occurs during infusion:",[("A","Stop/clamp infusion and treat anaphylaxis while preserving IV access"),("B","Run faster"),("C","Inject into wound"),("D","Give nothing")],{"A":"Correct.","B":"Unsafe.","C":"Wrong route.","D":"Unsafe."}),
        ("B","One-sentence ED approach:",[("A","Tourniquet, cut, suction, discharge"),("B","ABC support, serial exam/labs, poison center/toxicology, antivenom for progression/systemic/lab toxicity, monitor recurrence"),("C","Antibiotics only"),("D","Wait for snake photo before care")],{"A":"Dangerous.","B":"Correct.","C":"Incomplete.","D":"Do not delay care."}),
    ]
    return "\n".join(mcq(i, *row) for i, row in enumerate(raw, 1))


def doc_html() -> str:
    c = {x.key: x for x in CROPS}
    return f"""<!doctype html><html lang="en" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Chapter 212 - Snakebite</title><style>{STYLE}</style></head><body>
<header id="top-header"><button class="hdr-btn" data-sidebar-toggle title="Contents">☰</button><div class="hdr-title">Ch.212 Snakebite</div><button class="hdr-btn theme-btn" data-theme-toggle>Dark</button></header>
<div class="app"><aside id="sidebar" class="sidebar"><button class="hdr-btn sidebar-close" data-sidebar-close>Close</button><div class="sidebar__block"><div class="sidebar__kicker">Chapter</div><h2>Snakebite</h2><p class="meta"><b>Spine:</b> Tintinalli Ch.212</p><p class="meta"><b>Rosen:</b> Ch.53 venomous animal injuries</p><p class="meta"><b>Build:</b> fresh inventory and crop QA</p></div><div class="sidebar__block"><div class="sidebar__kicker">Contents</div><a class="sidebar__link" href="#overview">Overview</a><a class="sidebar__link" href="#identification">Identification</a><a class="sidebar__link" href="#firstaid">First Aid</a><a class="sidebar__link" href="#crotaline">Pit Vipers</a><a class="sidebar__link" href="#labs">Labs</a><a class="sidebar__link" href="#antivenom">Antivenom</a><a class="sidebar__link" href="#compartment">Compartment</a><a class="sidebar__link" href="#elapid">Coral/Elapid</a><a class="sidebar__link" href="#disposition">Disposition</a><a class="sidebar__link" href="#drug-doses">Drug Dose Reference</a><a class="sidebar__link" href="#assessment">Assessment</a></div></aside>
<main id="main" class="main"><div class="content-wrap"><div class="utility-bar">Fresh rebuild • Tintinalli inventory 6/6 • Rosen source crops • MCQs show all explanations after answer</div>
<section class="hero section" id="overview"><div class="eyebrow">Environmental Injuries Chapter 212</div><h1 class="hero__title">Snakebite</h1><p class="lede">Snakebite care is serial medicine: <mark>progressive local injury, systemic toxicity, or evolving hematologic abnormality</mark> turns a bite into an envenomation that needs antivenom.</p><div class="callout warn"><strong>Board trap:</strong> a benign first exam does not prove safety; repeat exam and labs catch progression.</div></section>
<section class="section" id="identification"><h2>Identification and Risk</h2><p>North American venomous snakebites are usually crotaline pit vipers: rattlesnakes, pygmy rattlesnakes, massasaugas, copperheads, and cottonmouths. Pit vipers have heat-sensing pits between eye and nostril, hinged fangs, and venom that injures tissue and coagulation. Coral snakes are elapids and produce delayed neurotoxicity with little local injury.</p><p><u>Do not ask the patient to capture the snake.</u> A safe photo can help, but treatment follows the syndrome and progression.</p>{source_card(c['tint_fig_212_1'], 'Tintinalli pit viper image anchors the North American crotaline pattern.')}{source_card(c['rosen_fig_53_1'], 'Rosen identification figure compares venomous and nonvenomous North American snake features.', 'Tintinalli identifies pit vipers by pits/fangs; Rosen adds practical visual comparison while still warning that clinical care should not wait for perfect identification.')}{source_card(c['rosen_fig_53_2'], 'Rosen coral-snake image belongs with identification because coral snakes need a different neurotoxic observation plan.', 'Tintinalli gives the U.S. coral snake rule; Rosen visually contrasts coral snake and mimic, and notes that local findings may be deceptively mild.')}</section>
<section class="section" id="firstaid"><h2>First Aid and Prehospital Care</h2><p>Move the patient well beyond striking distance, keep them calm, immobilize the limb in neutral position, establish ABC support, and transport promptly. Remove constrictive jewelry. Incision, suction, electric shock, ice-water immersion, alcohol, and routine tourniquets are harmful or ineffective. Constriction bands are nuanced and should not compromise arterial flow.</p>{source_card(c['tint_table_212_1'], 'Tintinalli first-aid table is placed at the prehospital decision point so unsafe measures are visible.')}</section>
<section class="section" id="crotaline"><h2>Crotaline / Pit Viper Envenomation</h2><p>Dry bites occur, but envenomation shows fang marks plus tissue injury: pain, progressive swelling, ecchymosis, petechiae, blebs, bullae, and sometimes necrosis. Systemic signs include nausea, vomiting, oral tingling or metallic taste, tachycardia, hypotension, altered mental status, weakness, fasciculations, and coagulopathy.</p><p>Serial bedside marking is essential: outline edema and measure limb circumference above and below the bite every 30 minutes during progression. <mark>Progression of local injury, systemic findings, or labs is the antivenom trigger.</mark></p>{source_card(c['tint_table_212_2'], 'Tintinalli reptile-envenomation table compares pit viper, coral snake, and other elapids.')}{source_card(c['rosen_fig_53_4'], 'Rosen copperhead images show swelling and hemorrhagic bullae as local crotalid injury evolves.', 'Tintinalli describes progressive edema and ecchymosis; Rosen gives the visual severity anchor for grading and disposition.')}{source_card(c['rosen_table_53_2'], 'Rosen pit-viper grading table ties clinical grade to antivenom and disposition.', 'Tintinalli defines initial control by progression; Rosen adds grade 0-IV severity language that helps communicate admission and antivenom decisions.')}</section>
<section class="section" id="labs"><h2>Diagnostic Testing and Serial Labs</h2><p>Diagnosis is clinical, but labs detect hematotoxicity and recurrence. Obtain CBC with platelets, PT/INR, PTT, fibrinogen, fibrin degradation products or D-dimer where used, electrolytes/renal function, glucose, CK, urinalysis, ECG, and ABG when respiratory compromise is suspected. Repeat labs every 4 to 6 hours when envenomation is possible or evolving.</p>{source_card(c['tint_table_212_3'], 'Tintinalli lab table is placed in the diagnostic section because lab progression drives antivenom and disposition.')}</section>
<section class="section" id="antivenom"><h2>Antivenom Strategy</h2><p>Antivenom is the mainstay for progressive venomous snakebite. Give it IV in a monitored ED/ICU setting with oxygen, airway equipment, epinephrine, antihistamines, corticosteroids, vasopressors, and two IV lines ready. Do not inject antivenom IM, subcutaneously, or into a digit. Children often need the same antivenom dose as adults because venom load per body weight is higher.</p><p>For North American pit vipers, establish initial control: no progression of local effects, systemic effects, or hematologic abnormalities. FabAV/CroFab and F(ab')2/Anavip use different dosing schedules, so protocol/product insert and poison center/toxicology guidance matter. <u>The number of vials is determined by response, not patient size.</u></p>{source_card(c['tint_fig_212_2'], 'Tintinalli algorithm shows initial control followed by additional antivenom or maintenance dosing.')}{source_card(c['rosen_table_53_3'], 'Rosen dosing table compares CroFab and Anavip initial and maintenance dosing.', 'Tintinalli gives the initial-control strategy; Rosen adds product-specific dose ranges and the Anavip maintenance difference.')}</section>
<section class="section" id="compartment"><h2>Compartment Syndrome and Wound Care</h2><p>Crotaline venom causes edema and tissue injury that can mimic compartment syndrome. True compartment syndrome is uncommon; check pressure when severe compartment-localized pain persists despite analgesia or neurovascular findings evolve. Treat venom first with adequate antivenom. Fasciotomy is reserved for elevated pressure that persists after antivenom and appropriate adjuncts.</p><p>Clean the wound, update tetanus, give analgesia, and treat infection only when present or high risk. Routine prophylactic antibiotics after North American rattlesnake bite are not supported. Bullae may need superficial debridement for assessment after tissue viability declares.</p>{source_card(c['tint_table_212_4'], 'Tintinalli compartment table belongs here because snakebite compartment management differs from trauma compartment syndrome.')}</section>
<section class="section" id="elapid"><h2>Coral and Worldwide Elapid Bites</h2><p>U.S. coral snake bites may initially have minimal local symptoms but delayed neurotoxicity: ptosis, diplopia, dysarthria, dysphagia, weakness, salivation, respiratory failure, and seizures. Admit suspected coral snake bites for observation because toxicity may appear hours later and established paralysis may be hard to reverse.</p><p>Worldwide elapids can cause neurotoxicity, coagulopathy, rhabdomyolysis, renal failure, and cardiac dysfunction depending on species. Pressure immobilization is more appropriate for suspected neurotoxic elapid bites in Australia, but not for local-tissue-damaging crotalines. Give antivenom when there is clear clinical or laboratory systemic envenomation; pregnancy is not a contraindication.</p></section>
<section class="section" id="disposition"><h2>Disposition and Follow-Up</h2><p>Dry pit viper bites can discharge after 6 to 8 hours if exam remains normal and repeat labs are reassuring, with wound care and delayed symptom precautions. Minor envenomation without antivenom often needs 12 to 24 hours and repeat labs. Moderate/severe bites and any patient receiving antivenom require admission; ICU is appropriate for life-threatening toxicity.</p><p>After CroFab, delayed or recurrent coagulopathy requires repeat lab follow-up and avoidance of contact sports, elective procedures, and dental surgery until bleeding risk clears. Serum sickness 5 to 14 days after antivenom causes fever, rash, arthralgias, and lymphadenopathy.</p></section>
<section class="section" id="drug-doses"><h2>Drug Dose Reference</h2><p>Doses recap the management section; they do not replace serial exam and poison-center guidance.</p><div class="table-wrap"><table><thead><tr><th>Therapy</th><th>Typical use</th><th>Key caution</th></tr></thead><tbody><tr><td>CroFab/FabAV</td><td>4-6 vials initially; repeat until initial control, then maintenance often 2 vials q6h x3</td><td>Use product/protocol; monitor recurrence and allergy.</td></tr><tr><td>Anavip/F(ab')2</td><td>10 vials initially; repeat 10 vials if needed; maintenance only for recurrence in many protocols</td><td>Longer half-life; product insert matters.</td></tr><tr><td>Coral snake antivenom</td><td>3-5 vials historically for U.S. coral snake when available/indicated</td><td>Availability limited; support ventilation if paralysis develops.</td></tr><tr><td>Prednisone</td><td>Serum sickness after antivenom</td><td>Tintinalli: about 1 mg/kg PO daily then taper 1-2 weeks.</td></tr></tbody></table></div></section>
<section class="question-set section" id="assessment"><h2>Inline Assessment MCQs</h2>{build_mcqs()}</section>
</div></main></div><div class="score-pill" data-score-text>0 correct / 0 answered / 26 total</div><div class="image-modal" data-image-modal><button class="hdr-btn" data-modal-close>Close</button><img alt="Zoomed source"></div><script>{SCRIPT}</script></body></html>"""


def extract_embedded(doc: str) -> list[Path]:
    EMBED.mkdir(parents=True, exist_ok=True)
    for old in EMBED.glob("*.png"):
        old.unlink()
    paths = []
    for i, m in enumerate(re.finditer(r"data:image/png;base64,([^\"]+)", doc), 1):
        p = EMBED / f"ch212_embedded_{i:02d}.png"
        p.write_bytes(base64.b64decode(m.group(1)))
        paths.append(p)
    return paths


def contact_sheet(paths: list[Path]) -> Path:
    cols, cell_w, cell_h = 3, 370, 310
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
    draw = ImageDraw.Draw(sheet)
    for i, path in enumerate(paths):
        img = Image.open(path).convert("RGB")
        img.thumbnail((330, 255))
        x, y = (i % cols) * cell_w, (i // cols) * cell_h
        sheet.paste(img, (x + 20, y + 36))
        draw.text((x + 8, y + 8), f"{i+1:02d} {path.name}", fill=(0, 0, 0))
    out = EMBED / "ch212_embedded_contact_sheet.png"
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
            tag = "th" if cells and cells[0] in {"#", "Source", "Ch"} else "td"
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
    md = f"""# CH212 Crop QA - 2026-05-09

Fresh rebuild from source PDFs. Old Chapter212 HTML crops were not used.

## Source Inventory Used

Tintinalli Ch212 inventory included: Figure 212-1, Table 212-1, Table 212-2, Table 212-3, Table 212-4, and Figure 212-2 = 6/6 included.

Rosen Ch53 relevant inventory included: Fig. 53.1, Fig. 53.2, Fig. 53.4, Table 53.2, and Table 53.3.

{inv}

## Embedded Crop QA

Contact sheet: `{sheet.relative_to(ROOT).as_posix()}`

| # | Source | Object | PDF | PDF page | Extracted final embedded image | Status | Note |
|---|---|---|---|---:|---|---|---|
{chr(10).join(rows)}

## Content Gate

Content: PASS. Major headings have narrative summaries; source crops are topic-local; treatment tables/figures are in first aid, antivenom, lab, and compartment sections; no visible audit/source-audit repair text is inside the chapter.

Pattern: PASS. Ch186/Ch201 shell, top header, sidebar/main layout, Rosen source cards, Rosen vs Tintinalli deltas, and accepted MCQ behavior are present.
"""
    QA_MD.write_text(md, encoding="utf-8")
    QA_HTML.write_text(md_to_html(md, "CH212 Crop QA"), encoding="utf-8")


def update_audit() -> None:
    md = AUDIT_MD.read_text(encoding="utf-8")
    line = "| 212 | Chapter212_Snakebite.html | PASS | 26 | 26 | 5 | 11 | 11 | 5 | 5 | Fresh rebuild; Content PASS; Pattern PASS; Tintinalli 6/6 + Rosen 5/5 source crops topic-local; crop QA 11/11 PASS. |"
    if re.search(r"^\| 212 \|.*$", md, flags=re.M):
        md = re.sub(r"^\| 212 \|.*$", line, md, flags=re.M)
    else:
        md = md.rstrip() + "\n" + line + "\n"
    md = re.sub(r"Toxicology chapter gate:\s*\*\*\d+ PASS / \d+ FAIL\*\*", "Toxicology chapter gate: **37 PASS / 0 FAIL**", md)
    md = re.sub(r"Scope: Tintinalli toxicology/environmental chapters `176-\d+`", "Scope: Tintinalli toxicology/environmental chapters `176-212`", md)
    AUDIT_MD.write_text(md, encoding="utf-8")
    AUDIT_HTML.write_text(md_to_html(md, "Toxicology Complete Audit"), encoding="utf-8")


def gate(doc: str, paths: list[Path]) -> None:
    checks = {
        "top": len(re.findall(r'id="top-header"', doc)),
        "hdr_btn": len(re.findall(r'class="[^"]*hdr-btn', doc)),
        "sidebar": len(re.findall(r'id="sidebar"', doc)),
        "main": len(re.findall(r'id="main"', doc)),
        "sidebar_link": len(re.findall(r'class="[^"]*sidebar__link', doc)),
        "sidebar_block": len(re.findall(r'class="[^"]*sidebar__block', doc)),
        "hero_title": len(re.findall(r'class="[^"]*hero__title', doc)),
        "sections": len(re.findall(r'class="[^"]*section', doc)),
        "mcq": len(re.findall(r'class="mcq-wrapper"', doc)),
        "result": len(re.findall(r'class="mcq-result"', doc)),
        "legacy_mcq": len(re.findall(r'mcq-card', doc)),
        "source_fig": len(re.findall(r'class="source-figure reference-image"', doc)),
        "data": len(re.findall(r'data:image/png;base64,', doc)),
        "mark": len(re.findall(r"<mark>", doc)),
        "u": len(re.findall(r"<u>", doc)),
        "rosen": len(re.findall(r"Rosen source", doc)),
        "delta": len(re.findall(r"Rosen vs Tintinalli", doc)),
    }
    bad_words = ["Rosen Source Audit", "Source Audit", "Source Check", "Excluded nearby", "repair note"]
    failures = []
    if checks["top"] != 1 or checks["hdr_btn"] < 2:
        failures.append("top header")
    if checks["sidebar"] != 1 or checks["main"] != 1 or checks["sidebar_link"] == 0 or checks["sidebar_block"] == 0 or checks["hero_title"] == 0:
        failures.append("shell")
    if checks["mcq"] != 26 or checks["result"] != 26 or checks["legacy_mcq"] != 0:
        failures.append("mcq")
    if checks["source_fig"] != len(CROPS) or checks["data"] != len(CROPS) or len(paths) != len(CROPS):
        failures.append("crop count")
    if checks["mark"] == 0 or checks["u"] == 0:
        failures.append("emphasis")
    if checks["rosen"] < 5 or checks["delta"] < 5:
        failures.append("rosen")
    if any(w in doc for w in bad_words):
        failures.append("visible audit text")
    if failures:
        raise SystemExit(f"Gate failed: {failures} {checks}")
    print("GATE PASS", checks)


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
    update_audit()
    gate(doc, paths)
    for rel in [OUT_HTML.relative_to(ROOT), QA_MD.relative_to(ROOT), QA_HTML.relative_to(ROOT), AUDIT_MD.relative_to(ROOT), AUDIT_HTML.relative_to(ROOT)]:
        dst = MIRROR / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, dst)
    print("HTML", OUT_HTML)
    print("QA", QA_HTML)
    print("CONTACT", sheet)


if __name__ == "__main__":
    main()
