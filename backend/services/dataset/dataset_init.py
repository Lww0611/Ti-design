import os
from core import config # ✅ 修正导入
from services.dataset.dataset_service import save_uploaded_dataset
from db.session import SessionLocal
from db.db_models.dataset_table import Dataset

def init_system_datasets():
    print("🔄 Initializing system datasets...")
    target_dir = config.SYSTEM_DATASET_DIR
    if not target_dir.exists(): return

    db = SessionLocal()
    try:
        for filename in os.listdir(target_dir):
            if not filename.endswith(".csv"): continue
            exists = db.query(Dataset).filter(Dataset.filename == filename, Dataset.source_type == "system").first()
            if exists: continue

            print(f"📥 Importing: {filename}")
            class FakeUploadFile:
                def __init__(self, path):
                    self.filename = os.path.basename(path)
                    self.file = open(path, "rb")

            fake_file = FakeUploadFile(target_dir / filename)
            save_uploaded_dataset(db, fake_file, source_type="system")
            fake_file.file.close()
    finally:
        db.close()