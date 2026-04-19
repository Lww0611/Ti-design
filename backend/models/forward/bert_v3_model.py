from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any

import joblib
import numpy as np
import pandas as pd

from models.base import BaseModel


class BertV3Model(BaseModel):
    """
    Legacy Bert-v3 pipeline wrapper.
    Loads sklearn pickles and adapts online feature dict to training columns.
    """

    name = "BERT-v3"

    def __init__(self) -> None:
        base_dir = Path(__file__).resolve().parent.parent / "weights" / "bert_v3"
        self.xgb_path = base_dir / "alloy_model_XGBoost.pkl"
        self.rf_path = base_dir / "alloy_model_RF.pkl"

        if not self.xgb_path.is_file():
            raise FileNotFoundError(f"BERT-v3 未就绪: 缺少 {self.xgb_path}")

        xgb_loaded = joblib.load(self.xgb_path)
        rf_loaded = joblib.load(self.rf_path) if self.rf_path.is_file() else None
        self.selected_features: list[Any] | None = None
        self.rf_selected_features: list[Any] | None = None
        if isinstance(xgb_loaded, dict):
            sf = xgb_loaded.get("selected_features")
            if isinstance(sf, (list, tuple)) and len(sf) > 0:
                self.selected_features = list(sf)
        if isinstance(rf_loaded, dict):
            sf = rf_loaded.get("selected_features")
            if isinstance(sf, (list, tuple)) and len(sf) > 0:
                self.rf_selected_features = list(sf)

        self.xgb_model = self._resolve_predictor(xgb_loaded, "alloy_model_XGBoost.pkl")
        self.rf_model = self._resolve_predictor(rf_loaded, "alloy_model_RF.pkl") if rf_loaded is not None else None

        cols = self.selected_features
        if cols is None or len(cols) == 0:
            cols = getattr(self.xgb_model, "feature_names_in_", None)
        if cols is None or len(cols) == 0:
            cols = getattr(self.rf_model, "feature_names_in_", None) if self.rf_model is not None else None
        self.feature_columns = list(cols) if cols is not None and len(cols) > 0 else None

        rf_cols = self.rf_selected_features
        if rf_cols is None or len(rf_cols) == 0:
            rf_cols = getattr(self.rf_model, "feature_names_in_", None) if self.rf_model is not None else None
        self.rf_feature_columns = list(rf_cols) if rf_cols is not None and len(rf_cols) > 0 else self.feature_columns

        self.bert_assets_dir = (
            Path(__file__).resolve().parent.parent / "weights" / "bert_v3" / "legacy_encoder_assets"
        )
        self.bert_runtime_dir = Path(__file__).resolve().parents[1] / "legacy_bert_runtime"
        self.legacy_bert_dir = Path(__file__).resolve().parents[2] / "bert"
        self.extract_script = self._resolve_extract_script()
        self.vocab_path = self.bert_assets_dir / "vocab.txt"
        self.bert_config_path = self.bert_assets_dir / "bert_config.json"
        self.ckpt_path = self.bert_assets_dir / "model.ckpt-1800000"
        self.tf_python = self._resolve_tf_python()
        self._embedding_cache: dict[str, np.ndarray] = {}

        self.xgb_uses_embedding = self._looks_like_embedding_space(self.feature_columns)
        self.rf_uses_embedding = self._looks_like_embedding_space(self.rf_feature_columns)
        if (self.xgb_uses_embedding or self.rf_uses_embedding) and self.tf_python is None:
            raise RuntimeError(
                "BERT-v3 当前权重依赖 embedding 特征，但未找到可用 TensorFlow 解释器。"
                "请安装 TensorFlow，或设置环境变量 BERT_V3_TF_PYTHON 指向可运行的 python。"
            )

    @staticmethod
    def _find_predictor_in_dict(bundle: dict) -> Any | None:
        preferred_keys = (
            "model",
            "estimator",
            "pipeline",
            "xgb_model",
            "rf_model",
            "regressor",
            "best_model",
        )
        for k in preferred_keys:
            v = bundle.get(k)
            if callable(getattr(v, "predict", None)):
                return v

        for v in bundle.values():
            if callable(getattr(v, "predict", None)):
                return v

        return None

    @staticmethod
    def _looks_like_embedding_space(columns: list[Any] | None) -> bool:
        if not columns:
            return False
        numeric_like = 0
        for c in columns:
            s = str(c)
            if s.isdigit():
                numeric_like += 1
        return numeric_like >= max(50, int(len(columns) * 0.8))

    def _resolve_predictor(self, loaded: Any, filename: str) -> Any:
        if callable(getattr(loaded, "predict", None)):
            return loaded

        if isinstance(loaded, dict):
            model_obj = self._find_predictor_in_dict(loaded)
            if model_obj is not None:
                return model_obj

        raise TypeError(
            f"BERT-v3 文件 {filename} 未找到可调用 predict() 的模型对象，"
            f"实际类型: {type(loaded).__name__}"
        )

    def _resolve_tf_python(self) -> str | None:
        candidates = []
        if sys.executable:
            candidates.append(sys.executable)
        env_py = os.getenv("BERT_V3_TF_PYTHON")
        if env_py:
            candidates.append(env_py)
        backend_tfenv_py = str(Path(__file__).resolve().parents[2] / ".tfenv" / "bin" / "python")
        candidates.append(backend_tfenv_py)
        venv_py = str(Path(__file__).resolve().parents[3] / "venv" / "bin" / "python")
        candidates.append(venv_py)
        candidates.append("/opt/homebrew/bin/python3.11")
        candidates.append("python")
        candidates.append("python3")

        for py in candidates:
            try:
                r = subprocess.run(
                    [py, "-c", "import tensorflow as tf; print(tf.__version__)"],
                    capture_output=True,
                    text=True,
                    timeout=120,
                    check=False,
                )
                if r.returncode == 0:
                    return py
            except Exception:
                continue
        return None

    def _resolve_extract_script(self) -> Path:
        candidates = [
            self.bert_runtime_dir / "extract_features.py",
            self.legacy_bert_dir / "extract_features.py",
        ]
        for p in candidates:
            if p.is_file():
                return p
        # keep first candidate in error message path
        return candidates[0]

    def _patch_legacy_imputer_attrs(self, model_obj: Any) -> None:
        """
        Compatibility shim for old pickles under newer sklearn runtime.
        """
        visited = set()

        def walk(obj: Any) -> None:
            oid = id(obj)
            if oid in visited:
                return
            visited.add(oid)

            cls_name = obj.__class__.__name__
            if cls_name == "SimpleImputer" and not hasattr(obj, "_fill_dtype"):
                stat = getattr(obj, "statistics_", None)
                dtype = getattr(stat, "dtype", np.dtype("float64"))
                setattr(obj, "_fill_dtype", dtype)

            if hasattr(obj, "steps"):
                for _, sub in getattr(obj, "steps", []):
                    walk(sub)
            if hasattr(obj, "named_steps"):
                for sub in getattr(obj, "named_steps", {}).values():
                    walk(sub)
            if hasattr(obj, "transformers_"):
                for tr in getattr(obj, "transformers_", []):
                    if isinstance(tr, tuple) and len(tr) >= 2:
                        walk(tr[1])
            if hasattr(obj, "estimator"):
                sub = getattr(obj, "estimator")
                if sub is not None:
                    walk(sub)

        walk(model_obj)

    @staticmethod
    def _scalar(v: Any) -> float:
        arr = np.asarray(v, dtype=float).reshape(-1)
        return float(arr[0]) if arr.size else 0.0

    @staticmethod
    def _decode_prediction(pred: Any) -> tuple[float, float | None]:
        arr = np.asarray(pred, dtype=float)
        if arr.ndim == 0:
            return float(arr), None
        arr = arr.reshape(-1)
        if arr.size == 0:
            return 0.0, None
        if arr.size == 1:
            return float(arr[0]), None
        return float(arr[0]), float(arr[1])

    def _feature_value(self, col: str, features: dict) -> float | str:
        if not isinstance(col, str):
            return 0.0

        if col in features:
            return features[col]

        if col.endswith(" (wt%)"):
            ele = col.replace(" (wt%)", "")
            return self._scalar(features.get(ele, 0.0))

        wt_name = f"{col} (wt%)"
        if wt_name in features:
            return self._scalar(features.get(wt_name, 0.0))

        cl = col.lower()
        if cl in {"process", "condition", "split_conditions"}:
            return str(features.get("Process") or "as-received")
        if "transition" in cl and "temperature" in cl:
            return self._scalar(features.get("transition temperature (°C)", 882.0))

        return 0.0

    def _build_input_frame(self, features: dict, columns: list[Any] | None) -> pd.DataFrame:
        if not columns:
            return pd.DataFrame([features])

        row = {col: self._feature_value(col, features) for col in columns}
        return pd.DataFrame([row], columns=columns)

    @staticmethod
    def _format_num(v: Any) -> float:
        try:
            return float(v)
        except Exception:
            return 0.0

    def _build_legacy_bert_text(self, features: dict) -> str:
        # Keep consistent with legacy training script template.
        order = ["Ti", "Fe", "Zr", "Nb", "Sn", "Ta", "Mo", "Al", "V", "Cr", "Hf", "Mn", "W", "Si", "Cu"]
        parts = []
        for ele in order:
            v = self._format_num(features.get(f"{ele} (wt%)", 0.0))
            if v > 0:
                parts.append(f"{ele} {v}%")
        composition_str = ", ".join(parts)
        condition = str(features.get("Process") or "as-received")
        return f"Titanium alloy composition: {composition_str}. Condition: {condition}"

    def _extract_embedding_vector(self, text: str) -> np.ndarray:
        if text in self._embedding_cache:
            return self._embedding_cache[text]

        if self.tf_python is None:
            raise RuntimeError(
                "BERT-v3 需要 TensorFlow 才能生成 embedding。"
                "请在后端环境安装 tensorflow 后重试。"
            )

        required_paths = [
            self.extract_script,
            self.vocab_path,
            self.bert_config_path,
            Path(f"{self.ckpt_path}.index"),
        ]
        for p in required_paths:
            if not Path(p).exists():
                raise FileNotFoundError(f"BERT-v3 embedding 文件缺失: {p}")

        with tempfile.TemporaryDirectory(prefix="bert_v3_") as td:
            td_path = Path(td)
            input_txt = td_path / "input.txt"
            out_emb = td_path / "embedding.json"
            out_attn = td_path / "attention.json"
            input_txt.write_text(text + "\n", encoding="utf-8")

            cmd = [
                self.tf_python,
                str(self.extract_script),
                "--target=embedding",
                "--layers=11",
                f"--bert_config_file={self.bert_config_path}",
                f"--vocab_file={self.vocab_path}",
                "--do_lower_case=True",
                f"--input_file={input_txt}",
                f"--output_file_embedding={out_emb}",
                f"--output_file_attention={out_attn}",
                "--max_seq_length=128",
                "--batch_size=1",
                f"--init_checkpoint={self.ckpt_path}",
                "--use_one_hot_embeddings=False",
            ]
            run = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if run.returncode != 0:
                raise RuntimeError(
                    f"BERT-v3 embedding 提取失败 (exit={run.returncode}): "
                    f"{(run.stderr or run.stdout)[-500:]}"
                )

            lines = out_emb.read_text(encoding="utf-8").splitlines()
            if not lines:
                raise RuntimeError("BERT-v3 embedding 输出为空")
            payload = json.loads(lines[0])
            feat_list = payload.get("features", [])
            if not feat_list:
                raise RuntimeError("BERT-v3 embedding 输出无 features")

            cls_feat = feat_list[0]
            if cls_feat.get("token") != "[CLS]":
                cls_feat = next((f for f in feat_list if f.get("token") == "[CLS]"), feat_list[0])
            layers = cls_feat.get("layers", [])
            if not layers:
                raise RuntimeError("BERT-v3 embedding 输出缺少 layers")
            values = np.asarray(layers[0].get("values", []), dtype=np.float32)
            if values.size != 768:
                raise RuntimeError(f"BERT-v3 embedding 维度异常: {values.size}")

        self._embedding_cache[text] = values
        return values

    def _build_embedding_frame(self, features: dict, columns: list[Any] | None) -> pd.DataFrame:
        emb = self._extract_embedding_vector(self._build_legacy_bert_text(features))
        if not columns:
            columns = [str(i) for i in range(int(emb.shape[0]))]
        row = {}
        for c in columns:
            idx = int(str(c))
            row[c] = float(emb[idx]) if 0 <= idx < emb.shape[0] else 0.0
        return pd.DataFrame([row], columns=columns)

    def predict(self, features: dict) -> dict:
        use_xgb_embedding = self.xgb_uses_embedding
        X = (
            self._build_embedding_frame(features, self.feature_columns)
            if use_xgb_embedding
            else self._build_input_frame(features, self.feature_columns)
        )
        self._patch_legacy_imputer_attrs(self.xgb_model)
        if self.rf_model is not None:
            self._patch_legacy_imputer_attrs(self.rf_model)

        xgb_strength, _ = self._decode_prediction(self.xgb_model.predict(X))
        strength = xgb_strength
        elongation = None

        # According to training artifact assignment: XGBoost -> strength, RF -> elongation.
        if self.rf_model is not None:
            try:
                use_rf_embedding = self.rf_uses_embedding
                X_rf = (
                    self._build_embedding_frame(features, self.rf_feature_columns)
                    if use_rf_embedding
                    else self._build_input_frame(features, self.rf_feature_columns)
                )
                rf_out_1, rf_out_2 = self._decode_prediction(self.rf_model.predict(X_rf))
                elongation = rf_out_2 if rf_out_2 is not None else rf_out_1
            except Exception:
                # Keep strength-only output when RF prediction is not available.
                pass

        if elongation is not None:
            elongation = max(0.0, float(elongation))

        return {
            "model": self.name,
            "strength": round(float(strength), 2),
            "elongation": None if elongation is None else round(float(elongation), 2),
            "raw": {
                "strength": round(float(strength), 2),
                "strength_err": None,
                "elongation": None if elongation is None else round(float(elongation), 2),
                "elongation_err": None,
            },
        }
