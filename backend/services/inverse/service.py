from db.session import SessionLocal
from db.db_models.task_table import TaskTable
from db.db_models.inverse_result import InverseResult

import random
import logging

logger = logging.getLogger(__name__)


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
            input_json=payload
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        # 2️⃣ 解析输入
        constraints = payload.get("constraints", {})
        target_strength = payload.get("targetStrength", payload.get("targetRm"))
        target_elongation = payload.get("targetElongation", payload.get("targetA"))
        strategy = payload.get("strategy", "balanced")

        candidates = []

        # 3️⃣ 生成候选方案（mock）
        for _ in range(50):
            elements = {
                el: round(random.uniform(rng[0], rng[1]), 2)
                for el, rng in constraints.items()
            }

            # mock 性能预测
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

            # 4️⃣ 评分
            score = 0

            if target_strength:
                if target_strength[0] <= strength <= target_strength[1]:
                    score += 30
                else:
                    dist = min(
                        abs(strength - target_strength[0]),
                        abs(strength - target_strength[1])
                    )
                    score += max(0, 30 - dist * 0.1)

            if target_elongation:
                if target_elongation[0] <= elongation <= target_elongation[1]:
                    score += 30
                else:
                    dist = min(
                        abs(elongation - target_elongation[0]),
                        abs(elongation - target_elongation[1])
                    )
                    score += max(0, 30 - dist * 2)

            # 策略加权
            norm_s = min(strength, 1800) / 1800
            norm_e = min(elongation, 30) / 30

            if strategy == "strength":
                score += (norm_s * 0.8 + norm_e * 0.2) * 40
            elif strategy == "ductility":
                score += (norm_s * 0.2 + norm_e * 0.8) * 40
            else:
                score += (norm_s * 0.5 + norm_e * 0.5) * 40

            candidates.append({
                "elements": elements,
                "predicted_strength": round(strength, 1),
                "predicted_elongation": round(elongation, 1),
                "score": round(min(score, 99.9), 1)
            })

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
