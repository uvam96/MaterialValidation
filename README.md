# FG Description Validator — Deployment Guide

Batch-checks proposed Finished Goods descriptions against Bondville's SAP
material creation standard before they're submitted to SAP.

## Files
- `fg_description_validator.py` — the app
- `requirements.txt` — dependencies Streamlit Cloud installs automatically
- `sample_fg_list.csv` — example input to test with

## Deploy to Streamlit Community Cloud (free, public URL)

**1. Create a GitHub repo**
- Go to github.com → New repository (e.g. `fg-description-validator`)
- Can be public or private — Streamlit Cloud works with both once connected

**2. Upload the files**
- On the repo page, "Add file" → "Upload files"
- Upload `fg_description_validator.py`, `requirements.txt`, and (optionally)
  `sample_fg_list.csv`
- Commit directly to the `main` branch

**3. Deploy on Streamlit Cloud**
- Go to [share.streamlit.io](https://share.streamlit.io) and sign in with
  your GitHub account
- Click "Create app" → "Deploy a public app from GitHub"
- Pick the repo, branch (`main`), and main file path
  (`fg_description_validator.py`)
- Click "Deploy"

Streamlit Cloud installs everything from `requirements.txt` automatically and
gives you a URL like `https://fg-description-validator.streamlit.app` — share
that with anyone who needs to check descriptions before creating FGs in SAP.

**4. Updating later**
- Any time you push a new commit to the repo (e.g. edit the file on GitHub
  directly, or push from your machine), the deployed app redeploys itself
  automatically within a minute or two — no redeployment steps needed.

## Notes
- The app has no login/auth by default — anyone with the URL can use it. If
  that's a concern, Streamlit Cloud's paid tiers support viewer restrictions,
  or you can add a simple password gate in the app itself (ask me if you want
  that added).
- If you later want the duplicate check to run against the real SAP material
  master instead of just within each uploaded batch, that's a small addition
  — either point it at a refreshed export or the SAP ByD OData feed.
