"""
Root entry point for Streamlit Cloud deployment.
Adds AllDone/ to sys.path so all imports resolve correctly,
then executes the actual app.
"""
import sys
import os
from pathlib import Path

# Make AllDone/ importable (tools, github_api, cache, latex, etc.)
alldone_dir = Path(__file__).parent / "AllDone"
sys.path.insert(0, str(alldone_dir))
os.chdir(alldone_dir)  # ensure relative paths (.env) resolve correctly

# Re-run the actual app from AllDone/
exec(open(alldone_dir / "app.py").read())
