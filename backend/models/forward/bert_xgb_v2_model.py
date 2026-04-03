import json
from pathlib import Path

import numpy as np
import xgboost as xgb
from sentence_transformers import SentenceTransformer

from models.base import BaseModel


class BertXGBV2Model(BaseModel):
    """
    sentence-transformers 句向量（BERT 族） + 双 XGBoost（原生 save_model 加载）。
    权重目录:
      models/weights/bert_xgb_v2/
        encoder/          # SentenceTransformer.save
        strength_xgb.json
        elongation_xgb.json
        manifest.json
    """

    name = "BERT-XGB-v2"

    def __init__(self) -> None:
        base_dir = Path(__file__).resolve().parent.parent / "weights" / "bert_xgb_v2"

        self.encoder_dir = base_dir / "encoder"
        self.strength_path = base_dir / "strength_xgb.json"
        self.elongation_path = base_dir / "elongation_xgb.json"
        self.manifest_path = base_dir / "manifest.json"

        self.encoder: SentenceTransformer | None = None
        self.strength_booster: xgb.Booster | None = None
        self.elongation_booster: xgb.Booster | None = None
        self.numeric_columns: list[str] = []
        self._load()

    def _load(self) -> None:
        if not self.manifest_path.is_file():
            raise FileNotFoundError(
                f"BERT-XGB-v2 未就绪: 缺少 {self.manifest_path}，"
                "请先运行 scripts/train_bert_xgb_v2.py 生成权重。"
            )
        with open(self.manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
        self.numeric_columns = manifest["numeric_columns"]

        for p in (self.encoder_dir, self.strength_path, self.elongation_path):
            if not Path(p).exists():
                raise FileNotFoundError(f"BERT-XGB-v2 缺少文件或目录: {p}")

        print("🔄 Loading BERT-XGB-v2 (SentenceTransformer + XGBoost) …")
        self.encoder = SentenceTransformer(str(self.encoder_dir), trust_remote_code=True)

        self.strength_booster = xgb.Booster()
        self.strength_booster.load_model(str(self.strength_path))

        self.elongation_booster = xgb.Booster()
        self.elongation_booster.load_model(str(self.elongation_path))

        print("✅ BERT-XGB-v2 loaded.")

    def _feature_matrix(self, features: dict) -> np.ndarray:
        numeric_vector = np.array(
            [float(features.get(col, 0.0)) for col in self.numeric_columns],
            dtype=np.float32,
        ).reshape(1, -1)

        process_text = features.get("Process") or "as-received"
        embedding = self.encoder.encode(
            [str(process_text)],
            convert_to_numpy=True,
            normalize_embeddings=False,
        )
        embedding = np.asarray(embedding, dtype=np.float32)
        return np.hstack([numeric_vector, embedding])

    def predict(self, features: dict) -> dict:
        X = self._feature_matrix(features)
        dmat = xgb.DMatrix(X)

        strength = float(self.strength_booster.predict(dmat)[0])
        elongation = float(self.elongation_booster.predict(dmat)[0])
        elongation = max(0.0, elongation)

        return {
            "model": self.name,
            "strength": round(strength, 2),
            "elongation": round(elongation, 2),
            "raw": {
                "strength": round(strength, 2),
                "strength_err": None,
                "elongation": round(elongation, 2),
                "elongation_err": None,
            },
        }
