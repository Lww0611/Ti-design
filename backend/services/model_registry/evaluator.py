import pandas as pd
from sklearn.metrics import r2_score

from services.features.builder import ELEMENT_COLUMNS, build_features


def evaluate_bert_xgb_v2_on_dataframe(df: pd.DataFrame) -> dict:
    """
    在系统数据集上对 BERT-XGB-v2 逐行构造与线上一致的 features，计算强度/延伸率 R²。
    """
    from models.forward.bert_xgb_v2_model import BertXGBV2Model

    required = (
        ["Process", "Strength (MPa)", "Elongation (%)"]
        + [f"{e} (wt%)" for e in ELEMENT_COLUMNS]
    )
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"数据集缺少列: {missing}")

    work = df.dropna(subset=["Process", "Strength (MPa)", "Elongation (%)"]).copy()
    work = work[work["Process"].astype(str).str.strip().str.len() > 0]
    if work.empty:
        raise ValueError("有效样本为空（请检查 Process / 目标列）")

    model = BertXGBV2Model()
    pred_s: list[float] = []
    pred_e: list[float] = []
    tcol = "transition temperature (°C)"

    for _, row in work.iterrows():
        elements = {ele: float(row[f"{ele} (wt%)"]) for ele in ELEMENT_COLUMNS}
        payload = {
            "elements": elements,
            "hotWorking": {
                "enabled": False,
                "type": "Forging",
                "temperature": 0.0,
                "deformation": 0.0,
                "passes": 1,
            },
            "heatTreatmentMode": "text",
            "heatTreatmentText": str(row["Process"]),
            "heatTreatment": {"enabled": False, "stages": []},
        }
        if tcol in row.index and pd.notna(row[tcol]):
            payload["transitionTemperature"] = float(row[tcol])

        feat = build_features(payload)
        out = model.predict(feat)
        pred_s.append(out["strength"])
        pred_e.append(out["elongation"])

    y_s = work["Strength (MPa)"].astype(float).to_numpy()
    y_e = work["Elongation (%)"].astype(float).to_numpy()
    r2_s = float(r2_score(y_s, pred_s))
    r2_e = float(r2_score(y_e, pred_e))
    return {
        "r2_score": (r2_s + r2_e) / 2.0,
        "r2_score_strength": r2_s,
        "r2_score_elongation": r2_e,
        "n_samples": int(len(work)),
    }


def evaluate_matscibert_xgb_on_dataframe(df: pd.DataFrame) -> dict:
    """
    在系统数据集上对 MatSciBERT-XGB 逐行构造与线上一致的 features，计算强度/延伸率 R²。
    """
    from models.forward.matscibert_xgb_model import MatSciBERTXGBModel

    required = (
        ["Process", "Strength (MPa)", "Elongation (%)"]
        + [f"{e} (wt%)" for e in ELEMENT_COLUMNS]
    )
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"数据集缺少列: {missing}")

    work = df.dropna(subset=["Process", "Strength (MPa)", "Elongation (%)"]).copy()
    work = work[work["Process"].astype(str).str.strip().str.len() > 0]
    if work.empty:
        raise ValueError("有效样本为空（请检查 Process / 目标列）")

    model = MatSciBERTXGBModel()
    pred_s: list[float] = []
    pred_e: list[float] = []
    tcol = "transition temperature (°C)"

    for _, row in work.iterrows():
        elements = {ele: float(row[f"{ele} (wt%)"]) for ele in ELEMENT_COLUMNS}
        payload = {
            "elements": elements,
            "hotWorking": {
                "enabled": False,
                "type": "Forging",
                "temperature": 0.0,
                "deformation": 0.0,
                "passes": 1,
            },
            "heatTreatmentMode": "text",
            "heatTreatmentText": str(row["Process"]),
            "heatTreatment": {"enabled": False, "stages": []},
        }
        if tcol in row.index and pd.notna(row[tcol]):
            payload["transitionTemperature"] = float(row[tcol])

        feat = build_features(payload)
        out = model.predict(feat)
        pred_s.append(out["strength"])
        pred_e.append(out["elongation"])

    y_s = work["Strength (MPa)"].astype(float).to_numpy()
    y_e = work["Elongation (%)"].astype(float).to_numpy()
    r2_s = float(r2_score(y_s, pred_s))
    r2_e = float(r2_score(y_e, pred_e))
    return {
        "r2_score": (r2_s + r2_e) / 2.0,
        "r2_score_strength": r2_s,
        "r2_score_elongation": r2_e,
        "n_samples": int(len(work)),
    }


def evaluate_model_on_data(model_obj, df: pd.DataFrame, features: list, target_col: str):
    """
    核心评估逻辑：传入模型对象、DataFrame、特征列表和目标列名
    """
    if target_col not in df.columns:
        raise ValueError(f"目标列 {target_col} 不在数据集中")

    # 执行精准切片
    X = df[features]
    y = df[target_col]

    # 执行预测
    y_pred = model_obj.predict(X)

    # 计算评分
    return float(r2_score(y, y_pred))