import sys
from pathlib import Path

# Set up paths for Streamlit Community Cloud
REPO_ROOT = Path(__file__).resolve().parent
PROJECT_DIR = REPO_ROOT / "PCCOE_Sarthak_PRN_CS1_AIML"
CODE_DIR = PROJECT_DIR / "Code"

if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

# Execute main application script
app_script = CODE_DIR / "app.py"
with open(app_script, "r", encoding="utf-8") as f:
    code = compile(f.read(), str(app_script), "exec")
    exec(code, globals())
