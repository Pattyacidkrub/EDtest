# Toxicology Chapter Workflow

This file is the standing rule for continuing the toxicology chapter build.

## Source Hierarchy

- Tintinalli is the chapter spine: chapter order, headings, tables, figures, core management flow, and board emphasis follow Tintinalli first.
- **Every Tintinalli table and figure in the chapter scope must be inventoried and included as a source crop unless the user explicitly says to omit it.** Do not choose only the "important-looking" Tintinalli tables/figures. If the source chapter contains `Figure 260-1` through `Figure 260-4` and `Table 260-1` through `Table 260-10`, the completed HTML and crop QA must account for all 14 objects.
- Rosen must be integrated as real content, not just named in metadata or MCQ references.
- If Rosen cannot be located quickly, stop and find the Rosen section before publishing.

## Required Chapter Structure

Every completed toxicology chapter must include:

- **Rebuild-first rule:** after this point, do not "patch" an old generated chapter just to satisfy counts. If a chapter is incomplete, legacy-styled, table-heavy, crop-problematic, or fails any gate, rebuild the chapter body and shell into the accepted Ch186/Ch201 teaching format before marking it complete.
- A rebuild means re-reading the source spine, rewriting the major sections as coherent board-review narrative, placing source tables/figures beside the exact topic they support, rebuilding MCQs so explanations for every option show after answering, redoing crop QA from the final embedded images, and then updating audit.
- Mechanical fixes alone are not completion. Adding MCQs, adding `<mark>`/`<u>`, renaming classes, or adding a headbar to an otherwise thin chapter is still `FAIL` until the rebuilt chapter reads like the accepted examples.
- Tintinalli-based narrative sections.
- Every major Tintinalli heading/topic must have a real narrative summary. Do not leave a section as only source tables plus one short paragraph.
- Content completeness is a required audit gate, not an optional style check. A chapter is `FAIL` if any major clinical heading is table-only, image-only, source-card-only, or has only a token paragraph.
- Tables/figures must be inserted next to the exact clinical topic they support, not dumped as a block at the start or end of the chapter.
- Treatment tables/figures belong inside the relevant treatment subsection. Do not move treatment source tables into `Drug Dose Reference`; that section is only a quick recap after the full clinical treatment discussion.
- For each toxin/topic, include the useful board-facing sequence when applicable:
  - sources/exposure pattern
  - pathophysiology/mechanism
  - clinical features
  - diagnostic/lab pattern
  - ED treatment
  - disposition/observation traps
- Source figure/table cards from Tintinalli when available.
- For Tintinalli, "when available" means every table/figure label found inside the chapter's Tintinalli source span, not a selected subset. The audit must explicitly say `Tintinalli inventory X/X` or `every Tintinalli figure/table included (X/X)`.
- Rosen must follow the Chapter201 pattern, not a single summary box:
  - add visible `Rosen source` cards in the relevant section
  - include every Rosen figure/table that belongs to the topic being built
  - include a clear `Rosen vs Tintinalli` difference statement for each Rosen figure/table/card
  - put Rosen cards next to the clinical topic they modify, not only in one late section
  - add Rosen to hero/sidebar/source metadata when the chapter layout supports it
- Rosen audit belongs in the separate audit file, not as a visible chapter section, unless the user explicitly asks to show it inside the HTML.
- MCQ rationales that reference both Tintinalli and Rosen where relevant.
- Drug Dose Reference when any antidote, chelator, resuscitation drug, decontamination therapy, or directed treatment appears.
  - Drug Dose Reference must be a concise dose recap only.
  - It must not be the only place where treatment tables or treatment logic appear.
- Inline MCQ target: at least 6.
- Board-style/end MCQ target: at least 20.
- Strong visual emphasis: marked terms, color callouts, high-yield traps, and board-facing wording.

### Non-Negotiable Content Audit Gate

Before marking any chapter complete, run a content audit in addition to the mechanical MCQ/emphasis/crop checks.

If a chapter fails content, source placement, crop, MCQ behavior, or Ch186/Ch201 layout, the default repair is a rebuild, not a patch. Do not report a rebuilt chapter as complete until the final HTML has been read/opened again and the audit row passes the workflow markdown gate.

Do not trust a mechanical pass by itself. A chapter is not complete until the human content/source gate passes after opening or reading the rebuilt HTML.

A chapter fails the content audit if any of these are true:

- A major heading or clinical topic has no real narrative summary.
- A major section is mostly tables, figures, source cards, or MCQs with little explanatory prose.
- A toxin/topic is missing one of the expected clinical elements when applicable: exposure/source, pathophysiology, clinical features, diagnostic/lab pattern, ED treatment, and disposition/observation traps.
- Treatment content appears only in `Drug Dose Reference` or only as a source table. Treatment tables must be discussed in the relevant treatment subsection first.
- Tables/figures are clustered together away from the topic they support.
- The chapter omits any Tintinalli table or figure from the chapter source span without a written exclusion approved by the user. Missing Tintinalli objects are `Content: FAIL` even if the chapter has many other source cards.
- Visible audit material appears inside the chapter body, such as `Rosen Source Audit`, `Source Audit`, `Included`, `Excluded`, or repair notes. Audit content belongs only in the separate audit file.
- Rosen, Tintinalli, ATLS, or any other source is named in metadata/sidebar but not integrated into the relevant body section.
- For trauma chapters, ATLS must be integrated in the clinical narrative and not only mentioned in metadata, captions, or MCQ rationales.
- Legacy inline MCQs remain as `mcq-card` blocks instead of the accepted `mcq-wrapper` interaction pattern.
- MCQ click behavior reveals only the selected option explanation. Accepted chapters must reveal every option explanation after answering.

The chapter audit file must include a content gate result:

- `Content: PASS` only when every major topic has enough narrative and tables/figures are topic-local.
- `Content: FAIL` with short reasons when narrative is thin, table-only, misplaced, or visibly contains audit/repair text.

If content fails, rebuild the affected sections before fixing cosmetic details. Do not use MCQs, source cards, or tables as a substitute for the missing narrative.

Ch186 failure lesson: never mark a chapter `PASS` just because crop QA, MCQ count, and emphasis counts pass. First check for leftover legacy `mcq-card`, thin standalone Rosen/ATLS source cards, sparse emphasis by section, table-only treatment sections, and misplaced treatment tables. Any one of these is `Content: FAIL` until repaired and re-audited.

### Non-Negotiable Chapter201 Pattern Gate

The workflow markdown is an audit gate, not background reading. Before any toxicology chapter is marked `PASS`, run a Chapter201-pattern audit against the final HTML.

A complete chapter must match the accepted **Ch186/Ch201 visual shell** and Chapter201 teaching pattern unless the user explicitly asks for a different format:

- Uses the Chapter201 layout family: `.app`, `.sidebar`, `.sidebar__block`, `.main`, `.utility-bar`, `.hero__title`, and `.section`.
- Uses the Chapter201 visible headbar: `#top-header` with `.hdr-btn` controls before `.app`; missing headbar is an automatic FAIL even if `.utility-bar` exists.
- The first visible screen must not have a blank top gap. The top shell must follow Ch186/Ch201: fixed `#top-header`, left menu button, chapter title, dark/theme button, then `.app`.
- Uses the Ch186/Ch201 navigation shell, not a loose approximation: `#sidebar` is fixed below `#top-header`, `#main` is offset from the sidebar, sidebar links use `.sidebar__link`, and the sidebar has a close control for small screens.
- Do not mark a chapter `PASS` if it only has the right content classes but the shell feels different from Ch186/Ch201: sticky grid sidebars, missing main offset, missing close button, missing sidebar link styling, or blank spacing at the top are `FAIL`.
- Uses Chapter201 source components for source material: `.source-card`, `.source-card__label`, `.source-card__title`, `.reference-image`, and, when comparing sources, `.source-delta`.
- Rosen integration must be visible in the body with `Rosen source` cards, `Rosen vs Tintinalli` differences, and topic-local placement. A single end-of-chapter Rosen paragraph is `FAIL`.
- MCQs must use the accepted `mcq-wrapper`, `mcq-options`, `opt-explain`, and `mcq-result` pattern. The click handler must reveal every option explanation after answering.
- Source images must be embedded as final `data:image` images or otherwise extracted from the final HTML for crop QA. External image links alone are not enough for completion.
- The audit row must include `Pattern: PASS` only if the Chapter201-pattern audit passes.

Minimum automatic checks before any `PASS`:

- `#top-header` count exactly 1 and `.hdr-btn` count at least 2
- For Chapter201 `.app` layout files, `<body>` must put `#top-header` before `.app`; `<body><div class="app">` without `#top-header` is `FAIL`.
- For older legacy shells without `.app`, `#top-header` must still be the first visible shell before sidebar/main content; a blank top area or missing fixed headbar is `FAIL`.
- `#sidebar` count exactly 1 and `#main` count exactly 1 for Ch186/Ch201-style chapters.
- CSS must include a fixed sidebar below the headbar: `#sidebar.sidebar` or equivalent fixed `#sidebar` with `top: var(--header-h)`.
- CSS must include main content offset: `#main`/`.main` with `margin-left: var(--sidebar-w)` or equivalent sidebar-width offset.
- `.sidebar__link` count greater than 0 for navigational sidebar links.
- `.sidebar-close` or `[data-sidebar-close]` must be present for mobile/small-screen sidebar behavior.
- `.sidebar__block` count greater than 0
- `.hero__title` count greater than 0
- `.section` count greater than 0
- `.source-card__label` count greater than 0 when source cards exist
- `.reference-image` count matches embedded source images
- `Rosen source` card count greater than 0 when Rosen is used
- `Rosen vs Tintinalli` count greater than 0 when Rosen is used
- `.mcq-wrapper` count at least 26
- `.mcq-result` count matches `.mcq-wrapper`
- final `data:image` count matches the chapter crop QA rows

If any of these checks fail, keep the chapter `FAIL` even when content, MCQ count, emphasis count, and crop QA otherwise pass.

### Non-Negotiable Visual Emphasis Gate

Do not mark a chapter complete if the chapter reads like plain notes. Each completed chapter must keep the visual teaching style used in the accepted chapters (`Chapter201`, `Chapter202`, `Chapter178`, `Chapter192`, `Chapter191`).

Required before final reply:

- Every major content section must contain visible emphasis, such as `<mark>`, `<u>`, `<strong>`, and/or callout boxes.
- Board traps must be visually marked, not buried in plain paragraphs.
- Important toxin names, antidotes, contraindications, diagnostic clues, and disposition traps should be highlighted close to the relevant text.
- Do not remove emphasis while rewriting narrative sections.
- If a rewrite replaces a section, re-add the emphasis before running final checks.

Minimum file-level check before final reply:

- `<mark>` count must be greater than 0.
- `<u>` count must be greater than 0.
- Each major clinical section should have at least one marked or underlined board-facing phrase unless there is a clear reason not to.

## Rosen Figure/Table Rule

Before publishing a toxicology chapter:

- Search the relevant Rosen chapter/pages for all `Table`, `Fig.`, and algorithm labels.
- Capture or embed the relevant Rosen figure/table images the same way Chapter201 does.
- If a Rosen table spans a broader chapter, include the rows that directly affect the current Tintinalli chapter and save the broader table for the chapter where it belongs.
- Do not include a Rosen table/box just because it is nearby. If it is ocular, phone-number, WMD, or otherwise not useful for the current chapter, exclude it and state that in the audit.
- Before showing the user, visually sanity-check every Rosen crop: the image must contain the actual table/figure header and readable content, not a random paragraph slice or a half-cut table.
- Each Rosen card must answer:
  - What does Rosen add?
  - What is different from Tintinalli?
  - What exam/ED decision changes because of that difference?

## Tintinalli Figure/Table Inventory Gate

Before publishing any chapter, including trauma and non-toxicology chapters built with this workflow:

- Search the exact Tintinalli chapter source span for all `Table`, `TABLE`, `Figure`, `FIGURE`, `Fig.`, and algorithm labels.
- Build an inventory list before writing the final HTML. The inventory must include every Tintinalli source object label and PDF page.
- Embed every Tintinalli table/figure from that chapter as a real PDF crop in the final HTML. Do not redraw, retype, summarize-only, or silently omit a Tintinalli table/figure.
- Place every Tintinalli source card next to the relevant clinical topic. Do not dump all images at the start or end of the chapter.
- If a Tintinalli object spans multiple pages or columns, split into clearly labeled parts and include all parts needed to show title/header/body/footnotes.
- If a nearby label is outside the chapter scope, such as the next chapter's `Figure 261-1`, exclude it and record the exclusion in the QA/audit file, not inside the chapter HTML.
- The chapter-specific crop QA must include a line such as `Tintinalli inventory: 14/14 included` and list every Tintinalli crop row.
- The main audit row must include `every Tintinalli figure/table included (X/X)` before the chapter can be marked `PASS`.
- Any chapter missing one Tintinalli table or figure is `FAIL` until rebuilt or recropped. This rule overrides mechanical passes for MCQ count, emphasis count, HTTP status, and existing crop count.

## Figure/Table Crop Workflow

This crop workflow applies to all source images in any chapter, including Tintinalli, Rosen, ATLS, and any other PDF source.

### Non-Negotiable Crop Gate

Do not mark a chapter complete, do not say "done", and do not send the chapter for review unless a chapter-specific crop QA file exists and every embedded source image is marked `PASS`.

Required crop QA file name:

- `CH###_CROP_QA_YYYY-MM-DD.md`

The QA file must list every embedded source crop in the chapter, including Tintinalli, Rosen, ATLS, and any other source. This is mandatory even when only one new Rosen card was added. If the chapter already had Tintinalli crops, they still must be re-extracted from the final HTML and visually checked.

Each row in the crop QA file must include:

- source name, such as Tintinalli or Rosen
- object label, such as `Table 204-3` or `Fig. 148.2`
- source PDF filename
- PDF page number used for the crop
- embedded extracted image path
- visual QA status: `PASS`, `FAIL`, or `RECROP DONE -> PASS`
- short note confirming title/header/body/footnote status

Final response must include:

- chapter HTML path or URL
- complete chapter audit path
- chapter crop QA path
- crop count summary, for example: `12 embedded source crops checked, 12 PASS, 0 FAIL`

If any crop has not been extracted from the final HTML and opened visually, the chapter is not complete.

- Use the real source figure/table image from the PDF. Do not redraw, retype, or convert a source table into HTML unless the user explicitly asks for that.
- Crop the complete source object, not just the "useful-looking" middle:
  - table/figure number
  - title
  - column headers
  - every row/cell or full figure body
  - footnotes, legends, and continuation notes when present
- Never publish a crop that cuts off the left/right border, table title, bottom row, footnote, or figure legend.
- Never include unrelated surrounding material: paragraph fragments, next chapter headers, unrelated neighboring tables, or random page text.
- A crop that includes unrelated paragraphs below or above the source object is `FAIL`, even if the table itself is readable.
- A crop that was QA-checked before embed but not extracted from final HTML is `FAIL`.
- If the table/figure spans multiple pages, split into clearly labeled parts such as `part 1` and `part 2`. Each part must still have a sensible start/end. Include a caption explaining that it is a continuation.
- Prefer a wider/taller crop with clean margins over a tight crop that risks losing content. White margin is acceptable; missing content is not.
- After embedding the crop into HTML, extract the embedded `data:image` back out and open that extracted image for visual QA. Do not rely only on the pre-embed crop file.
- Visual QA checklist before showing the user:
  - source number/title visible
  - headers visible
  - all rows/body visible
  - footnote/legend visible if present
  - no unrelated page text attached
  - image readable in the chapter layout, including mobile width
  - caption matches the actual source image
- If a crop fails QA, recrop from the PDF and re-embed before sending the chapter.

### Required Self-Check Before Final Reply

Before replying to the user with a completed chapter, run a file-level check and include the result in the final answer:

- number of `figure.source-figure` images in the final HTML
- number of extracted embedded images in the crop QA folder
- number of rows in `CH###_CROP_QA_YYYY-MM-DD.md`
- whether every row is `PASS`

If these numbers do not match, stop and fix the mismatch before responding.

ATLS-specific note: ATLS figures/tables follow the same crop rules. If an ATLS algorithm/table is used, the crop must include the full algorithm/table title, decision boxes/rows, arrows/legend, and any footnotes or source notes. Do not trim ATLS algorithms so tightly that arrows, branch labels, or edge boxes are missing.

## Git Hygiene

- Stage only the intended chapter HTML plus `docs/index.html` and `docs/manifest.json`.
- Do not stage unrelated modified complete chapters.
- Watch for recurring publish-script contamination:
  - unwanted `A04` in `docs/index.html` or `docs/manifest.json`
  - altered `A16` local_refs/converted_images/missing counts
  - titles losing the word `and`
- Verify staged diff before commit.

## Current Repair Scope

The chapters created in this session must be repaired for real Rosen integration before continuing:

- `Chapter198_Iron.html`
- `Chapter199_HydrocarbonsVolatileSubstances.html`
- `Chapter200_CausticIngestions.html`
- `Chapter203_MetalsMetalloids.html`
- `Chapter204_IndustrialToxins.html`

Do not continue to Chapter205 until these are fixed and pushed.
