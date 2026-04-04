from db.session import SessionLocal
from db.db_models.task_table import TaskTable
from db.db_models.inverse_result import InverseResult
from models.registry import ModelRegistry
from services.features.builder import build_features
from models.cvae_generator import CompositionGenerator

import logging
import os
import random
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def _normalize_interval(raw) -> Optional[List[float]]:
    """把前端/JSON 的目标区间规范为 [lo, hi] 浮点，避免滑块数据未参与计算。"""
    if raw is None:
        return None
    try:
        if not isinstance(raw, (list, tuple)) or len(raw) < 2:
            return None
        a, b = float(raw[0]), float(raw[1])
        return [a, b]
    except (TypeError, ValueError):
        return None


def _normalize_constraints(raw) -> Dict[str, List[float]]:
    out: Dict[str, List[float]] = {}
    if not isinstance(raw, dict):
        return out
    for k, v in raw.items():
        try:
            if isinstance(v, (list, tuple)) and len(v) >= 2:
                out[str(k)] = [float(v[0]), float(v[1])]
        except (TypeError, ValueError):
            continue
    return out

_global_cvae_generator: CompositionGenerator | None = None


def _composition_key(elements: Dict[str, float], ndigits: int = 3) -> str:
    """成分去重用键（排序后固定小数位，避免 Top5 出现同一配方占满多行）。"""
    return "|".join(f"{k}:{round(float(v), ndigits)}" for k, v in sorted(elements.items()))


def _dist_to_interval(value: float, interval: List[float] | None) -> float:
    """到目标区间的距离：区间内为 0，区间外为到较近边界的距离。"""
    if not interval or len(interval) != 2:
        return 0.0
    lo, hi = float(interval[0]), float(interval[1])
    if lo > hi:
        lo, hi = hi, lo
    if lo <= value <= hi:
        return 0.0
    return float(min(abs(value - lo), abs(value - hi)))


def _total_target_distance(
    strength: float,
    elongation: float,
    target_strength: List[float] | None,
    target_elongation: List[float] | None,
) -> float:
    return _dist_to_interval(strength, target_strength) + _dist_to_interval(
        elongation, target_elongation
    )


def _dedupe_candidates_by_composition(
    candidates: List[dict],
    target_strength: List[float] | None,
    target_elongation: List[float] | None,
) -> List[dict]:
    """相同成分只保留「离双目标总距离更小」的一条。"""
    best: Dict[str, dict] = {}
    for c in candidates:
        key = _composition_key(c["elements"])
        prev = best.get(key)
        d = _total_target_distance(
            float(c["predicted_strength"]),
            float(c["predicted_elongation"]),
            target_strength,
            target_elongation,
        )
        if prev is None:
            best[key] = c
            continue
        d_prev = _total_target_distance(
            float(prev["predicted_strength"]),
            float(prev["predicted_elongation"]),
            target_strength,
            target_elongation,
        )
        if d < d_prev:
            best[key] = c
    return list(best.values())


def _ui_fit_score(
    strength: float,
    elongation: float,
    target_strength: List[float] | None,
    target_elongation: List[float] | None,
) -> float:
    """0–100：与目标区间的匹配程度，供前端展示。"""
    parts: List[float] = []
    if target_strength:
        ds = _dist_to_interval(strength, target_strength)
        span = max(float(target_strength[1]) - float(target_strength[0]), 1.0)
        parts.append(max(0.0, 50.0 - (ds / span) * 50.0))
    else:
        parts.append(50.0)
    if target_elongation:
        de = _dist_to_interval(elongation, target_elongation)
        span_e = max(float(target_elongation[1]) - float(target_elongation[0]), 0.5)
        parts.append(max(0.0, 50.0 - (de / span_e) * 50.0))
    else:
        parts.append(50.0)
    return float(round(min(99.9, sum(parts)), 1))


def _balanced_sort_key(
    c: dict,
    target_strength: List[float] | None,
    target_elongation: List[float] | None,
) -> tuple:
    """综合优先：总目标偏差最小，再以归一化 (Rm+A) 作平局打破。升序排序更优在前。"""
    s = float(c["predicted_strength"])
    e = float(c["predicted_elongation"])
    ds = _dist_to_interval(s, target_strength)
    de = _dist_to_interval(e, target_elongation)
    return (ds + de, -(s / 1800.0 + e / 30.0))


def _element_l1(a: Dict[str, float], b: Dict[str, float], keys: List[str]) -> float:
    return sum(abs(float(a.get(k, 0.0)) - float(b.get(k, 0.0))) for k in keys)


def _pick_diverse_top(
    sorted_candidates: List[dict],
    n: int = 5,
) -> List[dict]:
    """在已排序列表上贪心选取成分 L1 足够分散的 TopN，避免表格里多条几乎相同。"""
    if not sorted_candidates:
        return []
    keys = sorted({k for c in sorted_candidates for k in c["elements"]})
    min_l1_steps = [0.55, 0.35, 0.2, 0.1, 0.0]
    for min_l1 in min_l1_steps:
        picked: List[dict] = []
        for c in sorted_candidates:
            if len(picked) >= n:
                break
            if min_l1 > 0 and picked:
                if any(_element_l1(c["elements"], p["elements"], keys) < min_l1 for p in picked):
                    continue
            picked.append(c)
        if len(picked) >= min(n, len(sorted_candidates)):
            return picked[:n]
    return sorted_candidates[:n]


def _get_cvae_generator() -> CompositionGenerator:
    global _global_cvae_generator
    if _global_cvae_generator is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # backend/services/inverse -> backend
        ckpt_path = os.path.join(base_dir, "models", "weights", "cvae_composition.pt")
        scaler_path = os.path.join(base_dir, "models", "weights", "cond_scaler.pkl")
        _global_cvae_generator = CompositionGenerator(
            ckpt_path=ckpt_path,
            scaler_path=scaler_path,
        )
    return _global_cvae_generator


def _predict_performance_for_elements(elements: Dict[str, float]) -> Tuple[float, float]:
    """
    调用统一模型注册表进行正向预测，返回 (strength, elongation)。
    """
    payload = {
        "elements": elements,
        "hotWorking": {
            "enabled": False,
            "type": "hot-working",
            "temperature": 0.0,
            "deformation": 0.0,
            "passes": 1,
        },
        "heatTreatmentMode": "structured",
        "heatTreatment": {
            "enabled": False,
            "stages": [],
        },
        "heatTreatmentText": None,
    }

    features = build_features(payload)
    model_instance = ModelRegistry.get_model("BERT-XGB-v2")
    if not model_instance:
        raise RuntimeError("Model 'BERT-XGB-v2' not found in ModelRegistry")

    pred_raw = model_instance.predict(features)
    if not isinstance(pred_raw, dict):
        pred_raw = {"strength": pred_raw, "elongation": None, "raw": {}}

    strength = float(pred_raw.get("strength", 0.0) or 0.0)
    elongation = float(pred_raw.get("elongation", 0.0) or 0.0)
    return strength, elongation


def _generate_random_forward_candidates(
    constraints: Dict[str, List[float]],
    target_strength: Optional[List[float]],
    target_elongation: Optional[List[float]],
    n_random: int,
) -> List[dict]:
    """
    在元素约束盒内均匀随机采样 + 真实正向模型。
    VAE 流形往往窄，正向预测容易挤在某一强度带；随机点能把「目标区间」在排序里真正体现出来。
    """
    candidates: List[dict] = []
    if not constraints:
        return candidates
    keys = list(constraints.keys())
    for _ in range(n_random):
        elements: Dict[str, float] = {}
        for el in keys:
            lo, hi = constraints[el]
            lo, hi = float(lo), float(hi)
            if hi < lo:
                lo, hi = hi, lo
            if hi <= 0 and lo <= 0:
                elements[el] = 0.0
            else:
                elements[el] = round(random.uniform(lo, hi), 3)
        try:
            strength, elongation = _predict_performance_for_elements(elements)
        except Exception:
            continue
        candidates.append(
            {
                "elements": elements,
                "predicted_strength": round(strength, 1),
                "predicted_elongation": round(elongation, 1),
                "score": _ui_fit_score(
                    strength, elongation, target_strength, target_elongation
                ),
            }
        )
    return candidates


def _generate_candidates_with_vae(
    constraints: Dict[str, List[float]],
    target_strength: Optional[List[float]],
    target_elongation: Optional[List[float]],
    n_samples: int = 100,
    n_random_supplement: int = 280,
) -> List[dict]:
    generator = _get_cvae_generator()

    compositions = generator.sample_compositions(
        constraints=constraints,
        target_strength=target_strength,
        target_elongation=target_elongation,
        n_samples=n_samples,
    )

    candidates: List[dict] = []

    for elements in compositions:
        try:
            strength, elongation = _predict_performance_for_elements(elements)
        except Exception as e:
            logger.warning(f"Forward prediction failed for elements {elements}: {e}")
            continue

        score = _ui_fit_score(
            strength, elongation, target_strength, target_elongation
        )

        candidates.append(
            {
                "elements": elements,
                "predicted_strength": round(strength, 1),
                "predicted_elongation": round(elongation, 1),
                "score": score,
            }
        )

    if n_random_supplement > 0 and constraints:
        candidates.extend(
            _generate_random_forward_candidates(
                constraints,
                target_strength,
                target_elongation,
                n_random_supplement,
            )
        )

    return candidates


def _generate_candidates_mock(
    constraints: Dict[str, List[float]],
    target_strength: Optional[List[float]],
    target_elongation: Optional[List[float]],
) -> List[dict]:
    candidates: List[dict] = []

    rm = target_strength
    ae = target_elongation
    base_rm = (rm[0] + rm[1]) / 2.0 if rm else 1000.0
    base_a = (ae[0] + ae[1]) / 2.0 if ae else 15.0
    half_rm = max(abs(rm[1] - rm[0]) / 2.0, 60.0) if rm else 160.0
    half_a = max(abs(ae[1] - ae[0]) / 2.0, 1.5) if ae else 6.0

    for _ in range(160):
        elements = {
            el: round(random.uniform(rng[0], rng[1]), 2) for el, rng in constraints.items()
        }

        comp_tweak = (
            (elements.get("Al", 0) - 6.2) * 42
            + (elements.get("V", 0) - 4.0) * 28
            + elements.get("Mo", 0) * 22
            + random.uniform(-half_rm * 0.45, half_rm * 0.45)
        )
        strength = base_rm + comp_tweak * 0.4
        strength = max(400.0, min(1800.0, strength))

        elongation = (
            base_a
            + random.uniform(-half_a * 0.55, half_a * 0.55)
            + (1100.0 - min(strength, 1100.0)) / 95.0
        )
        elongation = max(2.0, min(38.0, elongation))

        score = _ui_fit_score(
            strength, elongation, target_strength, target_elongation
        )

        candidates.append(
            {
                "elements": elements,
                "predicted_strength": round(strength, 1),
                "predicted_elongation": round(elongation, 1),
                "score": score,
            }
        )

    return candidates


def inverse_with_registry(payload: dict):
    """
    统一逆向设计接口（与 predict 完全一致风格）：
    - 创建 task
    - 执行逆向搜索（mock）
    - 保存 Top5 结果
    - 更新 task 状态
    - 返回 task_id + results
    """
    db = SessionLocal()

    try:
        # 1️⃣ 创建任务
        task = TaskTable(
            task_type="inverse",
            status="running",
            title="Inverse Design",
            input_json=payload,
            case_id=payload.get("case_id"),
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        # 2️⃣ 解析输入（规范区间，确保滑块 targetRm/targetA 参与 CVAE 与排序）
        constraints = _normalize_constraints(payload.get("constraints") or {})
        target_strength = _normalize_interval(
            payload.get("targetStrength", payload.get("targetRm"))
        )
        target_elongation = _normalize_interval(
            payload.get("targetElongation", payload.get("targetA"))
        )

        # 3️⃣ 使用 VAE 生成候选方案；失败时回退到 mock
        try:
            candidates = _generate_candidates_with_vae(
                constraints=constraints,
                target_strength=target_strength,
                target_elongation=target_elongation,
                n_samples=400,
            )
            if not candidates:
                logger.warning("No candidates generated by VAE, fallback to mock.")
                candidates = _generate_candidates_mock(
                    constraints=constraints,
                    target_strength=target_strength,
                    target_elongation=target_elongation,
                )
        except Exception:
            logger.exception("VAE-based inverse generation failed, fallback to mock.")
            candidates = _generate_candidates_mock(
                constraints=constraints,
                target_strength=target_strength,
                target_elongation=target_elongation,
            )

        # 5️⃣ 去重 → 综合排序 → 成分多样化取 Top5
        candidates = _dedupe_candidates_by_composition(
            candidates, target_strength, target_elongation
        )
        candidates.sort(
            key=lambda x: _balanced_sort_key(x, target_strength, target_elongation)
        )
        top5 = _pick_diverse_top(candidates, 5)

        results = []

        for idx, item in enumerate(top5, start=1):
            db_item = InverseResult(
                task_id=task.id,
                rank=idx,
                elements=item["elements"],
                predicted_strength=item["predicted_strength"],   # 或 strength
                predicted_elongation=item["predicted_elongation"], # 或 elongation
                score=item["score"],
                raw=item.get("raw", {})
            )
            db.add(db_item)
            db.commit()

            results.append({
                "rank": idx,
                **item
            })

        # 6️⃣ 更新任务状态
        task.status = "success"
        db.commit()

        return {
            "task_id": task.id,
            "results": results
        }

    except Exception as e:
        logger.exception("Inverse design failed")
        if "task" in locals():
            task.status = "failed"
            db.commit()
        raise e

    finally:
        db.close()
