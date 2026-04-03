from db.session import SessionLocal
from db.db_models.task_table import TaskTable
from db.db_models.inverse_result import InverseResult
from models.registry import ModelRegistry
from services.features.builder import build_features
from models.cvae_generator import CompositionGenerator

import logging
import os
import random
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

_global_cvae_generator: CompositionGenerator | None = None


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


def _score_candidate(
    strength: float,
    elongation: float,
    target_strength: List[float] | None,
    target_elongation: List[float] | None,
    strategy: str,
) -> float:
    score = 0.0

    if target_strength:
        if target_strength[0] <= strength <= target_strength[1]:
            score += 30
        else:
            dist = min(
                abs(strength - target_strength[0]),
                abs(strength - target_strength[1]),
            )
            score += max(0.0, 30.0 - dist * 0.1)

    if target_elongation:
        if target_elongation[0] <= elongation <= target_elongation[1]:
            score += 30
        else:
            dist = min(
                abs(elongation - target_elongation[0]),
                abs(elongation - target_elongation[1]),
            )
            score += max(0.0, 30.0 - dist * 2.0)

    norm_s = min(strength, 1800.0) / 1800.0
    norm_e = min(elongation, 30.0) / 30.0

    if strategy == "strength":
        score += (norm_s * 0.8 + norm_e * 0.2) * 40.0
    elif strategy == "ductility":
        score += (norm_s * 0.2 + norm_e * 0.8) * 40.0
    else:
        score += (norm_s * 0.5 + norm_e * 0.5) * 40.0

    return float(round(min(score, 99.9), 1))


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


def _generate_candidates_with_vae(
    constraints: Dict[str, List[float]],
    target_strength: List[float] | None,
    target_elongation: List[float] | None,
    strategy: str,
    n_samples: int = 100,
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

        score = _score_candidate(
            strength=strength,
            elongation=elongation,
            target_strength=target_strength,
            target_elongation=target_elongation,
            strategy=strategy,
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


def _generate_candidates_mock(
    constraints: Dict[str, List[float]],
    target_strength: List[float] | None,
    target_elongation: List[float] | None,
    strategy: str,
) -> List[dict]:
    candidates: List[dict] = []

    for _ in range(50):
        elements = {
            el: round(random.uniform(rng[0], rng[1]), 2) for el, rng in constraints.items()
        }

        strength = (
            400
            + elements.get("Al", 0) * 60
            + elements.get("V", 0) * 40
            + elements.get("Mo", 0) * 30
            + elements.get("O", 0) * 800
            + elements.get("N", 0) * 1000
            + random.uniform(-50, 50)
        )

        elongation = max(5, 30 - strength / 60)

        score = _score_candidate(
            strength=strength,
            elongation=elongation,
            target_strength=target_strength,
            target_elongation=target_elongation,
            strategy=strategy,
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

        # 2️⃣ 解析输入
        constraints = payload.get("constraints", {})
        target_strength = payload.get("targetStrength", payload.get("targetRm"))
        target_elongation = payload.get("targetElongation", payload.get("targetA"))
        strategy = payload.get("strategy", "balanced")

        # 3️⃣ 使用 VAE 生成候选方案；失败时回退到 mock
        try:
            candidates = _generate_candidates_with_vae(
                constraints=constraints,
                target_strength=target_strength,
                target_elongation=target_elongation,
                strategy=strategy,
                n_samples=100,
            )
            if not candidates:
                logger.warning("No candidates generated by VAE, fallback to mock.")
                candidates = _generate_candidates_mock(
                    constraints=constraints,
                    target_strength=target_strength,
                    target_elongation=target_elongation,
                    strategy=strategy,
                )
        except Exception:
            logger.exception("VAE-based inverse generation failed, fallback to mock.")
            candidates = _generate_candidates_mock(
                constraints=constraints,
                target_strength=target_strength,
                target_elongation=target_elongation,
                strategy=strategy,
            )

        # 5️⃣ Top5
        candidates.sort(key=lambda x: x["score"], reverse=True)
        top5 = candidates[:5]

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
