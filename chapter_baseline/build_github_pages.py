from __future__ import annotations

import hashlib
import html
import json
import os
import re
import shutil
import stat
import time
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
CHAPTER_DATA = ROOT / "chapter_data"
COMPLETE_DIR = ROOT / "_Handoff_20260506" / "Complete"
DOCS = ROOT / "docs"
BOARD_MANIFEST = ROOT / "board_2569_manifest.json"

SPECIAL_CHAPTERS = [
    {
        "id": "a01",
        "title": "A01 Solution Ready Special",
        "source": CHAPTER_DATA / "ChapterA01Special_SolutionReady.html",
        "output": "A01.html",
        "group": "special",
    },
    {
        "id": "a02",
        "title": "A02 Solution Ready Special",
        "source": CHAPTER_DATA / "ChapterA02Special_SolutionReady.html",
        "output": "A02.html",
        "group": "special",
    },
    {
        "id": "a03",
        "title": "A03 Solution Ready Special",
        "source": CHAPTER_DATA / "ChapterA03Special_SolutionReady.html",
        "output": "A03.html",
        "group": "special",
    },
    {
        "id": "a04",
        "title": "A04 Endocrine / Metabolic Study",
        "source": CHAPTER_DATA / "ChapterA04Special_EndocrineMetabolicStudy.html",
        "output": "A04.html",
        "group": "special",
    },
    {
        "id": "a05",
        "title": "A05 Solution Ready Special",
        "source": CHAPTER_DATA / "ChapterA05Special_SolutionReady.html",
        "output": "A05.html",
        "group": "special",
    },
    {
        "id": "a06",
        "title": "A06 Solution Ready Special",
        "source": CHAPTER_DATA / "ChapterA06Special_SolutionReady.html",
        "output": "A06.html",
        "group": "special",
    },
    {
        "id": "a07",
        "title": "A07 Solution Ready Special",
        "source": CHAPTER_DATA / "ChapterA07Special_SolutionReady.html",
        "output": "A07.html",
        "group": "special",
    },
    {
        "id": "a08",
        "title": "A08 Solution Ready Special",
        "source": CHAPTER_DATA / "ChapterA08Special_SolutionReady.html",
        "output": "A08.html",
        "group": "special",
    },
    {
        "id": "a09",
        "title": "A09 Infectious Study",
        "source": CHAPTER_DATA / "ChapterA09Special_InfectiousStudy.html",
        "output": "A09.html",
        "group": "special",
    },
    {
        "id": "a10",
        "title": "A10 Solution Ready Special",
        "source": CHAPTER_DATA / "ChapterA10Special_SolutionReady.html",
        "output": "A10.html",
        "group": "special",
    },
    {
        "id": "a11",
        "title": "A11 Solution Ready Special",
        "source": CHAPTER_DATA / "ChapterA11Special_SolutionReady.html",
        "output": "A11.html",
        "group": "special",
    },
    {
        "id": "a12",
        "title": "A12 Solution Ready Special",
        "source": CHAPTER_DATA / "ChapterA12Special_SolutionReady.html",
        "output": "A12.html",
        "group": "special",
    },
    {
        "id": "a13",
        "title": "A13 Solution Ready Special",
        "source": CHAPTER_DATA / "ChapterA13Special_SolutionReady.html",
        "output": "A13.html",
        "group": "special",
    },
    {
        "id": "a14",
        "title": "A14 Renal / Urogenital Study",
        "source": CHAPTER_DATA / "ChapterA14Special_RenalUrogenitalStudy.html",
        "output": "A14.html",
        "group": "special",
    },
    {
        "id": "a15",
        "title": "A15 Solution Ready Special",
        "source": CHAPTER_DATA / "ChapterA15Special_SolutionReady.html",
        "output": "A15.html",
        "group": "special",
    },
    {
        "id": "a16",
        "title": "A16 Toxicology Study",
        "source": CHAPTER_DATA / "ChapterA16Special_ToxicologyStudy.html",
        "output": "A16.html",
        "group": "special",
    },
    {
        "id": "a17",
        "title": "A17 Solution Ready Special",
        "source": CHAPTER_DATA / "ChapterA17Special_SolutionReady.html",
        "output": "A17.html",
        "group": "special",
    },
    {
        "id": "b",
        "title": "B Solution Ready Special",
        "source": CHAPTER_DATA / "ChapterBSpecial_SolutionReady.html",
        "output": "B.html",
        "group": "special",
    },
    {
        "id": "c",
        "title": "C EMS Study",
        "source": CHAPTER_DATA / "ChapterCSpecial_EMSStudy.html",
        "output": "C.html",
        "group": "special",
    },
    {
        "id": "d",
        "title": "D Solution Ready Special",
        "source": CHAPTER_DATA / "ChapterDSpecial_SolutionReady.html",
        "output": "D.html",
        "group": "special",
    },
    {
        "id": "e",
        "title": "E Solution Ready Special",
        "source": CHAPTER_DATA / "ChapterESpecial_SolutionReady.html",
        "output": "E.html",
        "group": "special",
    },
]


def load_special_chapters() -> list[dict[str, str]]:
    data = json.loads(BOARD_MANIFEST.read_text(encoding="utf-8"))
    chapters: list[dict[str, str]] = []
    for item in data["blueprint"]:
        code = item["code"]
        chapters.append(
            {
                "id": code.lower(),
                "title": f"{code} {item['name']}",
                "source": CHAPTER_DATA / f"Chapter{code}Special_SolutionReady.html",
                "output": f"{code}.html",
                "group": "special",
            }
        )
    return chapters


SPECIAL_CHAPTERS = load_special_chapters()

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
PASSTHROUGH_EXTENSIONS = {".css", ".js", ".svg", ".gif", ".ico", ".pdf"}
HTML_EXTENSIONS = {".html", ".htm"}
REMOTE_PREFIXES = ("http://", "https://", "data:", "mailto:", "#")


class AttrCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.refs: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for key, value in attrs:
            if key in {"src", "href"} and value:
                self.refs.append((key, html.unescape(value)))


def is_remote(ref: str) -> bool:
    return ref.startswith(REMOTE_PREFIXES)


def slugify(value: str) -> str:
    stem = Path(value).stem.lower()
    stem = re.sub(r"[^a-z0-9]+", "-", stem).strip("-")
    return stem[:70] or "asset"


def chapter_sort_key(path: Path) -> tuple[int, str]:
    match = re.search(r"Chapter(\d+)", path.name, re.I)
    return (int(match.group(1)) if match else 9999, path.name.lower())


def complete_title(path: Path) -> str:
    match = re.match(r"Chapter(\d+)_(.+)\.html$", path.name, re.I)
    if not match:
        return path.stem
    chapter_no, raw_title = match.groups()
    spaced = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", raw_title)
    return f"Ch.{chapter_no} {spaced}"


def complete_chapters() -> list[dict[str, str]]:
    if not COMPLETE_DIR.exists():
        return []
    chapters = []
    for path in sorted(COMPLETE_DIR.glob("*.html"), key=chapter_sort_key):
        match = re.search(r"Chapter(\d+)", path.name, re.I)
        chapter_id = f"ch{match.group(1)}" if match else slugify(path.name)
        chapters.append(
            {
                "id": chapter_id,
                "title": complete_title(path),
                "source": path,
                "output": f"complete/{path.name}",
                "group": "complete",
            }
        )
    return chapters


def resolve_ref(ref: str, html_path: Path) -> Path | None:
    if is_remote(ref):
        return None

    clean_ref = ref.split("#", 1)[0].split("?", 1)[0]
    direct = (html_path.parent / clean_ref).resolve()
    if direct.exists():
        return direct

    # Some older generated paths missed a "../". Recover by basename so publish
    # does not silently omit the image.
    basename = Path(clean_ref).name
    matches = list(ROOT.rglob(basename))
    if matches:
        return matches[0].resolve()
    return None


def output_image_path(source: Path, chapter_id: str) -> Path:
    digest = hashlib.sha1(str(source).encode("utf-8")).hexdigest()[:10]
    return DOCS / "assets" / chapter_id / f"{slugify(source.name)}-{digest}.webp"


def output_passthrough_path(source: Path) -> Path:
    digest = hashlib.sha1(str(source).encode("utf-8")).hexdigest()[:10]
    suffix = source.suffix.lower()
    return DOCS / "assets" / "shared" / f"{slugify(source.name)}-{digest}{suffix}"


def convert_image(source: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_mtime >= source.stat().st_mtime:
        return

    with Image.open(source) as image:
        image = ImageOps.exif_transpose(image)
        if image.mode not in {"RGB", "RGBA"}:
            image = image.convert("RGBA" if "A" in image.getbands() else "RGB")

        max_width = 1800
        if image.width > max_width:
            new_height = round(image.height * (max_width / image.width))
            image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)

        for attempt in range(5):
            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                if image.mode == "RGBA":
                    # WebP supports alpha; quality keeps highlighted textbook crops readable.
                    image.save(dest, "WEBP", quality=86, method=6)
                else:
                    image.save(dest, "WEBP", quality=84, method=6)
                break
            except FileNotFoundError:
                if attempt == 4:
                    raise
                time.sleep(0.2)


def copy_passthrough(source: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists() or dest.stat().st_mtime < source.stat().st_mtime:
        for attempt in range(5):
            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, dest)
                break
            except FileNotFoundError:
                if attempt == 4:
                    raise
                time.sleep(0.2)


def rewrite_html(
    chapter: dict[str, str],
    manifest: dict[str, dict[str, str]],
    published_html_names: set[str],
) -> dict[str, int | str]:
    html_path = Path(chapter["source"])
    chapter_id = chapter["id"]
    output_name = chapter["output"]
    text = html_path.read_text(encoding="utf-8")
    out = DOCS / "chapters" / output_name
    collector = AttrCollector()
    collector.feed(text)

    ref_map: dict[str, str] = {}
    stats = {
        "local_refs": 0,
        "converted_images": 0,
        "copied_assets": 0,
        "disabled_links": 0,
        "missing": 0,
    }

    for _attr, ref in collector.refs:
        if ref in ref_map or is_remote(ref):
            continue
        clean_ref = ref.split("#", 1)[0].split("?", 1)[0]
        if Path(clean_ref).suffix.lower() in HTML_EXTENSIONS:
            if Path(clean_ref).name not in published_html_names:
                ref_map[ref] = "#"
                stats["disabled_links"] += 1
            continue
        resolved = resolve_ref(ref, html_path)
        if not resolved:
            stats["missing"] += 1
            continue

        suffix = resolved.suffix.lower()
        if suffix in IMAGE_EXTENSIONS:
            dest = output_image_path(resolved, chapter_id)
            try:
                convert_image(resolved, dest)
            except OSError:
                stats["missing"] += 1
                continue
            stats["converted_images"] += 1
        elif suffix in PASSTHROUGH_EXTENSIONS:
            dest = output_passthrough_path(resolved)
            try:
                copy_passthrough(resolved, dest)
            except OSError:
                stats["missing"] += 1
                continue
            stats["copied_assets"] += 1
        else:
            continue

        stats["local_refs"] += 1
        ref_map[ref] = Path(os.path.relpath(dest, out.parent)).as_posix()

    def attr_replacer(match: re.Match[str]) -> str:
        attr = match.group(1)
        quote = match.group(2)
        raw = html.unescape(match.group(3))
        replacement = ref_map.get(raw)
        if not replacement:
            return match.group(0)
        return f'{attr}={quote}{html.escape(replacement, quote=True)}{quote}'

    text = re.sub(r'\b(src|href)=(["\'])(.*?)\2', attr_replacer, text)

    # Safari/iOS friendliness: avoid eager image decode/loading when opening
    # long chapters with many textbook crops.
    text = re.sub(r"<img(?![^>]*\bloading=)", "<img loading=\"lazy\"", text)
    text = re.sub(r"<img(?![^>]*\bdecoding=)", "<img decoding=\"async\"", text)

    # Make the page usable when installed to home screen and show the optimized
    # publish provenance in dev tools.
    text = text.replace(
        "</head>",
        (
            '<meta name="theme-color" content="#f7f3ea">'
            f'<meta name="x-published-from" content="{html.escape(html_path.name)}">'
            "</head>"
        ),
        1,
    )

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")

    manifest[chapter_id] = {
        "title": chapter["title"],
        "html": f"chapters/{output_name}",
        "source": str(html_path.relative_to(ROOT)),
        "group": chapter.get("group", "special"),
        "local_refs": str(stats["local_refs"]),
        "converted_images": str(stats["converted_images"]),
        "copied_assets": str(stats["copied_assets"]),
        "disabled_links": str(stats["disabled_links"]),
        "missing": str(stats["missing"]),
    }
    return stats | {"output": str(out)}


def dir_size(path: Path) -> int:
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def build_cards(chapters: Iterable[dict[str, str]], manifest: dict[str, dict[str, str]], label: str) -> str:
    cards = []
    for chapter in chapters:
        chapter_id = chapter["id"]
        item = manifest[chapter_id]
        cards.append(
            f"""
            <a class="chapter-card" href="{html.escape(item['html'])}">
              <span class="chapter-card__eyebrow">{chapter_id.upper()}</span>
              <strong>{html.escape(item['title'])}</strong>
              <span>{html.escape(label)}</span>
            </a>
            """
        )
    return "".join(cards)


def build_index(chapters: list[dict[str, str]], manifest: dict[str, dict[str, str]]) -> None:
    existing = DOCS / "index.html"
    if existing.exists() and os.environ.get("ER_PUBLISH_REBUILD_INDEX") != "1":
        text = existing.read_text(encoding="utf-8")
        if "chapter-row" in text and "chapterSearch" in text:
            return

    old_exam_label = "ข้อสอบเก่า"
    special = [chapter for chapter in chapters if chapter.get("group") == "special"]

    def docs_complete_chapters() -> list[dict[str, str]]:
        complete_dir = DOCS / "chapters" / "complete"
        found: list[dict[str, str]] = []
        if not complete_dir.exists():
            return found
        for path in sorted(complete_dir.glob("Chapter*.html"), key=chapter_sort_key):
            match = re.search(r"Chapter(\d+)", path.name, re.I)
            chapter_id = f"ch{match.group(1)}" if match else slugify(path.name)
            found.append(
                {
                    "id": chapter_id,
                    "title": complete_title(path),
                    "html": f"chapters/complete/{path.name}",
                    "group": "complete",
                }
            )
        return found

    complete = docs_complete_chapters()

    def complete_category(chapter_id: str) -> str:
        number_match = re.search(r"\d+", chapter_id)
        number = int(number_match.group(0)) if number_match else 0
        if number == 1:
            return "EMS"
        if 48 <= number <= 61:
            return "Cardiology"
        if 62 <= number <= 64:
            return "Pulmonary"
        if 151 <= number <= 152:
            return "Infectious"
        if 176 <= number <= 207:
            return "Toxicology"
        if 208 <= number <= 213:
            return "Environmental"
        if 254 <= number <= 260:
            return "Trauma"
        return "Other"

    def category_class(category: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", category.lower()).strip("-")

    def complete_row(chapter: dict[str, str]) -> str:
        number_match = re.search(r"\d+", chapter["id"])
        number = int(number_match.group(0)) if number_match else 0
        display_title = re.sub(r"^Ch\.\d+\s+", "", chapter["title"])
        category = complete_category(chapter["id"])
        return f"""
      <a class="chapter-row" href="{html.escape(chapter['html'])}" data-type="chapter" data-title="{html.escape(display_title.lower())}" data-chapter="{number}" data-category="{html.escape(category)}">
        <span class="chapter-no">CH{number:03d}</span>
        <span class="chapter-main"><strong>{html.escape(display_title)}</strong><span>Open chapter</span></span>
        <span class="category-pill category-{category_class(category)}">{html.escape(category)}</span>
        <span class="open-mark" aria-hidden="true">›</span>
      </a>"""

    def special_row(chapter: dict[str, str]) -> str:
        item = manifest[chapter["id"]]
        code = chapter["id"].upper()
        title = item["title"]
        search = f"{code} {title} {old_exam_label} old exam special".lower()
        return f"""
      <a class="chapter-row special-row" href="{html.escape(item['html'])}" data-type="special" data-title="{html.escape(search)}" data-chapter="{html.escape(code.lower())}" data-category="{html.escape(old_exam_label)}">
        <span class="chapter-no">{html.escape(code)}</span>
        <span class="chapter-main"><strong>{html.escape(title)}</strong><span>เปิดข้อสอบเก่า</span></span>
        <span class="category-pill category-special">{html.escape(old_exam_label)}</span>
        <span class="open-mark" aria-hidden="true">›</span>
      </a>"""

    special_rows = "".join(special_row(chapter) for chapter in special)
    complete_rows = "".join(complete_row(chapter) for chapter in complete)

    categories = Counter(complete_category(chapter["id"]) for chapter in complete)
    category_order = ["Cardiology", "Pulmonary", "Toxicology", "Environmental", "Trauma", "Infectious", "EMS"]
    filter_buttons = [
        f'<button class="filter-button is-active" type="button" data-filter="All">All<span>{len(complete)}</span></button>',
        f'<button class="filter-button" type="button" data-filter="{html.escape(old_exam_label)}">{html.escape(old_exam_label)}<span>{len(special)}</span></button>'
    ]
    for category in category_order:
        if categories.get(category):
            filter_buttons.append(
                f'<button class="filter-button" type="button" data-filter="{html.escape(category)}">{html.escape(category)}<span>{categories[category]}</span></button>'
            )

    index = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
  <meta http-equiv="Pragma" content="no-cache">
  <meta http-equiv="Expires" content="0">
  <meta name="theme-color" content="#f6f8f8">
  <title>ER Board Review</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f8f8;
      --surface: #ffffff;
      --surface-soft: #edf3f4;
      --ink: #152127;
      --muted: #66747c;
      --line: #d6e0e4;
      --accent: #0f717a;
      --accent-dark: #0b5960;
      --rust: #a33729;
      --shadow: 0 12px 34px rgba(25, 43, 50, .08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background: var(--bg);
      line-height: 1.42;
    }}
    main {{ width: min(1080px, calc(100% - 32px)); margin: 0 auto; padding: 24px 0 40px; }}
    .topbar {{ display: grid; grid-template-columns: 1fr auto; gap: 18px; align-items: end; padding-bottom: 18px; border-bottom: 1px solid var(--line); }}
    h1 {{ margin: 0; font-size: clamp(2rem, 5vw, 3.5rem); line-height: 1; letter-spacing: 0; }}
    .lede {{ margin: 9px 0 0; color: var(--muted); max-width: 620px; }}
    .stats {{ display: flex; gap: 10px; align-items: stretch; }}
    .stat {{ min-width: 132px; padding: 12px 14px; border: 1px solid var(--line); border-radius: 8px; background: var(--surface); box-shadow: var(--shadow); }}
    .stat strong {{ display: block; font-size: 1.65rem; line-height: 1; }}
    .stat span {{ color: var(--muted); font-size: .84rem; }}
    .toolbar {{ position: sticky; top: 0; z-index: 5; margin: 16px 0; padding: 10px; border: 1px solid var(--line); border-radius: 8px; background: rgba(255,255,255,.95); box-shadow: var(--shadow); backdrop-filter: blur(10px); }}
    .search-row {{ display: grid; grid-template-columns: 1fr auto; gap: 10px; }}
    .search-input {{ width: 100%; min-height: 44px; padding: 0 13px; border: 1px solid var(--line); border-radius: 8px; background: var(--surface-soft); color: var(--ink); font: inherit; outline: none; }}
    .search-input:focus {{ border-color: var(--accent); box-shadow: 0 0 0 3px rgba(15,113,122,.14); }}
    .clear-button {{ min-height: 44px; padding: 0 14px; border: 1px solid var(--line); border-radius: 8px; background: var(--surface); color: var(--ink); font: inherit; cursor: pointer; }}
    .filters {{ display: flex; gap: 8px; overflow-x: auto; padding-top: 9px; }}
    .filter-button {{ flex: 0 0 auto; display: inline-flex; align-items: center; gap: 7px; min-height: 34px; padding: 0 11px; border: 1px solid var(--line); border-radius: 999px; background: var(--surface); color: var(--ink); font: inherit; cursor: pointer; }}
    .filter-button span {{ color: var(--muted); font-size: .8rem; }}
    .filter-button.is-active {{ background: var(--accent); border-color: var(--accent); color: #fff; }}
    .filter-button.is-active span {{ color: rgba(255,255,255,.8); }}
    .section-block {{ margin-top: 22px; }}
    .section-head {{ display: flex; justify-content: space-between; align-items: baseline; gap: 16px; margin: 0 0 9px; }}
    h2 {{ margin: 0; color: var(--rust); font-size: 1rem; letter-spacing: 0; }}
    .result-count {{ color: var(--muted); font-size: .9rem; }}
    .chapter-list {{ overflow: hidden; border: 1px solid var(--line); border-radius: 8px; background: var(--surface); box-shadow: 0 1px 0 rgba(20,30,35,.03); }}
    .chapter-row {{ min-height: 58px; display: grid; grid-template-columns: 86px 1fr 132px 28px; gap: 12px; align-items: center; padding: 10px 14px; border-top: 1px solid var(--line); color: inherit; text-decoration: none; }}
    .chapter-row:first-child {{ border-top: 0; }}
    .chapter-row:hover {{ background: #f9fcfc; }}
    .chapter-row[hidden], .section-block[hidden] {{ display: none !important; }}
    .chapter-no {{ color: var(--rust); font-weight: 800; font-size: .86rem; }}
    .chapter-main strong {{ display: block; font-size: 1rem; font-weight: 720; }}
    .chapter-main span {{ display: none; color: var(--accent-dark); font-weight: 700; font-size: .86rem; margin-top: 2px; }}
    .category-pill {{ justify-self: start; min-width: 100px; padding: 5px 9px; border-radius: 999px; background: #edf3f4; color: #46626b; text-align: center; font-size: .78rem; font-weight: 700; }}
    .category-cardiology {{ background: #e7f4f2; color: #14675f; }}
    .category-pulmonary {{ background: #e9f0fb; color: #365f93; }}
    .category-toxicology {{ background: #f8ece8; color: #914130; }}
    .category-environmental {{ background: #edf3e7; color: #526f2c; }}
    .category-trauma {{ background: #eceefa; color: #4c5791; }}
    .category-infectious {{ background: #f4eef8; color: #72518b; }}
    .category-ems {{ background: #f1efe9; color: #695d47; }}
    .category-special {{ background: #e7f6f7; color: #0f717a; }}
    .open-mark {{ color: var(--muted); font-size: 1.35rem; line-height: 1; }}
    .empty {{ display: none; padding: 22px; border: 1px dashed var(--line); border-radius: 8px; background: var(--surface); color: var(--muted); }}
    .empty.is-visible {{ display: block; }}
    footer {{ margin-top: 26px; color: var(--muted); font-size: .88rem; }}
    @media (max-width: 760px) {{
      main {{ width: min(100% - 22px, 1080px); padding-top: 16px; }}
      .topbar {{ grid-template-columns: 1fr; align-items: start; }}
      .stats {{ width: 100%; }}
      .stat {{ flex: 1; }}
      .toolbar {{ margin-left: -11px; margin-right: -11px; border-left: 0; border-right: 0; border-radius: 0; }}
      .search-row {{ grid-template-columns: 1fr; }}
      .filters {{ padding-bottom: 1px; }}
      .chapter-list {{ border-radius: 8px; }}
      .chapter-row {{ min-height: 78px; grid-template-columns: 70px 1fr auto; grid-template-areas: "no main mark" "cat main mark"; gap: 4px 10px; padding: 12px; }}
      .chapter-no {{ grid-area: no; }}
      .chapter-main {{ grid-area: main; }}
      .chapter-main strong {{ font-size: .98rem; }}
      .chapter-main span {{ display: block; }}
      .category-pill {{ grid-area: cat; min-width: 0; justify-self: start; padding: 3px 7px; font-size: .72rem; }}
      .open-mark {{ grid-area: mark; }}
    }}
  </style>
</head>
<body>
  <main>
    <header class="topbar">
      <div>
        <h1>ER Board Review</h1>
        <p class="lede">Fast chapter library for board review. Search by chapter number, topic, or section.</p>
      </div>
      <div class="stats"><div class="stat"><strong>{len(complete)}</strong><span>complete chapters</span></div><div class="stat"><strong>{len(special)}</strong><span>special sets</span></div></div>
    </header>

    <section class="toolbar" aria-label="Chapter search and filters">
      <div class="search-row">
        <input id="chapterSearch" class="search-input" type="search" placeholder="Search: ข้อสอบเก่า, A09, 48, chest pain, tox..." autocomplete="off">
        <button id="clearSearch" class="clear-button" type="button">Clear</button>
      </div>
      <div class="filters" aria-label="Complete chapter categories">
        {" ".join(filter_buttons)}
      </div>
    </section>

    <section id="specialSection" class="section-block">
      <div class="section-head"><h2>ข้อสอบเก่า</h2><span id="specialResultCount" class="result-count">{len(special)} shown</span></div>
      <div id="specialList" class="chapter-list">{special_rows}
      </div>
    </section>

    <section id="chapterSection" class="section-block">
      <div class="section-head"><h2>Complete Chapters</h2><span id="chapterResultCount" class="result-count">{len(complete)} shown</span></div>
      <div id="chapterList" class="chapter-list">{complete_rows}
      </div>
    </section>

    <div id="emptyState" class="empty">No matching chapters or special sets.</div>
    <footer>Generated from local Special and Complete chapter HTML.</footer>
  </main>
  <script>
    const searchInput = document.getElementById('chapterSearch');
    const clearButton = document.getElementById('clearSearch');
    const filterButtons = Array.from(document.querySelectorAll('.filter-button'));
    const allRows = Array.from(document.querySelectorAll('.chapter-row'));
    const specialRows = Array.from(document.querySelectorAll('#specialList .chapter-row'));
    const chapterRows = Array.from(document.querySelectorAll('#chapterList .chapter-row'));
    const specialSection = document.getElementById('specialSection');
    const chapterSection = document.getElementById('chapterSection');
    const specialResultCount = document.getElementById('specialResultCount');
    const chapterResultCount = document.getElementById('chapterResultCount');
    const emptyState = document.getElementById('emptyState');
    const oldExamLabel = '{old_exam_label}';
    let activeFilter = 'All';

    function rowMatchesQuery(row, query) {{
      const chapter = row.dataset.chapter || '';
      const title = row.dataset.title || '';
      const category = (row.dataset.category || '').toLowerCase();
      return !query || chapter.includes(query) || title.includes(query) || category.includes(query);
    }}

    function updateList(rows, query, useCategoryFilter) {{
      let shown = 0;
      for (const row of rows) {{
        const category = row.dataset.category || '';
        const matchesFilter = !useCategoryFilter || activeFilter === 'All' || category === activeFilter;
        const isVisible = matchesFilter && rowMatchesQuery(row, query);
        row.hidden = !isVisible;
        if (isVisible) shown += 1;
      }}
      return shown;
    }}

    function applyFilters() {{
      const query = searchInput.value.trim().toLowerCase();
      const oldExamOnly = activeFilter === oldExamLabel;
      const showSpecialSection = activeFilter === 'All' || oldExamOnly;
      const shownSpecial = showSpecialSection ? updateList(specialRows, query, false) : 0;
      if (!showSpecialSection) {{
        specialRows.forEach((row) => {{ row.hidden = true; }});
      }}
      let shownChapter = 0;
      if (oldExamOnly) {{
        chapterRows.forEach((row) => {{ row.hidden = true; }});
      }} else {{
        shownChapter = updateList(chapterRows, query, true);
      }}
      specialResultCount.textContent = `${{shownSpecial}} shown`;
      chapterResultCount.textContent = `${{shownChapter}} shown`;
      specialSection.hidden = shownSpecial === 0;
      chapterSection.hidden = shownChapter === 0;
      emptyState.classList.toggle('is-visible', shownSpecial + shownChapter === 0);
    }}

    searchInput.addEventListener('input', applyFilters);
    clearButton.addEventListener('click', () => {{
      searchInput.value = '';
      searchInput.focus();
      applyFilters();
    }});
    filterButtons.forEach((button) => {{
      button.addEventListener('click', () => {{
        activeFilter = button.dataset.filter || 'All';
        filterButtons.forEach((item) => item.classList.toggle('is-active', item === button));
        applyFilters();
      }});
    }});
    applyFilters();
  </script>
</body>
</html>
"""
    (DOCS / "index.html").write_text(index, encoding="utf-8")


def build_publish_notes() -> None:
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    (DOCS / "README.md").write_text(
        """# ER Board Review Publish Build

This folder is the optimized GitHub Pages build for Special practice sets and Complete chapters.

- Open `index.html` for chapter links.
- Chapter pages live in `chapters/`.
- Referenced images were copied and converted to WebP in `assets/`.
- Images use lazy loading for better iPhone/iPad performance.

Regenerate after editing source chapters:

```powershell
python "..\\chapter_baseline\\build_github_pages.py"
```

If this `ER` folder is the GitHub repository root, set GitHub Pages to deploy from `main` branch, `/docs`.
""",
        encoding="utf-8",
    )


def main() -> int:
    if DOCS.exists() and os.environ.get("ER_PUBLISH_CLEAN") == "1":
        def handle_remove_error(function, path, _exc_info) -> None:
            os.chmod(path, stat.S_IWRITE)
            function(path)

        for attempt in range(10):
            try:
                shutil.rmtree(DOCS, onerror=handle_remove_error)
                break
            except OSError:
                if attempt == 9:
                    stale = ROOT / f"docs_stale_{int(time.time())}"
                    DOCS.rename(stale)
                    print(f"Renamed locked docs folder to {stale}")
                    break
                time.sleep(0.5)
    (DOCS / "assets").mkdir(parents=True, exist_ok=True)

    chapters = SPECIAL_CHAPTERS + complete_chapters()
    published_html_names = {Path(chapter["output"]).name for chapter in chapters}
    manifest: dict[str, dict[str, str]] = {}
    stats = {}
    for chapter in chapters:
        stats[chapter["id"]] = rewrite_html(chapter, manifest, published_html_names)

    build_index(chapters, manifest)
    build_publish_notes()
    (DOCS / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Wrote {DOCS}")
    for chapter_id, item in stats.items():
        print(f"{chapter_id}: {item}")
    print(f"docs_size_mb={dir_size(DOCS) / 1024 / 1024:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
