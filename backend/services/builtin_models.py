"""
将平台内置、权重在磁盘上的模型登记到 model 表（供模型管理页展示与元数据一致）。
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from db.session import SessionLocal
from db.db_models.model import Model
from db.db_models.user_table import User

_BACKEND_ROOT = Path(__file__).resolve().parents[1]


def _upsert_builtin(
    db,
    user: User,
    *,
    model_name: str,
    manifest_path: Path,
    model_file_path: str,
    description: str,
) -> None:
    if not manifest_path.is_file():
        return
    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)
    features = list(manifest.get("numeric_columns", [])) + ["Process"]
    metrics = manifest.get("metrics")

    existing = (
        db.query(Model)
        .filter(Model.user_id == user.id, Model.model_name == model_name)
        .first()
    )
    if existing:
        if metrics is not None:
            existing.metrics = metrics
            existing.model_file_path = model_file_path
            db.commit()
        return

    rec = Model(
        user_id=user.id,
        model_name=model_name,
        content=None,
        model_file_path=model_file_path,
        features=features,
        target="Strength (MPa); Elongation (%)",
        task_type="regression",
        description=description,
        status="builtin",
        metrics=metrics,
        created_at=datetime.utcnow(),
    )
    db.add(rec)
    db.commit()
    print(f"✅ 已登记内置模型 {model_name} (model.id={rec.id})")


def init_builtin_models() -> None:
    bert_manifest = _BACKEND_ROOT / "models" / "weights" / "bert_xgb_v2" / "manifest.json"
    bert_v3_manifest = _BACKEND_ROOT / "models" / "weights" / "bert_v3" / "manifest.json"
    ms_manifest = _BACKEND_ROOT / "models" / "weights" / "matscibert_xgb" / "manifest.json"

    if not bert_manifest.is_file():
        print("⚠ 跳过 BERT-XGB-v2 登记: 未找到 bert_xgb_v2/manifest.json")

    db = SessionLocal()
    try:
        user = db.query(User).order_by(User.id).first()
        if not user:
            print("⚠ 跳过内置模型登记: 数据库中无用户，请先注册账号")
            return

        if bert_manifest.is_file():
            _upsert_builtin(
                db,
                user,
                model_name="BERT-XGB-v2",
                manifest_path=bert_manifest,
                model_file_path="models/weights/bert_xgb_v2",
                description=(
                    "内置：sentence-transformers 句向量 + 双 XGBoost（强度/延伸率），"
                    "权重见 models/weights/bert_xgb_v2/。"
                ),
            )

        if bert_v3_manifest.is_file():
            _upsert_builtin(
                db,
                user,
                model_name="BERT-v3",
                manifest_path=bert_v3_manifest,
                model_file_path="models/weights/bert_v3",
                description=(
                    "内置：Bert-v3 训练产物（XGBoost + RandomForest 融合推理），"
                    "权重见 models/weights/bert_v3/。"
                ),
            )
        else:
            print("ℹ 未检测到 bert_v3/manifest.json，跳过 BERT-v3 登记。")

        if ms_manifest.is_file():
            _upsert_builtin(
                db,
                user,
                model_name="MatSciBERT-XGB",
                manifest_path=ms_manifest,
                model_file_path="models/weights/matscibert_xgb",
                description=(
                    "内置：MatSciBERT（HuggingFace）工艺文本嵌入 + 双 XGBoost（强度/延伸率），"
                    "权重见 models/weights/matscibert_xgb/；训练见 scripts/train_matscibert_xgb.py。"
                ),
            )
        else:
            print("ℹ 未检测到 matscibert_xgb/manifest.json，跳过 MatSciBERT-XGB 登记（训练后重启即登记）。")

    except Exception as e:
        db.rollback()
        print(f"⚠ 内置模型登记失败: {e}")
    finally:
        db.close()
