# scripts/backup_db.py
from pathlib import Path
import shutil 
from datetime import datetime

DB = Path(__file__).resolve().parent.parent / "t1d.db"
BACKUPS = Path(__file__).resolve().parent.parent / "backups"

print(F"Looking for DB at: {DB}")
if not DB.exists():
    print("Database not found")
else:    
    BACKUPS.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = BACKUPS / f"t1d-{stamp}.db"
    shutil.copy2(DB, dest)
    print(f"Backup created at {dest}")