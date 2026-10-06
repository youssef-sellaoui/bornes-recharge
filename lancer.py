from pathlib import Path
DOSSIER = Path(__file__).parent
import subprocess, sys
subprocess.run([sys.executable, "telecharger.py"], check=True, cwd=DOSSIER)
subprocess.run([sys.executable, "charger.py"], check=True, cwd=DOSSIER)
subprocess.run([sys.executable, "analyser.py"], check=True, cwd=DOSSIER)