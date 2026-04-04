"""
在固定随机划分下评估已训练的 MatSciBERT-XGB（与训练脚本相同 split 可对照 val R²）。

用法:
  cd backend && python scripts/evaluate_matscibert_xgb.py \\
    --data_path data/datasets/system/newdata3.csv \\
    --weights_dir models/weights/matscibert_xgb \\
    --test_size 0.2 --seed 42
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import torch
import xgboost as xgb
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split
from transformers import AutoModel, AutoTokenizer

PROCESS_COL = "Process"
STRENGTH_COL = "Strength (MPa)"
ELONGATION_COL = "Elongation (%)"


def _mean_pool(last_hidden: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
    mask = attention_mask.unsqueeze(-1).expand(last_hidden.size()).float()
    summed = torch.sum(last_hidden * mask, dim=1)
    denom = torch.clamp(mask.sum(dim=1), min=1e-9)
    return summed / denom


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--data_path", type=str, default="data/datasets/system/newdata3.csv")
    p.add_argument("--weights_dir", type=str, default="models/weights/matscibert_xgb")
    p.add_argument("--test_size", type=float, default=0.2)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--encode_batch_size", type=int, default=8)
    args = p.parse_args()

    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    wdir = root / args.weights_dir
    manifest_path = wdir / "manifest.json"
    if not manifest_path.is_file():
        raise SystemExit(f"缺少 {manifest_path}，请先训练模型。")

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    numeric_columns = manifest["numeric_columns"]
    max_length = int(manifest.get("max_length", 256))

    df = pd.read_csv(root / args.data_path)
    df = df.dropna(subset=[PROCESS_COL, STRENGTH_COL, ELONGATION_COL]).copy()
    df[PROCESS_COL] = df[PROCESS_COL].astype(str).str.strip()
    df = df[df[PROCESS_COL].str.len() > 0]

    y_s = df[STRENGTH_COL].astype(np.float32).to_numpy()
    y_e = np.maximum(df[ELONGATION_COL].astype(np.float32).to_numpy(), 0.0)
    X_num = df[numeric_columns].astype(np.float32).to_numpy()

    encoder_dir = wdir / "encoder"
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(str(encoder_dir))
    model = AutoModel.from_pretrained(str(encoder_dir)).to(device)
    model.eval()

    texts = df[PROCESS_COL].tolist()
    chunks: list[np.ndarray] = []
    with torch.no_grad():
        for start in range(0, len(texts), args.encode_batch_size):
            batch = texts[start : start + args.encode_batch_size]
            enc = tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=max_length,
                return_tensors="pt",
            )
            enc = {k: v.to(device) for k, v in enc.items()}
            out = model(**enc)
            pooled = _mean_pool(out.last_hidden_state, enc["attention_mask"])
            chunks.append(pooled.cpu().numpy().astype(np.float32))
    emb = np.vstack(chunks)
    X_full = np.hstack([X_num, emb])

    X_train, X_val, y_train_s, y_val_s, y_train_e, y_val_e = train_test_split(
        X_full,
        y_s,
        y_e,
        test_size=args.test_size,
        random_state=args.seed,
    )

    bs = xgb.Booster()
    bs.load_model(str(wdir / "strength_xgb.json"))
    be = xgb.Booster()
    be.load_model(str(wdir / "elongation_xgb.json"))

    def pred(booster: xgb.Booster, X: np.ndarray) -> np.ndarray:
        return booster.predict(xgb.DMatrix(X.astype(np.float32)))

    res = {
        "strength": {
            "train_r2": float(r2_score(y_train_s, pred(bs, X_train))),
            "val_r2": float(r2_score(y_val_s, pred(bs, X_val))),
        },
        "elongation": {
            "train_r2": float(r2_score(y_train_e, pred(be, X_train))),
            "val_r2": float(r2_score(y_val_e, pred(be, X_val))),
        },
        "n_total": len(df),
        "n_train": len(X_train),
        "n_val": len(X_val),
        "test_size": args.test_size,
        "seed": args.seed,
    }

    print(json.dumps(res, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
