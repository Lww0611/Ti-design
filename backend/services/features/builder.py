# backend/services/features/builder.py
from services.features.process_rewriter import rewrite_process_text

ELEMENT_COLUMNS = [
    "Ti", "Mo", "Al", "Sn", "V", "Zr", "Cr", "Nb", "Ta", "Fe",
    "W", "Si", "O", "C", "N", "H", "Ni", "Cu", "B", "Mn",
    "Y", "Zn"
]


def build_element_features(elements: dict) -> dict:
    """
    元素特征补齐
    """
    # 前端通常只填写合金元素，不填写 Ti。
    # 为避免 Ti=0 导致输入分布严重偏离训练集，这里用平衡法自动补齐 Ti：
    # Ti = max(0, 100 - sum(other elements))
    elements_local = {k: float(v) for k, v in (elements or {}).items()}
    ti_given = elements_local.get("Ti")
    if ti_given is None or ti_given <= 0:
        other_sum = 0.0
        for k, v in elements_local.items():
            if k != "Ti":
                other_sum += max(0.0, float(v))
        elements_local["Ti"] = max(0.0, 100.0 - other_sum)

    features = {}
    for ele in ELEMENT_COLUMNS:
        features[f"{ele} (wt%)"] = float(elements_local.get(ele, 0.0))
    return features


def normalize_process_structured(heat_treatment: dict, hot_working: dict) -> str:
    """
    把结构化热处理 / 热加工参数转换为文本 Process
    """

    texts = []

    # ---- 热加工 ----
    if hot_working and hot_working.get("enabled"):
        texts.append(
            f"{hot_working.get('type', 'hot-working').lower()} "
            f"{hot_working.get('temperature', '')}C "
            f"deformation {hot_working.get('deformation', '')}% "
            f"{hot_working.get('passes', 1)} passes"
        )

    # ---- 热处理阶段 ----
    if heat_treatment and heat_treatment.get("enabled"):
        for stage in heat_treatment.get("stages", []):
            stage_text = (
                f"{stage.get('type', 'treatment').lower()} "
                f"{stage.get('temperature', '')}C "
                f"{stage.get('duration', '')}h "
                f"{stage.get('coolingMode', '').lower()}"
            )
            texts.append(stage_text)

    if not texts:
        return "as-received"

    return "; ".join(texts)


def build_features(payload: dict) -> dict:
    """
    前端输入 → 模型特征
    """

    features = {}

    # ---- 1. 元素 ----
    features.update(build_element_features(payload.get("elements", {})))

    # ---- 2. transition temperature ----
    # 之前固定为 0 会导致输入明显偏离训练分布（对钛合金不合理）。
    # 在前端未提供该字段时，使用 Ti 的典型相变温度 882°C 作为默认值。
    features["transition temperature (°C)"] = float(payload.get("transitionTemperature", 882.0))

    # ---- 3. Process ----
    mode = payload.get("heatTreatmentMode")

    if mode == "text":
        process_text = payload.get("heatTreatmentText", "").strip()
        if not process_text:
            process_text = "as-received"
        else:
            process_text = rewrite_process_text(process_text)
    else:
        process_text = normalize_process_structured(
            payload.get("heatTreatment"),
            payload.get("hotWorking"),
        )

    features["Process"] = process_text

    return features
