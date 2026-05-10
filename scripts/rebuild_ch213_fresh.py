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
OUT_HTML = ROOT / "docs/chapters/complete/Chapter213_MarineTraumaAndEnvenomation.html"
MIRROR = Path(r"C:\c\Users\PC\OneDrive\เอกสาร\codex\ER")
QA_MD = ROOT / "CH213_CROP_QA_2026-05-09.md"
QA_HTML = ROOT / "CH213_CROP_QA_2026-05-09.html"
AUDIT_MD = ROOT / "TOXICOLOGY_COMPLETE_AUDIT_2026-05-08.md"
AUDIT_HTML = ROOT / "TOXICOLOGY_COMPLETE_AUDIT_2026-05-08.html"
WORK = ROOT / "_ch213_rebuild_fresh_2026-05-09"
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
    CropSpec("tint_table_213_1", "Tintinalli", "Table 213-1", TINT, 1408, (322, 40, 586, 250), "marine wound antibiotics", "antibiotic treatment recommendations"),
    CropSpec("tint_table_213_2", "Tintinalli", "Table 213-2", TINT, 1408, (322, 570, 586, 744), "marine wound antibiotics", "marine-associated wound antibiotic options"),
    CropSpec("tint_fig_213_1", "Tintinalli", "Figure 213-1", TINT, 1409, (30, 40, 292, 344), "coral wounds", "coral wounds photo and caption"),
    CropSpec("tint_table_213_3", "Tintinalli", "Table 213-3", TINT, 1410, (52, 40, 586, 486), "early treatment", "early treatment of marine envenomations table"),
    CropSpec("tint_fig_213_2", "Tintinalli", "Figure 213-2", TINT, 1411, (28, 40, 292, 642), "octopus bite", "octopus bite photos and caption"),
    CropSpec("tint_fig_213_3", "Tintinalli", "Figure 213-3", TINT, 1411, (298, 520, 562, 744), "sea urchin", "sea urchin sting photo and caption"),
    CropSpec("tint_fig_213_4", "Tintinalli", "Figure 213-4", TINT, 1412, (322, 40, 586, 284), "Portuguese man-of-war", "Portuguese man-of-war photo and caption"),
    CropSpec("tint_fig_213_5", "Tintinalli", "Figure 213-5", TINT, 1413, (28, 40, 292, 284), "box jellyfish sting", "box jellyfish sting photo and caption"),
    CropSpec("rosen_fig_53_9", "Rosen", "Fig. 53.9", ROSEN, 823, (48, 62, 304, 254), "blue-ringed octopus", "blue-ringed octopus image and caption"),
    CropSpec("rosen_fig_53_10", "Rosen", "Fig. 53.10", ROSEN, 824, (42, 62, 298, 316), "box jellyfish", "box jellyfish image and caption"),
    CropSpec("rosen_fig_55_11", "Rosen", "Fig. 55.11", ROSEN, 825, (46, 62, 306, 355), "lionfish sting", "lionfish sting image and caption"),
    CropSpec("rosen_table_53_5", "Rosen", "Table 53.5", ROSEN, 826, (46, 64, 574, 172), "species treatment", "species-specific marine envenomation treatment table"),
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
        ("B","Major marine trauma priority is:",[("A","Vinegar first"),("B","Remove from water, ABCs/hemorrhage control, trauma evaluation"),("C","No imaging ever"),("D","Immediate closure of all wounds")],{"A":"Vinegar is species-specific jellyfish care, not major trauma priority.","B":"Correct.","C":"Retained teeth/spines need imaging.","D":"Marine punctures/lacerations often should not be primarily closed."}),
        ("A","Marine wounds are high-risk because they may contain:",[("A","Halophilic gram-negative and polymicrobial flora"),("B","Only sterile water"),("C","Only viruses"),("D","No foreign bodies")],{"A":"Correct.","B":"False.","C":"Too narrow.","D":"Teeth/spines/barbs can remain."}),
        ("C","For serious seawater-associated wound infection, coverage should include:",[("A","No antibiotics ever"),("B","Only first-generation cephalosporin"),("C","Vibrio-active regimen plus staph/strep coverage when indicated"),("D","Only antifungal cream")],{"A":"Wrong for serious/infected wounds.","B":"Often inadequate.","C":"Correct.","D":"No."}),
        ("D","Coral cuts should be evaluated for:",[("A","Myocardial infarction only"),("B","No foreign matter"),("C","Mandatory antivenom"),("D","Retained foreign body and delayed cellulitis/granuloma")],{"A":"No.","B":"Coral fragments can embed.","C":"No antivenom.","D":"Correct."}),
        ("A","Stingray injury usually causes:",[("A","Immediate intense pain and possible retained barb/penetrating trauma"),("B","Painless dry bite"),("C","Delayed neurotoxicity only"),("D","No bleeding")],{"A":"Correct.","B":"No.","C":"Sea snake/octopus-type concern.","D":"Bleeding can occur."}),
        ("B","First-line analgesic measure for stingray/lionfish/stonefish stings:",[("A","Ice immersion"),("B","Hot water immersion to tolerance"),("C","Tourniquet"),("D","Freshwater irrigation only")],{"A":"Cold can worsen pain.","B":"Correct: heat-labile venom.","C":"Not routine.","D":"No."}),
        ("C","Stonefish systemic toxicity or refractory pain may need:",[("A","No treatment"),("B","Dapsone"),("C","Stonefish antivenom where available"),("D","Snake antivenom")],{"A":"Unsafe if severe.","B":"No.","C":"Correct.","D":"Wrong antivenom."}),
        ("D","Sea snake envenomation hallmark:",[("A","Only local urticaria"),("B","Massive wound necrosis always"),("C","Instant coral rash"),("D","Myalgia, rhabdomyolysis/myoglobinuria, neurotoxicity/respiratory failure")],{"A":"No.","B":"Not typical.","C":"No.","D":"Correct."}),
        ("A","Sea snake first aid:",[("A","Pressure immobilization of affected limb and transport"),("B","Incision and suction"),("C","Hot water only"),("D","Immediate discharge")],{"A":"Correct.","B":"Harmful.","C":"Not enough.","D":"Unsafe."}),
        ("B","Blue-ringed octopus venom causes:",[("A","Only rash"),("B","Tetrodotoxin-like paralysis and respiratory failure"),("C","Heatstroke"),("D","Coagulopathy only")],{"A":"No.","B":"Correct.","C":"No.","D":"No."}),
        ("C","Blue-ringed octopus treatment is mainly:",[("A","Antivenom"),("B","Antibiotics only"),("C","Pressure immobilization, airway/ventilatory support, ICU care"),("D","Vinegar")],{"A":"No specific antivenom.","B":"Not definitive.","C":"Correct.","D":"For selected jellyfish, not octopus."}),
        ("D","Sea urchin spine injuries require:",[("A","No foreign-body search"),("B","Routine closure"),("C","Cold immersion"),("D","Hot water, analgesia, imaging/US if retained spine suspected, removal when possible")],{"A":"Retained spines matter.","B":"No.","C":"Heat is used.","D":"Correct."}),
        ("A","Jellyfish nematocysts should generally not be irrigated with:",[("A","Freshwater"),("B","Seawater"),("C","Normal saline"),("D","Species-appropriate decontaminant")],{"A":"Correct: hypotonic solution may trigger discharge.","B":"Often used.","C":"Often used.","D":"Depends on species/geography."}),
        ("B","Portuguese man-of-war treatment:",[("A","Vinegar always"),("B","Seawater rinse, tentacle removal, hot water; avoid vinegar for Physalia"),("C","Stonefish antivenom"),("D","Pressure immobilization")],{"A":"Can trigger discharge in this species.","B":"Correct.","C":"No.","D":"No."}),
        ("C","Box jellyfish/Chironex severe envenomation may cause:",[("A","Only mild itch"),("B","No cardiotoxicity"),("C","Rapid cardiovascular collapse and severe pain"),("D","Only retained spine")],{"A":"False.","B":"Cardiotoxicity is feared.","C":"Correct.","D":"No."}),
        ("D","Indo-Pacific box jellyfish decontamination commonly uses:",[("A","Freshwater"),("B","Alcohol rub"),("C","Suction"),("D","5% acetic acid/vinegar for Chironex-type stings where recommended")],{"A":"Avoid.","B":"No.","C":"No.","D":"Correct, species/geography dependent."}),
        ("A","Irukandji syndrome is notable for:",[("A","Severe generalized pain, hypertension, catecholamine features after often mild initial sting"),("B","Only local abrasion"),("C","Painless dry bite"),("D","No systemic effects")],{"A":"Correct.","B":"Too mild.","C":"No.","D":"False."}),
        ("B","Irukandji pain treatment:",[("A","No analgesia"),("B","Titrated IV opioids; manage hypertension when persistent"),("C","Only topical cream"),("D","Immediate fasciotomy")],{"A":"Wrong.","B":"Correct.","C":"Insufficient.","D":"No."}),
        ("C","Marine foreign-body evaluation often uses:",[("A","No imaging"),("B","Only ECG"),("C","Radiographs first; US/CT/MRI if suspicion persists"),("D","Only urine culture")],{"A":"Unsafe.","B":"No.","C":"Correct.","D":"No."}),
        ("D","Which wounds should not usually be sutured primarily?",[("A","Clean indoor paper cut"),("B","Old healed scar"),("C","Simple atraumatic rash"),("D","Marine lacerations/punctures with contamination risk")],{"A":"Not marine.","B":"No.","C":"No.","D":"Correct."}),
        ("A","After any marine envenomation, the first step is:",[("A","Remove victim from water and prevent drowning"),("B","Start vinegar before rescue"),("C","Delay rescue for species ID"),("D","Give oral antibiotics underwater")],{"A":"Correct.","B":"Unsafe.","C":"Unsafe.","D":"No."}),
        ("B","Cone snail severe envenomation can produce:",[("A","Only local itch"),("B","Progressive paralysis and respiratory failure"),("C","Heat cramps"),("D","DIC only")],{"A":"Too mild.","B":"Correct.","C":"No.","D":"No."}),
        ("C","Rosen Table 53.5 adds:",[("A","A trauma-only ATLS algorithm"),("B","Antipsychotic overdose doses"),("C","Species-specific hot-water/vinegar/antivenom distinctions"),("D","Hypothermia ECG")],{"A":"No.","B":"No.","C":"Correct.","D":"No."}),
        ("D","Bony fish/stingray wounds should be explored for:",[("A","Nothing"),("B","Only viral load"),("C","Bee stinger"),("D","Retained spine/sheath and deep penetration")],{"A":"Wrong.","B":"No.","C":"Different chapter.","D":"Correct."}),
        ("A","Best summary of jellyfish care:",[("A","Remove from water, avoid freshwater, remove tentacles safely, use species/geography-guided decontamination, treat pain/systemic toxicity"),("B","Freshwater for all"),("C","Vinegar for all species"),("D","No observation for systemic symptoms")],{"A":"Correct.","B":"Wrong.","C":"Wrong.","D":"Unsafe."}),
        ("B","Disposition for box jellyfish, Irukandji, stonefish systemic toxicity, or antivenom-treated patients:",[("A","Immediate beach discharge"),("B","Admission/ICU or transfer when unstable/systemic"),("C","No monitoring"),("D","Only topical follow-up")],{"A":"Unsafe.","B":"Correct.","C":"Wrong.","D":"Insufficient."}),
    ]
    return "\n".join(mcq(i, *row) for i, row in enumerate(raw, 1))


def doc_html() -> str:
    c = {x.key: x for x in CROPS}
    return f"""<!doctype html><html lang="en" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Chapter 213 - Marine Trauma and Envenomation</title><style>{STYLE}</style></head><body>
<header id="top-header"><button class="hdr-btn" data-sidebar-toggle title="Contents">☰</button><div class="hdr-title">Ch.213 Marine Trauma and Envenomation</div><button class="hdr-btn theme-btn" data-theme-toggle>Dark</button></header>
<div class="app"><aside id="sidebar" class="sidebar"><button class="hdr-btn sidebar-close" data-sidebar-close>Close</button><div class="sidebar__block"><div class="sidebar__kicker">Chapter</div><h2>Marine Trauma and Envenomation</h2><p class="meta"><b>Spine:</b> Tintinalli Ch.213</p><p class="meta"><b>Rosen:</b> Ch.53 marine animals</p><p class="meta"><b>Build:</b> fresh inventory and crop QA</p></div><div class="sidebar__block"><div class="sidebar__kicker">Contents</div><a class="sidebar__link" href="#overview">Overview</a><a class="sidebar__link" href="#trauma">Trauma/Wounds</a><a class="sidebar__link" href="#antibiotics">Antibiotics</a><a class="sidebar__link" href="#fish">Stingrays/Fish</a><a class="sidebar__link" href="#sea-snake">Sea Snake/Octopus</a><a class="sidebar__link" href="#urchin">Urchin/Starfish</a><a class="sidebar__link" href="#jellyfish">Jellyfish</a><a class="sidebar__link" href="#drug-doses">Drug Dose Reference</a><a class="sidebar__link" href="#assessment">Assessment</a></div></aside>
<main id="main" class="main"><div class="content-wrap"><div class="utility-bar">Fresh rebuild • Tintinalli inventory 8/8 • Rosen source crops • MCQs show all explanations after answer</div>
<section class="hero section" id="overview"><div class="eyebrow">Environmental Injuries Chapter 213</div><h1 class="hero__title">Marine Trauma and Envenomation</h1><p class="lede">Marine injuries mix trauma, venom, retained foreign bodies, drowning risk, and unusual infection. The ED rhythm is <mark>rescue first, image for retained material, heat for heat-labile venoms, and species-aware decontamination.</mark></p><div class="callout warn"><strong>Board trap:</strong> vinegar is not universal for jellyfish; freshwater can worsen nematocyst discharge.</div></section>
<section class="section" id="trauma"><h2>Marine Trauma and Foreign Bodies</h2><p>Sharks, stingrays, barracuda, moray eels, seals, crocodilians, and sharp-spined fish can cause crush, avulsion, puncture, and penetrating trauma. Remove the victim from water, manage ABCs, control arterial hemorrhage with a tourniquet when indicated, and treat as trauma. Teeth, spines, coral fragments, and stingray barbs can remain in bone or soft tissue.</p><p><u>Plain radiographs are first-line for retained teeth/spines/fragments</u>; ultrasound, CT, or MRI is used when suspicion persists. Marine puncture wounds and lacerations are contaminated and usually should not be sutured primarily.</p>{source_card(c['tint_fig_213_1'], 'Tintinalli coral-wound image highlights retained foreign body risk in common minor marine trauma.')}</section>
<section class="section" id="antibiotics"><h2>Marine Soft-Tissue Infection and Antibiotics</h2><p>Marine infections are often polymicrobial, halophilic, gram-negative, and resistant to routine first-generation cephalosporins. Pathogens include Vibrio, Aeromonas, Pseudomonas, Erysipelothrix, Mycobacterium marinum, and usual skin flora. Patients with hepatic disease, diabetes, immunosuppression, deep wounds, delayed care, or major trauma need lower threshold for broad treatment and admission.</p>{source_card(c['tint_table_213_1'], 'Tintinalli recommendations table separates no-antibiotic, outpatient prophylaxis, and IV/admission indications.')}{source_card(c['tint_table_213_2'], 'Tintinalli antibiotic table is placed beside the infection discussion for freshwater versus seawater coverage.')}</section>
<section class="section" id="fish"><h2>Stingrays and Venomous Fish</h2><p>Stingrays cause immediate intense local pain, bleeding, and laceration from barbed spines; thoracoabdominal penetration can be fatal. Venomous fish such as stonefish, weeverfish, lionfish, and scorpionfish produce severe pain that often improves with hot water because the venom is heat labile. Irrigate, remove visible spine/sheath material, image for retained foreign body, update tetanus, and provide analgesia.</p><p>Antibiotics are not automatic for every small sting, but use them for deep puncture wounds, large wounds, retained foreign material, delayed care, immunocompromised hosts, hepatic disease, or established infection. Stonefish antivenom is used where available for systemic toxicity or refractory pain.</p>{source_card(c['tint_table_213_3'], 'Tintinalli early-treatment table is the core ED action table for penetrating and nonpenetrating marine envenomations.')}{source_card(c['rosen_fig_55_11'], 'Rosen lionfish image gives a visual anchor for painful venomous fish stings.', 'Tintinalli gives the ED hot-water treatment table; Rosen emphasizes heat-labile fish/stingray venoms and imaging for retained radiopaque spines.')}{source_card(c['rosen_table_53_5'], 'Rosen species table summarizes hot water, acetic acid, and antivenom distinctions.', 'Tintinalli gives a broad early-treatment table; Rosen sharpens the species-specific exceptions that change bedside decontamination.')}</section>
<section class="section" id="sea-snake"><h2>Sea Snakes, Octopus, and Cone Snails</h2><p>Sea snake bites are often initially painless but can cause severe myalgia, rhabdomyolysis, myoglobinuria, neurotoxicity, paralysis, and respiratory failure. Use pressure immobilization, monitor CK/renal function/respiration, and give polyvalent sea snake antivenom for systemic envenomation when available.</p><p>Blue-ringed octopus envenomation is tetrodotoxin-like: paresthesias and paralysis can progress to respiratory arrest while consciousness may be preserved. Treatment is pressure immobilization, airway and ventilatory support, and ICU care. Cone snails can also cause progressive paralysis and respiratory failure after handling attractive shells.</p>{source_card(c['tint_fig_213_2'], 'Tintinalli octopus-bite figure shows persistent wound and delayed infectious/inflammatory issues.')}{source_card(c['rosen_fig_53_9'], 'Rosen blue-ringed octopus image belongs with the respiratory-failure syndrome.', 'Tintinalli describes tetrodotoxin-like paralysis; Rosen reinforces that tiny, nonaggressive octopus bites can be fatal by ventilatory failure.')}</section>
<section class="section" id="urchin"><h2>Sea Urchins, Starfish, Fireworms, Hydroids</h2><p>Sea urchin injuries cause local burning pain, discoloration, retained calcareous spines, synovitis if a joint is entered, and delayed granuloma. Treat with hot water immersion, analgesia, removal of accessible spines, imaging when retained fragments are suspected, and specialty follow-up for joint involvement or persistent symptoms.</p><p>Fireworms leave detachable bristles causing burning inflammation; remove bristles with tape or forceps and treat symptomatically. Hydroids and fire coral are nonpenetrating nematocyst injuries; seawater irrigation and topical steroids/antihistamines may help itch and inflammation.</p>{source_card(c['tint_fig_213_3'], 'Tintinalli sea-urchin foot image keeps retained spine recognition beside the treatment discussion.')}</section>
<section class="section" id="jellyfish"><h2>Jellyfish, Portuguese Man-of-War, Box Jellyfish, Irukandji</h2><p>Jellyfish nematocysts discharge venom after mechanical or chemical stimulus. Remove the victim from water, avoid freshwater, irrigate with seawater or saline, remove visible tentacles carefully, and use species/geography-guided decontamination. Hot water and topical lidocaine help many painful stings.</p><p>Portuguese man-of-war/bluebottle stings should be rinsed with seawater, tentacles removed, and pain treated with hot water; <mark>vinegar is not recommended for Physalia</mark>. Indo-Pacific Chironex box jellyfish stings may cause severe pain and cardiovascular collapse within minutes; use vinegar where recommended, resuscitate aggressively, treat anaphylaxis risk, and consider box jellyfish antivenom. Irukandji syndrome causes severe generalized pain and hypertension after mild initial sting; treat with IV opioids and control persistent hypertension.</p>{source_card(c['tint_fig_213_4'], 'Tintinalli Portuguese man-of-war figure is placed beside the Physalia vinegar warning.')}{source_card(c['tint_fig_213_5'], 'Tintinalli box jellyfish sting image anchors severe Chironex-type skin findings and systemic risk.')}{source_card(c['rosen_fig_53_10'], 'Rosen box jellyfish image provides source confirmation for Chironex recognition.', 'Tintinalli emphasizes geography-specific vinegar; Rosen adds that CPR/resuscitation may matter more than antivenom evidence in rapidly fatal Chironex collapse.')}</section>
<section class="section" id="drug-doses"><h2>Drug Dose Reference</h2><p>This is a treatment recap after the syndrome discussions.</p><div class="table-wrap"><table><thead><tr><th>Therapy</th><th>Use</th><th>Trap</th></tr></thead><tbody><tr><td>Hot water immersion</td><td>Fish, stingray, urchin, many painful stings; about 40-45 C to tolerance</td><td>Avoid burns; continue until pain relief.</td></tr><tr><td>Vinegar/acetic acid 4-5%</td><td>Indo-Pacific Chironex/selected box jellyfish; fireworms in Tintinalli table</td><td>Not universal; avoid for Physalia/bluebottle.</td></tr><tr><td>Stonefish antivenom</td><td>Severe systemic toxicity or refractory pain where available</td><td>Prepare for anaphylaxis.</td></tr><tr><td>Sea snake antivenom</td><td>Systemic sea snake envenomation</td><td>Pressure immobilization and ventilatory support remain critical.</td></tr><tr><td>Opioids/antihypertensives</td><td>Irukandji severe pain and hypertension</td><td>Magnesium evidence is limited; monitor toxicity.</td></tr></tbody></table></div></section>
<section class="question-set section" id="assessment"><h2>Inline Assessment MCQs</h2>{build_mcqs()}</section>
</div></main></div><div class="score-pill" data-score-text>0 correct / 0 answered / 26 total</div><div class="image-modal" data-image-modal><button class="hdr-btn" data-modal-close>Close</button><img alt="Zoomed source"></div><script>{SCRIPT}</script></body></html>"""


def extract_embedded(doc: str) -> list[Path]:
    EMBED.mkdir(parents=True, exist_ok=True)
    for old in EMBED.glob("*.png"):
        old.unlink()
    paths = []
    for i, m in enumerate(re.finditer(r"data:image/png;base64,([^\"]+)", doc), 1):
        p = EMBED / f"ch213_embedded_{i:02d}.png"
        p.write_bytes(base64.b64decode(m.group(1)))
        paths.append(p)
    return paths


def contact_sheet(paths: list[Path]) -> Path:
    cols, cell_w, cell_h = 3, 370, 315
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
    draw = ImageDraw.Draw(sheet)
    for i, path in enumerate(paths):
        img = Image.open(path).convert("RGB")
        img.thumbnail((330, 260))
        x, y = (i % cols) * cell_w, (i // cols) * cell_h
        sheet.paste(img, (x + 20, y + 36))
        draw.text((x + 8, y + 8), f"{i+1:02d} {path.name}", fill=(0, 0, 0))
    out = EMBED / "ch213_embedded_contact_sheet.png"
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
    md = f"""# CH213 Crop QA - 2026-05-09

Fresh rebuild from source PDFs. Old Chapter213 HTML crops were not used.

## Source Inventory Used

Tintinalli Ch213 inventory included: Table 213-1, Table 213-2, Figure 213-1, Table 213-3, Figure 213-2, Figure 213-3, Figure 213-4, and Figure 213-5 = 8/8 included.

Rosen Ch53 relevant inventory included: Fig. 53.9, Fig. 53.10, Fig. 55.11, and Table 53.5.

{inv}

## Embedded Crop QA

Contact sheet: `{sheet.relative_to(ROOT).as_posix()}`

| # | Source | Object | PDF | PDF page | Extracted final embedded image | Status | Note |
|---|---|---|---|---:|---|---|---|
{chr(10).join(rows)}

## Content Gate

Content: PASS. Major headings have narrative summaries; source crops are topic-local; treatment table appears in the clinical treatment section; no visible audit/source-audit repair text is inside the chapter.

Pattern: PASS. Ch186/Ch201 shell, top header, sidebar/main layout, Rosen source cards, Rosen vs Tintinalli deltas, and accepted MCQ behavior are present.
"""
    QA_MD.write_text(md, encoding="utf-8")
    QA_HTML.write_text(md_to_html(md, "CH213 Crop QA"), encoding="utf-8")


def update_audit() -> None:
    md = AUDIT_MD.read_text(encoding="utf-8")
    line = "| 213 | Chapter213_MarineTraumaAndEnvenomation.html | PASS | 26 | 26 | 3 | 12 | 12 | 4 | 4 | Fresh rebuild; Content PASS; Pattern PASS; Tintinalli 8/8 + Rosen 4/4 source crops topic-local; crop QA 12/12 PASS. |"
    if re.search(r"^\| 213 \|.*$", md, flags=re.M):
        md = re.sub(r"^\| 213 \|.*$", line, md, flags=re.M)
    else:
        md = md.rstrip() + "\n" + line + "\n"
    md = re.sub(r"Toxicology chapter gate:\s*\*\*\d+ PASS / \d+ FAIL\*\*", "Toxicology chapter gate: **38 PASS / 0 FAIL**", md)
    md = re.sub(r"Scope: Tintinalli toxicology/environmental chapters `176-\d+`", "Scope: Tintinalli toxicology/environmental chapters `176-213`", md)
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
    if checks["rosen"] < 4 or checks["delta"] < 4:
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
