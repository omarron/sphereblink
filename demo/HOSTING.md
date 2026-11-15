# Hosting the static SphereBlink demo (no server needed)

`demo/` is a self-contained static site: `index.html` + `assets/` (GIFs, PNGs, JSON), ~4 MB, no JavaScript, no backend.
Open `demo/index.html` directly in a browser to preview it.

Nothing has been published. To publish (Omar does this from his own GitHub account):

**Option A — GitHub Pages (recommended)**
1. Create a public repo, e.g. `sphereblink`, and push this project folder (the `.gitignore` already excludes the 1.6 GB `cache/`).
2. Repo → Settings → Pages → "Deploy from a branch" → branch `main`, folder `/ (root)` — or move `demo/` contents to a `docs/` folder and choose `/docs`.
   If you keep `demo/`, the page URL is `https://<username>.github.io/sphereblink/demo/`.
3. Wait ~1 minute, open the URL in a private window, check the GIFs load.

**Option B — Netlify Drop / Cloudflare Pages**: drag the `demo/` folder onto https://app.netlify.com/drop (needs an account).

**Live app (optional)**: Streamlit Community Cloud → "New app" → pick the repo → main file `app.py`. First query for a new field takes a few minutes because cutouts (~4 MB each) are downloaded from IRSA.

Rebuild the page after re-running targets: `python3 sphereblink.py --all && python3 make_demo.py`.
