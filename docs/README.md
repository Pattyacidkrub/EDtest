# ER Board Review Publish Build

This folder is the optimized GitHub Pages build for A09/A14.

- Open `index.html` for chapter links.
- Chapter pages live in `chapters/`.
- Referenced images were copied and converted to WebP in `assets/`.
- Images use lazy loading for better iPhone/iPad performance.

Regenerate after editing source chapters:

```powershell
python "..\chapter_baseline\build_github_pages.py"
```

If this `ER` folder is the GitHub repository root, set GitHub Pages to deploy from `main` branch, `/docs`.
