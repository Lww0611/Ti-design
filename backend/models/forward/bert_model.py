import pickle
import numpy as np
from pathlib import Path

from models.base import BaseModel


class BertRegressionModel(BaseModel):
    """
    BERT + XGBoost 回归模型
    """
    name = "BERT-Regression"

    def __init__(self):
        base_dir = Path(__file__).resolve().parent.parent / "weights" / "bert_xgb"

        self.encoder_path = base_dir / "bert_encoder.pkl"
        self.strength_model_path = base_dir / "bert_xgb_strength.pkl"
        self.elongation_model_path = base_dir / "bert_xgb_elongation.pkl"

        self.encoder = None
        self.strength_model = None
        self.elongation_model = None

        self.numeric_columns = [
            'Ti (wt%)', 'Mo (wt%)', 'Al (wt%)', 'Sn (wt%)', 'V (wt%)',
            'Zr (wt%)', 'Cr (wt%)', 'Nb (wt%)', 'Ta (wt%)', 'Fe (wt%)',
            'W (wt%)', 'Si (wt%)', 'O (wt%)', 'C (wt%)', 'N (wt%)',
            'H (wt%)', 'Ni (wt%)', 'Cu (wt%)', 'B (wt%)', 'Mn (wt%)',
            'Y (wt%)', 'Zn (wt%)', 'transition temperature (°C)'
        ]

        self._load_models()

    # ---------------------------
    # 模型加载
    # ---------------------------
    def _load_models(self):
        print("🔄 Loading BERT hybrid models...")

        with open(self.encoder_path, "rb") as f:
            self.encoder = pickle.load(f)

        with open(self.strength_model_path, "rb") as f:
            self.strength_model = pickle.load(f)["model"]

        with open(self.elongation_model_path, "rb") as f:
            self.elongation_model = pickle.load(f)["model"]

        print("✅ BERT hybrid models loaded successfully.")

    # ---------------------------
    # 特征构建
    # ---------------------------
    def _build_feature_vector(self, features: dict) -> np.ndarray:
        """
        输入:
            {
              "Ti (wt%)": ...,
              ...
              "transition temperature (°C)": ...,
              "Process": "xxx"
            }
        输出:
            shape = (1, N_features)
        """

        # --- 数值特征 ---
        numeric_vector = np.array([
            float(features.get(col, 0.0)) for col in self.numeric_columns
        ]).reshape(1, -1)

        # --- 文本特征 ---
        process_text = features.get("Process", "unknown")
        embedding = self.encoder.encode([process_text])

        # --- 拼接 ---
        combined = np.hstack((numeric_vector, embedding))

        return combined

    # ---------------------------
    # 推理接口
    # ---------------------------
    def predict(self, features: dict) -> dict:
        """
        features: builder.build_features() 输出
        """
        X = self._build_feature_vector(features)

        strength = float(self.strength_model.predict(X)[0])
        elongation = float(self.elongation_model.predict(X)[0])

        return {
            "model": self.name,
            "strength": round(strength, 2),
            "elongation": round(elongation, 2),
            "raw": {
                "strength": round(strength, 2),
                "strength_err": None,
                "elongation": round(elongation, 2),
                "elongation_err": None
            }
        }
