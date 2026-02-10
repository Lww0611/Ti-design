import json
from pathlib import Path


def save_model_bundle(
    model_file,
    metadata: dict,
    model_id: int,
    base_dir: Path,
):
    model_dir = base_dir / f"model_{model_id}"
    model_dir.mkdir(parents=True, exist_ok=True)

    model_path = model_dir / "model.pkl"
    with open(model_path, "wb") as f:
        f.write(model_file)

    metadata_path = model_dir / "metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    return model_path, metadata_path
