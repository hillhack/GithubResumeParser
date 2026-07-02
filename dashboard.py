"""
Root entry point for Streamlit Cloud.
Streamlit Cloud is configured to run 'dashboard.py' — this file
adds AllDone/ to sys.path and executes the actual app.
"""
import sys
import os
from pathlib import Path

# Make AllDone/ importable (tools, github_api, cache, latex, etc.)
alldone_dir = Path(__file__).parent / "AllDone"
sys.path.insert(0, str(alldone_dir))
os.chdir(alldone_dir)  # ensure .env and relative paths resolve correctly

exec(open(alldone_dir / "app.py").read())
