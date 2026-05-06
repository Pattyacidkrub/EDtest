from __future__ import annotations

import hashlib
import html
import json
import os
import re
import shutil
import stat
import time
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
CHAPTER_DATA = ROOT / "chapter_data"
COMPLETE_DIR = ROOT / "_Handoff_20260506" / "Complete"
DOCS = ROOT / "docs"

SPECIAL_CHAPTERS = [
    {
        "id": "a09",
        "title": "A09 Infectious Study",
        "source": CHAPTER_DATA / "ChapterA09Special_InfectiousStudy.html",
        "output": "A09.html",
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
        "id": "a16",
        "title": "A16 Toxicology Study",
        "source": CHAPTER_DATA / "ChapterA16Special_ToxicologyStudy.html",
        "output": "A16.html",
        "group": "special",
    },
    {
        "id": "a17",
        "title": "A17 Trauma Study",
        "source": CHAPTER_DATA / "ChapterA17Special_TraumaStudy.html",
        "output": "A17.html",
        "group": "special",
    },
    {
        "id": "c",
        "title": "C EMS Study",
        "source": CHAPTER_DATA / "ChapterCSpecial_EMSStudy.html",
        "output": "C.html",
        "group": "special",
    },
]

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
            convert_image(resolved, dest)
            stats["converted_images"] += 1
        elif suffix in PASSTHROUGH_EXTENSIONS:
            dest = output_passthrough_path(resolved)
            copy_passthrough(resolved, dest)
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
    special = [chapter for chapter in chapters if chapter.get("group") == "special"]
    complete = [chapter for chapter in chapters if chapter.get("group") == "complete"]
    special_cards = build_cards(special, manifest, "Open practice set")
    complete_cards = build_cards(complete, manifest, "Open complete chapter")

    index = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
  <meta http-equiv="Pragma" content="no-cache">
  <meta http-equiv="Expires" content="0">
  <meta name="theme-color" content="#f7f3ea">
  <title>ER Board Review</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f7f3ea;
      --ink: #1e1d1a;
      --muted: #6d6760;
      --line: #ddd2c3;
      --accent: #9b2d1f;
      --card: #fffdfa;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--ink);
      line-height: 1.5;
    }}
    main {{
      width: min(920px, calc(100% - 32px));
      margin: 0 auto;
      padding: 48px 0;
    }}
    h1 {{ margin: 0 0 8px; font-size: clamp(2rem, 6vw, 4rem); letter-spacing: 0; }}
    p {{ color: var(--muted); margin: 0 0 28px; }}
    h2 {{ margin: 34px 0 14px; font-size: 1.1rem; color: var(--accent); letter-spacing: 0; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px; }}
    .chapter-card {{
      min-height: 150px;
      padding: 20px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--card);
      color: inherit;
      text-decoration: none;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      box-shadow: 0 1px 8px rgba(70, 50, 30, 0.08);
    }}
    .chapter-card:hover {{ border-color: var(--accent); }}
    .chapter-card__eyebrow {{ color: var(--accent); font-weight: 800; font-size: .82rem; }}
    footer {{ margin-top: 28px; font-size: .9rem; color: var(--muted); }}
  </style>
</head>
<body>
  <main>
    <h1>ER Board Review</h1>
    <p>Optimized mobile build for GitHub Pages. Images are converted to WebP and lazy-loaded for iPad/iPhone.</p>
    <h2>Special Practice Sets</h2>
    <div class="grid">
      {special_cards}
    </div>
    <h2>Complete Chapters</h2>
    <div class="grid">
      {complete_cards}
    </div>
    <footer>Generated from local Special and Complete chapter HTML.</footer>
  </main>
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
