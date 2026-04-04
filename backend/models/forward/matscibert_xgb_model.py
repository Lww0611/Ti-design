"""
MatSciBERT 句向量（HuggingFace Transformers）+ 双 XGBoost（强度 / 延伸率）。

权重目录（由 scripts/train_matscibert_xgb.py 生成）:
  models/weights/matscibert_xgb/
    encoder/              # tokenizer + model save_pretrained
    strength_xgb.json
    elongation_xgb.json
    manifest.json
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import torch
import xgboost as xgb
from transformers import AutoModel, AutoTokenizer

from models.base import BaseModel


def _mean_pool(last_hidden: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
    mask = attention_mask.unsqueeze(-1).expand(last_hidden.size()).float()
    summed = torch.sum(last_hidden * mask, dim=1)
    denom = torch.clamp(mask.sum(dim=1), min=1e-9)
    return summed / denom


class MatSciBERTXGBModel(BaseModel):
    name = "MatSciBERT-XGB"

    def __init__(self) -> None:
        base_dir = Path(__file__).resolve().parent.parent / "weights" / "matscibert_xgb"

        self.encoder_dir = base_dir / "encoder"
        self.strength_path = base_dir / "strength_xgb.json"
        self.elongation_path = base_dir / "elongation_xgb.json"
        self.manifest_path = base_dir / "manifest.json"

        self.tokenizer: AutoTokenizer | None = None
        self.encoder: AutoModel | None = None
        self.strength_booster: xgb.Booster | None = None
        self.elongation_booster: xgb.Booster | None = None
        self.numeric_columns: list[str] = []
        self.max_length: int = 256
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._load()

    def _load(self) -> None:
        if not self.manifest_path.is_file():
            raise FileNotFoundError(
                f"MatSciBERT-XGB 未就绪: 缺少 {self.manifest_path}，"
                "请先运行 scripts/train_matscibert_xgb.py 生成权重。"
            )
        with open(self.manifest_path, encoding="utf-8") as f:
            manifest = json.load(f)
        self.numeric_columns = manifest["numeric_columns"]
        self.max_length = int(manifest.get("max_length", 256))

        for p in (self.encoder_dir, self.strength_path, self.elongation_path):
            if not Path(p).exists():
                raise FileNotFoundError(f"MatSciBERT-XGB 缺少文件或目录: {p}")

        print("🔄 Loading MatSciBERT-XGB (Transformers + XGBoost) …")
        self.tokenizer = AutoTokenizer.from_pretrained(str(self.encoder_dir))
        self.encoder = AutoModel.from_pretrained(str(self.encoder_dir))
        self.encoder.to(self.device)
        self.encoder.eval()

        self.strength_booster = xgb.Booster()
        self.strength_booster.load_model(str(self.strength_path))

        self.elongation_booster = xgb.Booster()
        self.elongation_booster.load_model(str(self.elongation_path))

        print("✅ MatSciBERT-XGB loaded.")

    def _encode_text(self, text: str) -> np.ndarray:
        assert self.tokenizer is not None and self.encoder is not None
        t = str(text) if text else "as-received"
        enc = self.tokenizer(
            [t],
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
        )
        enc = {k: v.to(self.device) for k, v in enc.items()}
        with torch.no_grad():
            out = self.encoder(**enc)
            pooled = _mean_pool(out.last_hidden_state, enc["attention_mask"])
        return pooled.cpu().numpy().astype(np.float32)

    def _feature_matrix(self, features: dict) -> np.ndarray:
        numeric_vector = np.array(
            [float(features.get(col, 0.0)) for col in self.numeric_columns],
            dtype=np.float32,
        ).reshape(1, -1)

        process_text = features.get("Process") or "as-received"
        embedding = self._encode_text(str(process_text))
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
