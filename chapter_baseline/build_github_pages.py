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
DOCS = ROOT / "docs"

CHAPTERS = [
    {
        "id": "a09",
        "title": "A09 Infectious Study",
        "source": CHAPTER_DATA / "ChapterA09Special_InfectiousStudy.html",
        "output": "A09.html",
    },
    {
        "id": "a14",
        "title": "A14 Renal / Urogenital Study",
        "source": CHAPTER_DATA / "ChapterA14Special_RenalUrogenitalStudy.html",
        "output": "A14.html",
    },
    {
        "id": "a16",
        "title": "A16 Toxicology Study",
        "source": CHAPTER_DATA / "ChapterA16Special_ToxicologyStudy.html",
        "output": "A16.html",
    },
    {
        "id": "c",
        "title": "C EMS Study",
        "source": CHAPTER_DATA / "ChapterCSpecial_EMSStudy.html",
        "output": "C.html",
    },
]

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
PASSTHROUGH_EXTENSIONS = {".css", ".js", ".svg", ".gif", ".ico", ".pdf"}
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

        if image.mode == "RGBA":
            # WebP supports alpha; quality keeps highlighted textbook crops readable.
            image.save(dest, "WEBP", quality=86, method=6)
        else:
            image.save(dest, "WEBP", quality=84, method=6)


def copy_passthrough(source: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists() or dest.stat().st_mtime < source.stat().st_mtime:
        shutil.copy2(source, dest)


def rewrite_html(chapter: dict[str, str], manifest: dict[str, dict[str, str]]) -> dict[str, int | str]:
    html_path = Path(chapter["source"])
    chapter_id = chapter["id"]
    output_name = chapter["output"]
    text = html_path.read_text(encoding="utf-8")
    collector = AttrCollector()
    collector.feed(text)

    ref_map: dict[str, str] = {}
    stats = {"local_refs": 0, "converted_images": 0, "copied_assets": 0, "missing": 0}

    for _attr, ref in collector.refs:
        if ref in ref_map or is_remote(ref):
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
        ref_map[ref] = "../" + dest.relative_to(DOCS).as_posix()

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

    out = DOCS / "chapters" / output_name
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")

    manifest[chapter_id] = {
        "title": chapter["title"],
        "html": f"chapters/{output_name}",
        "source": str(html_path.relative_to(ROOT)),
        "local_refs": str(stats["local_refs"]),
        "converted_images": str(stats["converted_images"]),
        "copied_assets": str(stats["copied_assets"]),
        "missing": str(stats["missing"]),
    }
    return stats | {"output": str(out)}


def dir_size(path: Path) -> int:
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def build_index(manifest: dict[str, dict[str, str]]) -> None:
    cards = []
    for chapter in CHAPTERS:
        chapter_id = chapter["id"]
        item = manifest[chapter_id]
        cards.append(
            f"""
            <a class="chapter-card" href="{html.escape(item['html'])}">
              <span class="chapter-card__eyebrow">{chapter_id.upper()}</span>
              <strong>{html.escape(item['title'])}</strong>
              <span>Open practice chapter</span>
            </a>
            """
        )

    index = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
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
    <div class="grid">
      {''.join(cards)}
    </div>
    <footer>Generated from local Special chapter HTML.</footer>
  </main>
</body>
</html>
"""
    (DOCS / "index.html").write_text(index, encoding="utf-8")


def build_publish_notes() -> None:
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    (DOCS / "README.md").write_text(
        """# ER Board Review Publish Build

This folder is the optimized GitHub Pages build for Special practice chapters.

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
    if DOCS.exists():
        def handle_remove_error(function, path, _exc_info) -> None:
            os.chmod(path, stat.S_IWRITE)
            function(path)

        for attempt in range(5):
            try:
                shutil.rmtree(DOCS, onerror=handle_remove_error)
                break
            except PermissionError:
                if attempt == 4:
                    raise
                time.sleep(0.5)
    (DOCS / "assets").mkdir(parents=True, exist_ok=True)

    manifest: dict[str, dict[str, str]] = {}
    stats = {}
    for chapter in CHAPTERS:
        stats[chapter["id"]] = rewrite_html(chapter, manifest)

    build_index(manifest)
    build_publish_notes()
    (DOCS / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Wrote {DOCS}")
    for chapter_id, item in stats.items():
        print(f"{chapter_id}: {item}")
    print(f"docs_size_mb={dir_size(DOCS) / 1024 / 1024:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
