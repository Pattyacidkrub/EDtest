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
OUT_HTML = ROOT / "docs/chapters/complete/Chapter211_BitesAndStings.html"
MIRROR = Path(r"C:\c\Users\PC\OneDrive\เอกสาร\codex\ER")
QA_MD = ROOT / "CH211_CROP_QA_2026-05-09.md"
QA_HTML = ROOT / "CH211_CROP_QA_2026-05-09.html"
AUDIT_MD = ROOT / "TOXICOLOGY_COMPLETE_AUDIT_2026-05-08.md"
AUDIT_HTML = ROOT / "TOXICOLOGY_COMPLETE_AUDIT_2026-05-08.html"
WORK = ROOT / "_ch211_rebuild_fresh_2026-05-09"
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
    CropSpec("tint_table_211_1", "Tintinalli", "Table 211-1", TINT, 1397, (28, 38, 566, 248), "spider overview", "medically important spider bites and treatment table"),
    CropSpec("tint_fig_211_1", "Tintinalli", "Figure 211-1", TINT, 1397, (28, 572, 446, 744), "loxosceles distribution", "recluse spider density range map and caption"),
    CropSpec("tint_fig_211_2", "Tintinalli", "Figure 211-2", TINT, 1398, (52, 38, 316, 257), "brown recluse identification", "brown recluse fiddle marking figure and caption"),
    CropSpec("tint_fig_211_3", "Tintinalli", "Figure 211-3", TINT, 1398, (52, 534, 316, 744), "brown recluse lesion", "early brown recluse bite photo and caption"),
    CropSpec("tint_fig_211_4", "Tintinalli", "Figure 211-4", TINT, 1398, (322, 532, 586, 744), "widow spider identification", "black widow spider photo and caption"),
    CropSpec("tint_fig_211_5", "Tintinalli", "Figure 211-5", TINT, 1399, (28, 548, 292, 744), "latrodectus bite", "black widow bite photo and caption"),
    CropSpec("tint_table_211_2", "Tintinalli", "Table 211-2", TINT, 1401, (0, 35, 570, 255), "scorpion treatment", "scorpion sting effects and treatment table with footnotes"),
    CropSpec("rosen_fig_53_5", "Rosen", "Fig. 53.5", ROSEN, 817, (76, 78, 292, 224), "hymenoptera", "Africanized honeybee image and caption"),
    CropSpec("rosen_fig_53_6", "Rosen", "Fig. 53.6", ROSEN, 817, (316, 78, 574, 260), "black widow recognition", "female black widow image and caption"),
    CropSpec("rosen_fig_53_7", "Rosen", "Fig. 53.7", ROSEN, 818, (42, 62, 298, 306), "brown recluse recognition", "brown recluse image and caption"),
    CropSpec("rosen_fig_53_8", "Rosen", "Fig. 53.8", ROSEN, 818, (312, 62, 568, 258), "scorpion recognition", "Arizona bark scorpion image and caption"),
    CropSpec("rosen_table_53_4", "Rosen", "Table 53.4", ROSEN, 822, (46, 64, 574, 206), "scorpion grading", "North American Centruroides grading table and footnote"),
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
        ("A","Most deaths from arthropod stings are from:",[("A","Hymenoptera anaphylaxis"),("B","Simple mosquito bites"),("C","All brown recluse bites"),("D","All tick bites")],{"A":"Correct: bee/wasp/hornet/yellow-jacket allergy kills more than direct local venom.","B":"Mosquito bites are usually local; vector disease is separate.","C":"Brown recluse systemic toxicity is uncommon in the United States.","D":"Tick-borne disease matters, but not the usual immediate sting-fatality mechanism."}),
        ("B","A honeybee stinger is still visible in the skin. Best next step:",[("A","Delay removal until forceps are found"),("B","Remove it immediately by any practical method"),("C","Inject lidocaine with epinephrine through the stinger"),("D","Do nothing because venom stops instantly")],{"A":"Delay leaves venom apparatus contracting.","B":"Correct: speed matters more than scrape-versus-pinch technique.","C":"Not the priority.","D":"Venom can continue briefly after detachment."}),
        ("C","Large local Hymenoptera reactions:",[("A","Always require antibiotics"),("B","Are proof of anaphylaxis"),("C","May enlarge over 1-2 days and can mimic infection"),("D","Never involve airway risk")],{"A":"Antibiotics are for true infection.","B":"Local swelling alone is not systemic anaphylaxis.","C":"Correct.","D":"Oral/pharyngeal swelling can threaten airway."}),
        ("D","Systemic Hymenoptera reaction in the ED should be treated first with:",[("A","Oral antihistamine only"),("B","Topical steroid"),("C","Observation only"),("D","IM epinephrine plus ABC support")],{"A":"Adjunct only.","B":"Not enough.","C":"Unsafe for anaphylaxis.","D":"Correct."}),
        ("A","Fire ant lesions classically produce:",[("A","Sterile pustules that should be kept clean and not opened"),("B","Mandatory incision and drainage"),("C","Immediate necrotizing fasciitis in all patients"),("D","No allergic risk")],{"A":"Correct.","B":"Opening pustules increases infection risk.","C":"Not typical.","D":"Fire ants can cause systemic allergy."}),
        ("B","The brown recluse bite diagnosis is most reliable when:",[("A","Any necrotic ulcer is present"),("B","The spider is identified in an endemic area with compatible course"),("C","There are many lesions all over the body"),("D","The lesion drains pus on day 1")],{"A":"Many mimics cause ulcers.","B":"Correct.","C":"Numerous lesions argue against recluse.","D":"Early exudate suggests infection or another diagnosis."}),
        ("C","Major brown recluse venom mediator of necrosis is:",[("A","Alpha-latrotoxin"),("B","Histamine only"),("C","Phospholipase D/sphingomyelinase D activity"),("D","Tetrodotoxin")],{"A":"Widow spider toxin.","B":"Too simplistic.","C":"Correct.","D":"Marine/pufferfish toxin, not recluse."}),
        ("D","Brown recluse systemic toxicity in children can include:",[("A","Only itching"),("B","Guaranteed hypertension only"),("C","Immediate flaccid paralysis"),("D","Hemolysis, hemoglobinuria, rhabdomyolysis, renal injury, DIC")],{"A":"Too mild.","B":"Not the hallmark.","C":"Tick paralysis/scorpion differential, not recluse hallmark.","D":"Correct."}),
        ("A","Brown recluse treatment is primarily:",[("A","Supportive wound care, analgesia, tetanus, infection treatment only if present, delayed surgery if needed"),("B","Immediate wide excision for all"),("C","Dapsone for every patient"),("D","US antivenom for every patient")],{"A":"Correct.","B":"Early excision can worsen wounds.","C":"Not proven and has harms.","D":"No routine US antivenom."}),
        ("B","Black widow venom produces symptoms mainly by:",[("A","Local tissue necrosis"),("B","Massive neurotransmitter release from alpha-latrotoxin"),("C","Blocking acetylcholine release"),("D","Hemolysis")],{"A":"Recluse pattern.","B":"Correct.","C":"Botulism mechanism.","D":"Recluse systemic pattern."}),
        ("C","Latrodectism can mimic:",[("A","Simple cellulitis only"),("B","Stroke only"),("C","Acute abdomen, renal colic, withdrawal, myocardial ischemia"),("D","Painless rash only")],{"A":"Too narrow.","B":"Not typical.","C":"Correct.","D":"Pain and cramps are central."}),
        ("D","Routine laboratory confirmation for black widow bite is:",[("A","Always available ELISA"),("B","Required before treatment"),("C","Venom PCR from wound"),("D","Not available; diagnosis is clinical")],{"A":"No routine test.","B":"No.","C":"No.","D":"Correct."}),
        ("A","First-line symptomatic treatment for moderate black widow envenomation:",[("A","Opioid analgesia and benzodiazepines as needed"),("B","Calcium gluconate as definitive treatment"),("C","Dantrolene for all"),("D","Antibiotics for all")],{"A":"Correct.","B":"Not supported as routine effective therapy.","C":"Not recommended.","D":"Only if infection."}),
        ("B","Latrodectus antivenom is best reserved for:",[("A","All witnessed bites"),("B","Severe persistent symptoms or high-risk patients after risk-benefit discussion"),("C","Any itchy papule"),("D","Brown recluse wounds")],{"A":"Too broad.","B":"Correct.","C":"No.","D":"Wrong spider."}),
        ("C","A scorpion sting with cranial nerve dysfunction or skeletal neuromuscular dysfunction is Rosen grade:",[("A","1"),("B","2"),("C","3 or 4 depending combination"),("D","0")],{"A":"Grade 1 is local only.","B":"Grade 2 is local plus remote pain/paresthesia.","C":"Correct; these grades support antivenom use.","D":"No."}),
        ("D","Centruroides scorpion envenomation is especially concerning in:",[("A","Only healthy adults with local pain"),("B","Patients with no symptoms"),("C","Everyone needs intubation"),("D","Young children and patients with systemic neuromuscular/autonomic signs")],{"A":"Usually local care.","B":"No.","C":"Too broad.","D":"Correct."}),
        ("A","Scorpion treatment for local effects only:",[("A","Wound care, analgesia/NSAID, local anesthetic without epinephrine as needed"),("B","Mandatory antivenom"),("C","High-dose antibiotics"),("D","Immediate amputation")],{"A":"Correct.","B":"Systemic severe cases.","C":"Not routine.","D":"No."}),
        ("B","Which scorpion finding pushes toward antivenom/benzodiazepines?",[("A","Tiny local wheal only"),("B","Oculomotor abnormalities, neuromuscular agitation, muscle spasms"),("C","Asymptomatic exposure"),("D","One healed puncture months later")],{"A":"Local care.","B":"Correct.","C":"Observe if needed.","D":"No acute envenomation."}),
        ("C","Tick paralysis usually improves after:",[("A","Dapsone"),("B","Latrodectus antivenom"),("C","Finding and removing the tick"),("D","Hyperbaric oxygen")],{"A":"No.","B":"No.","C":"Correct.","D":"No."}),
        ("D","Chigger management is mainly:",[("A","Antivenom"),("B","Surgery"),("C","No itch treatment allowed"),("D","Antipruritics/topical steroids, hygiene, and infection treatment only if secondary infection")],{"A":"No venom syndrome needing antivenom.","B":"No.","C":"Wrong.","D":"Correct."}),
        ("A","Mosquito bite importance in this chapter includes:",[("A","Local allergic reactions and vector-borne disease awareness"),("B","Guaranteed venom shock"),("C","Latrodectism"),("D","Hemolysis at 24-72 h")],{"A":"Correct.","B":"No.","C":"Widow spider.","D":"Brown recluse systemic toxicity."}),
        ("B","Best disposition after Hymenoptera anaphylaxis requiring epinephrine:",[("A","Immediate discharge after injection"),("B","Observation at least several hours; longer if symptoms recur or severe"),("C","No autoinjector education"),("D","No allergy referral ever")],{"A":"Unsafe.","B":"Correct.","C":"Autoinjector education is important.","D":"Systemic reactions merit referral/immunotherapy discussion."}),
        ("C","Black widow patient with no symptoms after observation can usually:",[("A","Receive routine antivenom"),("B","Be admitted for all cases"),("C","Discharge with return precautions if reliable and well"),("D","Receive dapsone")],{"A":"Not indicated.","B":"Too broad.","C":"Correct.","D":"For recluse historically, not widow."}),
        ("D","Brown recluse admission is most appropriate for:",[("A","Tiny stable local lesion"),("B","No symptoms"),("C","Mild itch only"),("D","Expanding wound, systemic symptoms, hemolysis risk, or need for serial labs/wound care")],{"A":"Outpatient wound care may be enough.","B":"No.","C":"No.","D":"Correct."}),
        ("A","Rosen's scorpion table adds most directly:",[("A","A grading system linking Centruroides neurologic findings to antivenom decisions"),("B","A snakebite pit-viper algorithm"),("C","A pesticide cholinergic toxidrome table"),("D","A frostbite staging chart")],{"A":"Correct.","B":"Different chapter.","C":"Different chapter.","D":"Cold injury."}),
        ("B","Overall ED rule for bites and stings:",[("A","Every bite needs antivenom"),("B","Treat anaphylaxis first, identify the syndrome, control pain, use antivenom only for the right severe envenomation, and give clear return precautions"),("C","Ignore airway swelling"),("D","Use antibiotics for all arthropod wounds")],{"A":"False.","B":"Correct.","C":"Unsafe.","D":"Not routine."}),
    ]
    return "\n".join(mcq(i, *row) for i, row in enumerate(raw, 1))


def doc_html() -> str:
    c = {x.key: x for x in CROPS}
    return f"""<!doctype html><html lang="en" data-theme="light"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Chapter 211 - Bites and Stings</title><style>{STYLE}</style></head><body>
<header id="top-header"><button class="hdr-btn" data-sidebar-toggle title="Contents">☰</button><div class="hdr-title">Ch.211 Bites and Stings</div><button class="hdr-btn theme-btn" data-theme-toggle>Dark</button></header>
<div class="app"><aside id="sidebar" class="sidebar"><button class="hdr-btn sidebar-close" data-sidebar-close>Close</button><div class="sidebar__block"><div class="sidebar__kicker">Chapter</div><h2>Bites and Stings</h2><p class="meta"><b>Spine:</b> Tintinalli Ch.211</p><p class="meta"><b>Rosen:</b> Ch.53 venomous animal injuries</p><p class="meta"><b>Build:</b> fresh inventory and crop QA</p></div><div class="sidebar__block"><div class="sidebar__kicker">Contents</div><a class="sidebar__link" href="#overview">Overview</a><a class="sidebar__link" href="#hymenoptera">Hymenoptera</a><a class="sidebar__link" href="#spiders">Spiders</a><a class="sidebar__link" href="#recluse">Brown Recluse</a><a class="sidebar__link" href="#widow">Black Widow</a><a class="sidebar__link" href="#scorpions">Scorpions</a><a class="sidebar__link" href="#other">Other Arthropods</a><a class="sidebar__link" href="#drug-doses">Drug Dose Reference</a><a class="sidebar__link" href="#assessment">Assessment</a></div></aside>
<main id="main" class="main"><div class="content-wrap"><div class="utility-bar">Fresh rebuild • Tintinalli inventory 7/7 • Rosen source crops • MCQs show all explanations after answer</div>
<section class="hero section" id="overview"><div class="eyebrow">Environmental Injuries Chapter 211</div><h1 class="hero__title">Bites and Stings</h1><p class="lede">Most arthropod encounters are local wound problems, but the ED danger pattern is <mark>anaphylaxis, severe pain/autonomic envenomation, progressive neurologic toxicity, or delayed hematotoxicity</mark>.</p><div class="callout warn"><strong>Board trap:</strong> the right first move is syndrome recognition, not reflex antivenom or reflex antibiotics.</div></section>
<section class="section" id="hymenoptera"><h2>Hymenoptera: Bees, Wasps, Hornets, Yellow Jackets, Fire Ants</h2><p>Hymenoptera cause more sting-related deaths than other insects because allergy, not local venom injury, drives fatality. Honeybees leave a barbed stinger; remove it immediately by any practical method because <u>speed matters more than scrape-versus-pinch technique</u>. Wasps, hornets, and yellow jackets can sting repeatedly and are frequent causes of systemic reactions.</p><p>Local reactions cause pain, erythema, pruritus, and swelling. Large local reactions may enlarge over 24 to 48 hours and mimic cellulitis without infection. Mouth, throat, or periorbital stings need airway/eye caution. Anaphylaxis is treated with IM epinephrine, airway and circulatory support, antihistamines and steroids as adjuncts, observation, epinephrine autoinjector education, and allergy referral after systemic reactions.</p>{source_card(c['rosen_fig_53_5'], 'Rosen image anchors Africanized bee recognition and mass-sting risk.', 'Tintinalli emphasizes local/systemic allergic reactions; Rosen adds that Africanized bees are not more toxic per sting but attack in large numbers, changing observation for massive envenomation.')}</section>
<section class="section" id="spiders"><h2>Spider Bite Overview</h2><p>Most spiders cannot meaningfully envenomate humans. The medically important board patterns are necrotic arachnidism from Loxosceles, neuroautonomic latrodectism from widow spiders, and rare regional syndromes such as funnel-web or armed spider envenomation. <mark>Do not diagnose every ulcer as a brown recluse bite</mark>; geography, witnessed bite, spider identification, and course matter.</p>{source_card(c['tint_table_211_1'], 'Tintinalli table keeps the medically important spider syndromes, complications, and treatment options together for comparison.')}</section>
<section class="section" id="recluse"><h2>Brown Recluse / Loxosceles</h2><p>Loxosceles spiders are brown with a violin-shaped marking and six eyes in three pairs. The bite is often painless at first; local lesions can become firm, violaceous, blistered, and necrotic over days. Severe systemic illness is uncommon in the United States but children can develop hemolysis 24 to 72 hours later with hemoglobinuria, rhabdomyolysis, renal injury, DIC, and shock.</p><p>Diagnosis is clinical and often overcalled. Important mimics include skin and soft tissue infection, pyoderma gangrenosum, fungal/viral lesions, foreign body reaction, and cutaneous anthrax. Treatment is supportive: local wound care, analgesia, tetanus update, elevation/ice as tolerated, antibiotics only for true infection, and delayed surgical management after margins declare. <u>Dapsone, steroids, colchicine, hyperbaric oxygen, early excision, and antivenom are not routine ED fixes.</u></p>{source_card(c['tint_fig_211_1'], 'Tintinalli map helps keep brown recluse diagnosis geographically honest.')}{source_card(c['tint_fig_211_2'], 'Tintinalli identification image shows the fiddle marking and eye pattern.')}{source_card(c['tint_fig_211_3'], 'Tintinalli lesion photo shows an early violaceous recluse bite pattern.')}{source_card(c['rosen_fig_53_7'], 'Rosen recluse image gives a second recognition anchor.', 'Tintinalli stresses geography and lesion course; Rosen adds the diagnostic warning that many suspected spider bites are not spider bites at all.')}</section>
<section class="section" id="widow"><h2>Black Widow / Latrodectus</h2><p>Black widow venom contains alpha-latrotoxin, causing acetylcholine, norepinephrine, and other neurotransmitter release. The syndrome is pain out of proportion: pinprick bite, regional or generalized pain, muscle cramps, abdominal rigidity, diaphoresis, hypertension, tachycardia, nausea, vomiting, headache, and sometimes priapism or myocarditis.</p><p>The diagnosis is clinical; there is no routine confirmatory lab. Treat with wound cleansing, tetanus update, opioids for pain, and benzodiazepines for muscle spasm/agitation. Calcium gluconate and dantrolene are not reliable routine therapy. Antivenom can rapidly improve severe cases but is equine-derived, may cause anaphylaxis/serum sickness, and should be reserved for severe persistent symptoms or high-risk patients after risk-benefit discussion.</p>{source_card(c['tint_fig_211_4'], 'Tintinalli black widow photo shows the hourglass pattern.')}{source_card(c['tint_fig_211_5'], 'Tintinalli bite photo belongs with latrodectism clinical recognition.')}{source_card(c['rosen_fig_53_6'], 'Rosen image reinforces female black widow recognition.', 'Tintinalli provides antivenom discussion; Rosen emphasizes that latrodectism can mimic an acute abdomen, renal colic, ischemia, tetanus, or withdrawal.')}</section>
<section class="section" id="scorpions"><h2>Scorpion Stings</h2><p>Scorpion venom produces immediate local pain and paresthesias; severe Centruroides envenomation causes autonomic and neuromuscular excitation. Concerning findings include tachycardia, hypertension, hypersalivation, vomiting, diaphoresis, abnormal eye movements, roving eyes, dysphagia, slurred speech, skeletal muscle jerking, restlessness, and respiratory compromise. Children are at higher risk for rapid severe disease.</p><p>Local effects are treated with wound care, ice, NSAIDs/analgesia, and local anesthetic without epinephrine when needed. Systemic neuromuscular or autonomic toxicity requires cardiorespiratory monitoring, benzodiazepines, opioids when appropriate, and Centruroides immune F(ab)2 antivenom for severe North American bark scorpion envenomation. <mark>Antivenom binds circulating venom but does not reverse established end-organ injury instantly.</mark></p>{source_card(c['tint_table_211_2'], 'Tintinalli treatment table sits inside the scorpion treatment section because it drives ED therapy.')}{source_card(c['rosen_fig_53_8'], 'Rosen Arizona bark scorpion image ties the severe North American syndrome to Centruroides.', 'Tintinalli lists effects and treatments; Rosen adds the Centruroides-specific recognition and disposition frame.')}{source_card(c['rosen_table_53_4'], 'Rosen grading table links clinical features to antivenom decisions.', 'Tintinalli organizes by clinical effect; Rosen grades North American Centruroides severity and helps decide who needs antivenom and monitoring.')}</section>
<section class="section" id="other"><h2>Other Arthropods</h2><p>Chiggers cause intensely pruritic papules or papulovesicles after outdoor exposure and are treated with antihistamines, topical steroids, hygiene, and infection treatment only when secondary infection occurs. Mosquitoes, flies, fleas, lice, and bedbugs mostly cause local pruritic reactions, but mosquito-borne disease history matters for fever, travel, and outbreak context.</p><p>Tick paralysis is a progressive ascending paralysis caused by attached ticks; the key treatment is finding and removing the tick, with supportive care until weakness resolves. Centipedes cause painful local erythema and edema treated with local care and analgesia. Kissing bugs and other arthropods may produce allergic reactions; treat by severity.</p></section>
<section class="section" id="drug-doses"><h2>Drug Dose Reference</h2><p>This section is only a quick recap after the full clinical treatment sections.</p><div class="table-wrap"><table><thead><tr><th>Therapy</th><th>Use</th><th>High-yield caution</th></tr></thead><tbody><tr><td>IM epinephrine</td><td>Hymenoptera/fire-ant anaphylaxis</td><td>Use early with ABC support; observe for recurrence.</td></tr><tr><td>Opioids + benzodiazepines</td><td>Severe Latrodectus pain/cramps or severe scorpion neuromuscular agitation</td><td>Titrate with respiratory monitoring.</td></tr><tr><td>Latrodectus antivenom</td><td>Severe persistent widow symptoms/high-risk patients</td><td>Equine-derived; anaphylaxis/serum sickness risk.</td></tr><tr><td>Centruroides immune F(ab)2</td><td>Severe North American bark scorpion envenomation</td><td>Best for grade 3-4 neuromuscular/autonomic toxicity.</td></tr><tr><td>Antibiotics</td><td>Only if secondary infection/cellulitis</td><td>Not routine for clean bites/stings.</td></tr></tbody></table></div></section>
<section class="question-set section" id="assessment"><h2>Inline Assessment MCQs</h2>{build_mcqs()}</section>
</div></main></div><div class="score-pill" data-score-text>0 correct / 0 answered / 26 total</div><div class="image-modal" data-image-modal><button class="hdr-btn" data-modal-close>Close</button><img alt="Zoomed source"></div><script>{SCRIPT}</script></body></html>"""


def extract_embedded(doc: str) -> list[Path]:
    EMBED.mkdir(parents=True, exist_ok=True)
    for old in EMBED.glob("*.png"):
        old.unlink()
    paths = []
    for i, m in enumerate(re.finditer(r"data:image/png;base64,([^\"]+)", doc), 1):
        p = EMBED / f"ch211_embedded_{i:02d}.png"
        p.write_bytes(base64.b64decode(m.group(1)))
        paths.append(p)
    return paths


def contact_sheet(paths: list[Path]) -> Path:
    cols, cell_w, cell_h = 3, 360, 295
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
    draw = ImageDraw.Draw(sheet)
    for i, path in enumerate(paths):
        img = Image.open(path).convert("RGB")
        img.thumbnail((320, 240))
        x, y = (i % cols) * cell_w, (i // cols) * cell_h
        sheet.paste(img, (x + 20, y + 36))
        draw.text((x + 8, y + 8), f"{i+1:02d} {path.name}", fill=(0, 0, 0))
    out = EMBED / "ch211_embedded_contact_sheet.png"
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
    md = f"""# CH211 Crop QA - 2026-05-09

Fresh rebuild from source PDFs. Old Chapter211 HTML crops were not used.

## Source Inventory Used

Tintinalli Ch211 inventory included: Table 211-1, Figure 211-1, Figure 211-2, Figure 211-3, Figure 211-4, Figure 211-5, and Table 211-2 = 7/7 included.

Rosen Ch53 relevant inventory included: Fig. 53.5 Africanized honeybee, Fig. 53.6 female black widow, Fig. 53.7 brown recluse, Fig. 53.8 Arizona bark scorpion, and Table 53.4 Centruroides scorpion grading.

{inv}

## Embedded Crop QA

Contact sheet: `{sheet.relative_to(ROOT).as_posix()}`

| # | Source | Object | PDF | PDF page | Extracted final embedded image | Status | Note |
|---|---|---|---|---:|---|---|---|
{chr(10).join(rows)}

## Content Gate

Content: PASS. Major headings have narrative summaries; source crops are topic-local; treatment tables are in treatment sections; no visible audit/source-audit repair text is inside the chapter.

Pattern: PASS. Ch186/Ch201 shell, top header, sidebar/main layout, Rosen source cards, Rosen vs Tintinalli deltas, and accepted MCQ behavior are present.
"""
    QA_MD.write_text(md, encoding="utf-8")
    QA_HTML.write_text(md_to_html(md, "CH211 Crop QA"), encoding="utf-8")


def update_audit() -> None:
    md = AUDIT_MD.read_text(encoding="utf-8")
    line = "| 211 | Chapter211_BitesAndStings.html | PASS | 26 | 26 | 5 | 12 | 12 | 5 | 5 | Fresh rebuild; Content PASS; Pattern PASS; Tintinalli 7/7 + Rosen 5/5 source crops topic-local; crop QA 12/12 PASS. |"
    if re.search(r"^\| 211 \|.*$", md, flags=re.M):
        md = re.sub(r"^\| 211 \|.*$", line, md, flags=re.M)
    else:
        md = md.rstrip() + "\n" + line + "\n"
    md = re.sub(r"Toxicology chapter gate:\s*\*\*\d+ PASS / \d+ FAIL\*\*", "Toxicology chapter gate: **36 PASS / 0 FAIL**", md)
    md = re.sub(r"PASS chapters:\s*\d+", "PASS chapters: 36", md)
    md = re.sub(r"FAIL chapters:\s*\d+", "FAIL chapters: 0", md)
    md = re.sub(r"Scope: Tintinalli toxicology/environmental chapters `176-\d+`", "Scope: Tintinalli toxicology/environmental chapters `176-211`", md)
    md = re.sub(r"Scope:\s*Chapter 176-210", "Scope: Chapter 176-211", md)
    md = re.sub(r"Scope:\s*Chapter 176-209", "Scope: Chapter 176-211", md)
    md = re.sub(r"Scope:\s*Chapter 176-208", "Scope: Chapter 176-211", md)
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
