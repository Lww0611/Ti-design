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


def init_builtin_models() -> None:
    manifest_path = _BACKEND_ROOT / "models" / "weights" / "bert_xgb_v2" / "manifest.json"
    if not manifest_path.is_file():
        print("⚠ 跳过内置模型登记: 未找到 bert_xgb_v2/manifest.json")
        return

    with open(manifest_path, encoding="utf-8") as f:
        manifest = json.load(f)

    db = SessionLocal()
    try:
        user = db.query(User).order_by(User.id).first()
        if not user:
            print("⚠ 跳过内置模型登记: 数据库中无用户，请先注册账号")
            return

        name = "BERT-XGB-v2"
        features = list(manifest.get("numeric_columns", [])) + ["Process"]
        metrics = manifest.get("metrics")

        existing = (
            db.query(Model)
            .filter(Model.user_id == user.id, Model.model_name == name)
            .first()
        )
        if existing:
            if metrics is not None:
                existing.metrics = metrics
                existing.model_file_path = "models/weights/bert_xgb_v2"
                db.commit()
            return

        rec = Model(
            user_id=user.id,
            model_name=name,
            content=None,
            model_file_path="models/weights/bert_xgb_v2",
            features=features,
            target="Strength (MPa); Elongation (%)",
            task_type="regression",
            description=(
                "内置：sentence-transformers 句向量 + 双 XGBoost（强度/延伸率），"
                "权重见 models/weights/bert_xgb_v2/。"
            ),
            status="builtin",
            metrics=metrics,
            created_at=datetime.utcnow(),
        )
        db.add(rec)
        db.commit()
        print(f"✅ 已登记内置模型 {name} (model.id={rec.id})")
    except Exception as e:
        db.rollback()
        print(f"⚠ 内置模型登记失败: {e}")
    finally:
        db.close()
