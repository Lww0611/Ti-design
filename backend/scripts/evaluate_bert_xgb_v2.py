"""
在固定随机划分下评估已训练的 BERT-XGB-v2（与训练脚本相同的 train_test_split 设定即可复现 val R²）。

用法:
  cd backend && python scripts/evaluate_bert_xgb_v2.py \\
    --data_path data/datasets/system/newdata3.csv \\
    --weights_dir models/weights/bert_xgb_v2 \\
    --test_size 0.2 --seed 42
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb
from sentence_transformers import SentenceTransformer
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split

PROCESS_COL = "Process"
STRENGTH_COL = "Strength (MPa)"
ELONGATION_COL = "Elongation (%)"


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--data_path", type=str, default="data/datasets/system/newdata3.csv")
    p.add_argument("--weights_dir", type=str, default="models/weights/bert_xgb_v2")
    p.add_argument("--test_size", type=float, default=0.2)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--encode_batch_size", type=int, default=64)
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

    df = pd.read_csv(root / args.data_path)
    df = df.dropna(subset=[PROCESS_COL, STRENGTH_COL, ELONGATION_COL]).copy()
    df[PROCESS_COL] = df[PROCESS_COL].astype(str).str.strip()
    df = df[df[PROCESS_COL].str.len() > 0]

    y_s = df[STRENGTH_COL].astype(np.float32).to_numpy()
    y_e = np.maximum(df[ELONGATION_COL].astype(np.float32).to_numpy(), 0.0)
    X_num = df[numeric_columns].astype(np.float32).to_numpy()

    encoder_dir = wdir / "encoder"
    st = SentenceTransformer(str(encoder_dir), trust_remote_code=True)
    emb = st.encode(
        df[PROCESS_COL].tolist(),
        batch_size=args.encode_batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=False,
    )
    emb = np.asarray(emb, dtype=np.float32)
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
