import random

def mock_inverse_design(data):
    """
    模拟逆向设计：生成 Top 5 推荐方案
    """
    candidates = []

    # 1. 解析约束
    constraints = data.constraints
    target_rm = data.targetRm
    target_a = data.targetA
    strategy = data.strategy

    # 2. 生成 50 个候选方案
    for _ in range(50):
        elements = {}
        for el, rng in constraints.items():
            val = random.uniform(rng[0], rng[1])
            elements[el] = round(val, 2)

        # 简单模拟性能
        base_strength = 400
        base_strength += elements.get('Al', 0) * 60
        base_strength += elements.get('V', 0) * 40
        base_strength += elements.get('Mo', 0) * 30
        base_strength += elements.get('O', 0) * 800
        base_strength += elements.get('N', 0) * 1000

        pred_rm = base_strength + random.uniform(-50, 50)
        pred_a = max(5, 30 - (pred_rm / 60))

        # 3. 计算得分
        score = 0

        # A. 命中目标范围得分
        rm_hit = target_rm[0] <= pred_rm <= target_rm[1]
        a_hit = target_a[0] <= pred_a <= target_a[1]

        if rm_hit: score += 30
        else:
            dist = min(abs(pred_rm - target_rm[0]), abs(pred_rm - target_rm[1]))
            score += max(0, 30 - dist * 0.1)

        if a_hit: score += 30
        else:
            dist = min(abs(pred_a - target_a[0]), abs(pred_a - target_a[1]))
            score += max(0, 30 - dist * 2)

        # B. 策略加分
        norm_rm = min(pred_rm, 1800) / 1800
        norm_a = min(pred_a, 30) / 30

        if strategy == 'strength':
            strategy_score = (norm_rm * 0.8 + norm_a * 0.2) * 40
        elif strategy == 'ductility':
            strategy_score = (norm_rm * 0.2 + norm_a * 0.8) * 40
        else:
            strategy_score = (norm_rm * 0.5 + norm_a * 0.5) * 40

        score += strategy_score

        candidates.append({
            "elements": elements,
            "process": "950℃ / 1h / AC",
            "predicted_rm": round(pred_rm, 1),
            "predicted_a": round(pred_a, 1),
            "score": round(min(score, 99.9), 1)
        })

    # 4. 排序并取 Top 5
    candidates.sort(key=lambda x: x['score'], reverse=True)
    top_5 = candidates[:5]

    for i, item in enumerate(top_5):
        item['rank'] = i + 1

    return top_5