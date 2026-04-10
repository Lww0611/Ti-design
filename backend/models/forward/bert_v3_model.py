from __future__ import annotations

from pathlib import Path
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

    def predict(self, features: dict) -> dict:
        X = self._build_input_frame(features, self.feature_columns)
        self._patch_legacy_imputer_attrs(self.xgb_model)
        if self.rf_model is not None:
            self._patch_legacy_imputer_attrs(self.rf_model)

        xgb_strength, _ = self._decode_prediction(self.xgb_model.predict(X))
        strength = xgb_strength
        elongation = None

        # According to training artifact assignment: XGBoost -> strength, RF -> elongation.
        if self.rf_model is not None:
            try:
                X_rf = self._build_input_frame(features, self.rf_feature_columns)
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
