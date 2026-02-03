import os
from sqlalchemy.orm import Session
from services.dataset_service import save_uploaded_dataset
from db.session import SessionLocal
from db.db_models.dataset_table import Dataset


SYSTEM_DATASET_DIR = "data/datasets/system"


def init_system_datasets():
    print("🔄 Initializing system datasets...")

    if not os.path.exists(SYSTEM_DATASET_DIR):
        print("⚠️ No system dataset directory found.")
        return

    db: Session = SessionLocal()

    try:
        for filename in os.listdir(SYSTEM_DATASET_DIR):
            if not filename.endswith(".csv"):
                continue

            file_path = os.path.join(SYSTEM_DATASET_DIR, filename)

            exists = db.query(Dataset).filter(
                Dataset.filename == filename,
                Dataset.source_type == "system"
            ).first()

            if exists:
                print(f"✅ {filename} already exists, skipped.")
                continue

            print(f"📥 Importing system dataset: {filename}")

            class FakeUploadFile:
                def __init__(self, path):
                    self.filename = os.path.basename(path)
                    self.file = open(path, "rb")

            fake_file = FakeUploadFile(file_path)
            save_uploaded_dataset(db, fake_file, source_type="system")
            fake_file.file.close()

        print("✅ System datasets initialization complete.")

    finally:
        db.close()
