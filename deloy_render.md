# Render deployment guide for this Dash app

This project is a **Dash + Python** web app, not Streamlit.

The uploaded project structure already matches a normal Render Python web service:

- `app.py` is at the repo root
- `requirements.txt` is at the repo root
- the Dash WSGI entrypoint is `app:server`
- the Excel file is loaded from `data/lpg_stock_data.xlsx`

## Files to add to your repo root

Add these files at the same level as:

- `app.py`
- `requirements.txt`
- `components.py`
- `data/`

Files to add:

- `render.yaml`
- `deloy_render.md`

## Recommended `render.yaml`

Use the provided `render.yaml` file as-is.

It does the following:

- creates a **Python web service**
- installs dependencies from `requirements.txt`
- starts Dash with Gunicorn using `app:server`
- binds to `0.0.0.0:$PORT`
- pins Python to `3.11.11`
- enables auto deploy on every commit

## Why this config works for your app

Your `app.py` contains:

```python
server = app.server
```

So the correct production start target is:

```bash
gunicorn app:server
```

Your app also reads the workbook from:

```python
DATA_FILE_PATH = Path("data/lpg_stock_data.xlsx")
```

So the `data` folder and Excel file must be committed to the repository.

## Deployment steps on Render

### Option 1: Deploy using Blueprint (recommended for `render.yaml`)

1. Push your code to GitHub/GitLab/Bitbucket.
2. Make sure `render.yaml` is in the repo root.
3. Open **Render Dashboard**.
4. Click **New > Blueprint**.
5. Connect the repository.
6. Select the branch.
7. Keep the Blueprint path as `render.yaml`.
8. Click **Deploy Blueprint**.

## After deployment

Render will:

1. create a Python web service
2. run:

```bash
pip install -r requirements.txt
```

3. start the app with:

```bash
sh -c 'gunicorn app:server --bind 0.0.0.0:${PORT:-10000}'
```

If everything is correct, your Dash app should open on the generated `onrender.com` URL.

## Important checks before pushing

Make sure all of these are present in the repo:

- `app.py`
- `requirements.txt`
- `aggregations.py`
- `components.py`
- `config.py`
- `data_loader.py`
- `logger.py`
- `stock_logic.py`
- `assets/styles.css`
- `data/lpg_stock_data.xlsx`
- `render.yaml`

## Common issues and fixes

### 1. `FileNotFoundError: data/lpg_stock_data.xlsx`
Cause:
- the Excel file was not committed
- the folder name or file name differs by case

Fix:
- confirm `data/lpg_stock_data.xlsx` exists in the repo exactly with the same spelling

### 2. `ModuleNotFoundError`
Cause:
- missing package in `requirements.txt`

Fix:
- confirm these are present:

```txt
dash>=2.18.0
pandas>=2.2.0
numpy>=1.26.0
openpyxl>=3.1.0
plotly>=5.24.0
gunicorn>=21.2.0
```

### 3. No open port detected
Cause:
- app not binding properly for Render

Fix:
- keep the provided start command exactly as-is

```bash
sh -c 'gunicorn app:server --bind 0.0.0.0:${PORT:-10000}'
```

### 4. Build works locally but fails on Render
Cause:
- Linux is case-sensitive

Fix:
- check file and folder names carefully
- verify import names match file names exactly

## Local test command

To test production-style startup locally:

```bash
pip install -r requirements.txt
set PORT=10000
python -m gunicorn app:server --bind 0.0.0.0:%PORT%
```

For PowerShell:

```powershell
$env:PORT = "10000"
python -m gunicorn app:server --bind 0.0.0.0:$env:PORT
```

## Final note

This app should be deployed as a **Render Web Service**, not as a static site and not as Streamlit.
