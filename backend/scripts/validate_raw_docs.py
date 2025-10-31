from pathlib import Path
import sys, re

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

required = ["#", "Source:", "Last-Accessed", "##Summary", "## Key Points", "## Disclaimers"]

bad = []
for md in RAW.glob("*.md"):
    txt = md.read_text(encoding="utf-8")
    missing = [k for k in required if k not in txt]
    if missing:
        bad.append((md.name, missing))

if bad:
    print("Some files are missing required sections:")
    for name, miss in bad:
        print(f" - {name}: missing {', '.join(miss)}")
    sys.exit(1)

print("All markdown files look OK.")