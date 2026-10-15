"""Lance l'interface interactive : python run_app.py (puis ouvrir http://localhost:8501)."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

if __name__ == "__main__":
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(ROOT / "app" / "dashboard.py"),
                    "--server.port", "8501"], cwd=ROOT, check=False)
