# Archaeological Excavation & Trench Analysis Dashboard

A Python application for managing archaeological excavation projects, trenches, and artifact analysis records. It uses SQLite for persistent storage and provides a Tkinter desktop interface plus an ipywidgets interface for Jupyter/Google Colab.

## Features

- Create and manage excavation projects
- Record trenches and opening dates
- Store artifact analysis types and measured values
- View individual tables and a joined excavation report
- Delete projects, trenches, or analyses
- SQLite foreign-key integrity with cascading deletes
- Seed example records when the database is empty

## Requirements

- Python 3.9 or newer
- SQLite (included with Python)
- Tkinter for the desktop interface (usually included with Python)
- `ipywidgets` for the notebook interface

## Run locally

```bash
python archaeological_dashboard.py
```

The app creates `archaeological_excavation.db` in the same folder on first run.

## Run in Jupyter / Google Colab

Install the optional notebook dependency:

```bash
pip install -r requirements.txt
```

Then run the Python file in your notebook environment. The app detects an active Jupyter/Colab-style shell and displays notebook controls when `ipywidgets` is available.

## Database schema

| Table | Purpose |
|---|---|
| `excavation_projects` | Project name and contact email |
| `trenches` | Trenches linked to an excavation project |
| `artifact_analyses` | Analysis type and measured value linked to a trench |

Foreign keys are enabled for each connection. Deleting a project cascades to its trenches and analyses; deleting a trench cascades to its analyses.

## Files

- `archaeological_dashboard.py` — application source code
- `requirements.txt` — optional notebook dependency
- `.gitignore` — excludes generated databases and Python cache files

The SQLite database is generated locally and intentionally excluded from version control. Sample records are inserted only when the database has no projects.
