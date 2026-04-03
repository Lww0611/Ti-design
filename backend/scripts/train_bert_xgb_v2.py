"""
训练 BERT 句向量 + 双 XGBoost（强度 / 延伸率），产物供 BertXGBV2Model 加载。

示例:
  cd backend && python scripts/train_bert_xgb_v2.py \\
    --data_path data/datasets/system/newdata3.csv \\
    --output_dir models/weights/bert_xgb_v2 \\
    --sentence_model all-MiniLM-L6-v2 \\
    --finetune_epochs 2

句向量：默认用 sentence-transformers（基于 BERT 族微调模型）。
可选 --finetune_epochs：在小数据上做短期监督微调（MSE 回归头），再保存 encoder。

XGBoost 使用原生 save_model，避免 pickle 跨版本推理异常。
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
from sentence_transformers import SentenceTransformer
from sklearn.metrics import r2_score
from sklearn.model_selection import train_test_split


NUMERIC_COLUMNS = [
    "Ti (wt%)", "Mo (wt%)", "Al (wt%)", "Sn (wt%)", "V (wt%)",
    "Zr (wt%)", "Cr (wt%)", "Nb (wt%)", "Ta (wt%)", "Fe (wt%)",
    "W (wt%)", "Si (wt%)", "O (wt%)", "C (wt%)", "N (wt%)",
    "H (wt%)", "Ni (wt%)", "Cu (wt%)", "B (wt%)", "Mn (wt%)",
    "Y (wt%)", "Zn (wt%)", "transition temperature (°C)",
]

STRENGTH_COL = "Strength (MPa)"
ELONGATION_COL = "Elongation (%)"
PROCESS_COL = "Process"


def _numeric_matrix(df: pd.DataFrame) -> np.ndarray:
    missing = [c for c in NUMERIC_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"CSV 缺少列: {missing}")
    return df[NUMERIC_COLUMNS].astype(np.float32).to_numpy()


def _finetune_encoder(
    model: SentenceTransformer,
    texts: list[str],
    y_strength: np.ndarray,
    y_elong: np.ndarray,
    epochs: int,
    batch_size: int,
    lr: float,
    device: torch.device,
) -> SentenceTransformer:
    model = model.to(device)
    model.train()
    dim = model.get_sentence_embedding_dimension()
    head = torch.nn.Linear(dim, 2).to(device)
    opt = torch.optim.AdamW(
        list(model.parameters()) + list(head.parameters()),
        lr=lr,
        weight_decay=1e-4,
    )
    y = torch.tensor(np.stack([y_strength, y_elong], axis=1), dtype=torch.float32)
    n = len(texts)
    for _ in range(epochs):
        perm = torch.randperm(n)
        for start in range(0, n, batch_size):
            idx = perm[start : start + batch_size].tolist()
            batch_texts = [texts[i] for i in idx]
            feats = model.tokenize(batch_texts)
            feats = {k: v.to(device) for k, v in feats.items()}
            out = model(feats)
            emb = out["sentence_embedding"]
            pred = head(emb)
            target = y[idx].to(device)
            loss = torch.nn.functional.mse_loss(pred, target)
            opt.zero_grad()
            loss.backward()
            opt.step()
    model.eval()
    return model


def train(args: argparse.Namespace) -> None:
    out_dir = Path(args.output_dir)
    encoder_dir = out_dir / "encoder"
    out_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.data_path)
    for c in (PROCESS_COL, STRENGTH_COL, ELONGATION_COL):
        if c not in df.columns:
            raise ValueError(f"CSV 缺少列: {c}")

    df = df.dropna(subset=[PROCESS_COL, STRENGTH_COL, ELONGATION_COL]).copy()
    df[PROCESS_COL] = df[PROCESS_COL].astype(str).str.strip()
    df = df[df[PROCESS_COL].str.len() > 0]

    y_s = df[STRENGTH_COL].astype(np.float32).to_numpy()
    y_e = df[ELONGATION_COL].astype(np.float32).to_numpy()
    y_e = np.maximum(y_e, 0.0)

    texts = df[PROCESS_COL].tolist()
    X_num = _numeric_matrix(df)

    device = torch.device("cuda" if torch.cuda.is_available() and not args.cpu else "cpu")

    print(f"Loading sentence model: {args.sentence_model} …")
    st_model = SentenceTransformer(args.sentence_model, trust_remote_code=True)

    if args.finetune_epochs > 0:
        print(
            f"Fine-tuning encoder for {args.finetune_epochs} epochs "
            f"(device={device}, batch={args.finetune_batch}) …"
        )
        st_model = _finetune_encoder(
            st_model,
            texts,
            y_s,
            y_e,
            epochs=args.finetune_epochs,
            batch_size=args.finetune_batch,
            lr=args.finetune_lr,
            device=device,
        )

    print("Encoding Process texts …")
    emb = st_model.encode(
        texts,
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

    common_params = {
        "objective": "reg:squarederror",
        "eval_metric": "rmse",
        "max_depth": args.max_depth,
        "eta": args.eta,
        "subsample": args.subsample,
        "colsample_bytree": args.colsample_bytree,
        "seed": args.seed,
    }

    def _predict_dmatrix(bst: xgb.Booster, X: np.ndarray) -> np.ndarray:
        return bst.predict(xgb.DMatrix(X.astype(np.float32)))

    def train_one(y_tr, y_va, fname: str) -> xgb.Booster:
        dtr = xgb.DMatrix(X_train, label=y_tr)
        dva = xgb.DMatrix(X_val, label=y_va)
        bst = xgb.train(
            common_params,
            dtr,
            num_boost_round=args.n_rounds,
            evals=[(dtr, "train"), (dva, "val")],
            early_stopping_rounds=args.early_stopping,
            verbose_eval=50,
        )
        path = out_dir / fname
        bst.save_model(str(path))
        print(f"Saved {path}")
        return bst

    bst_s = train_one(y_train_s, y_val_s, "strength_xgb.json")
    bst_e = train_one(y_train_e, y_val_e, "elongation_xgb.json")

    metrics = {
        "strength": {
            "train_r2": float(r2_score(y_train_s, _predict_dmatrix(bst_s, X_train))),
            "val_r2": float(r2_score(y_val_s, _predict_dmatrix(bst_s, X_val))),
        },
        "elongation": {
            "train_r2": float(r2_score(y_train_e, _predict_dmatrix(bst_e, X_train))),
            "val_r2": float(r2_score(y_val_e, _predict_dmatrix(bst_e, X_val))),
        },
    }
    print("Metrics (holdout val, same split as early stopping):")
    print(f"  Strength   train R²={metrics['strength']['train_r2']:.4f}  val R²={metrics['strength']['val_r2']:.4f}")
    print(f"  Elongation train R²={metrics['elongation']['train_r2']:.4f}  val R²={metrics['elongation']['val_r2']:.4f}")

    st_model.save(str(encoder_dir))
    print(f"Saved encoder to {encoder_dir}")

    manifest = {
        "version": 1,
        "sentence_model_start": args.sentence_model,
        "numeric_columns": NUMERIC_COLUMNS,
        "embedding_dim": int(emb.shape[1]),
        "feature_dim": int(X_full.shape[1]),
        "process_column": PROCESS_COL,
        "strength_column": STRENGTH_COL,
        "elongation_column": ELONGATION_COL,
        "n_samples": int(len(df)),
        "finetune_epochs": args.finetune_epochs,
        "xgb": {
            "n_rounds": args.n_rounds,
            "early_stopping": args.early_stopping,
            "params": common_params,
        },
        "metrics": metrics,
        "split": {"test_size": args.test_size, "random_state": args.seed},
    }
    with open(out_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"Wrote {out_dir / 'manifest.json'}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--data_path", type=str, default="data/datasets/system/newdata3.csv")
    p.add_argument("--output_dir", type=str, default="models/weights/bert_xgb_v2")
    p.add_argument(
        "--sentence_model",
        type=str,
        default="all-MiniLM-L6-v2",
        help="sentence-transformers 模型 id（BERT 系句向量，如 all-MiniLM-L6-v2）",
    )
    p.add_argument("--test_size", type=float, default=0.2)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--encode_batch_size", type=int, default=32)
    p.add_argument("--finetune_epochs", type=int, default=0)
    p.add_argument("--finetune_batch", type=int, default=16)
    p.add_argument("--finetune_lr", type=float, default=2e-5)
    p.add_argument("--cpu", action="store_true", help="强制 CPU（含微调）")
    p.add_argument("--n_rounds", type=int, default=800)
    p.add_argument("--early_stopping", type=int, default=80)
    p.add_argument("--max_depth", type=int, default=6)
    p.add_argument("--eta", type=float, default=0.05)
    p.add_argument("--subsample", type=float, default=0.9)
    p.add_argument("--colsample_bytree", type=float, default=0.9)
    args = p.parse_args()

    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    # 将 HF 缓存放到项目内，避免部分环境无法写 ~/.cache
    hub_cache = root / ".hf_hub_cache"
    hub_cache.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HF_HOME", str(hub_cache))
    os.environ.setdefault("HF_HUB_CACHE", str(hub_cache))
    os.environ.setdefault("TRANSFORMERS_CACHE", str(hub_cache))
    train(args)


if __name__ == "__main__":
    main()
