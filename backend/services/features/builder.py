# backend/services/features/builder.py

ELEMENT_COLUMNS = [
    "Ti", "Mo", "Al", "Sn", "V", "Zr", "Cr", "Nb", "Ta", "Fe",
    "W", "Si", "O", "C", "N", "H", "Ni", "Cu", "B", "Mn",
    "Y", "Zn"
]


def build_element_features(elements: dict) -> dict:
    """
    元素特征补齐
    """
    features = {}
    for ele in ELEMENT_COLUMNS:
        features[f"{ele} (wt%)"] = float(elements.get(ele, 0.0))
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
    features["transition temperature (°C)"] = 0

    # ---- 3. Process ----
    mode = payload.get("heatTreatmentMode")

    if mode == "text":
        process_text = payload.get("heatTreatmentText", "").strip()
        if not process_text:
            process_text = "unknown process"
    else:
        process_text = normalize_process_structured(
            payload.get("heatTreatment"),
            payload.get("hotWorking"),
        )

    features["Process"] = process_text

    return features
