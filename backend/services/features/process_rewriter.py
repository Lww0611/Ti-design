import os
import re
from typing import Optional


class ProcessRewriter:
    """
    将自由文本热处理描述重写到 newdata3 的 Process 风格。

    优先级：
    1) 规则重写（稳定、快速）
    2) 可选轻量 LLM 重写（flan-t5-small），再做格式清洗
    """

    def __init__(self) -> None:
        self.use_llm = os.getenv("PROCESS_REWRITE_USE_LLM", "0") == "1"
        self._llm = None

    def rewrite(self, raw_text: str) -> str:
        text = (raw_text or "").strip()
        if not text:
            return "As-received"

        rule_result = self._rewrite_by_rules(text)
        if not self.use_llm:
            return rule_result

        llm_result = self._rewrite_by_llm(text)
        if llm_result:
            return llm_result
        return rule_result

    def _rewrite_by_rules(self, text: str) -> str:
        t = self._normalize_input(text)

        # 已经接近数据集句式，直接返回
        if any(k in t.lower() for k in ["solution:", "aging:", "annealing:", "laser powder bed fusion", "lded"]):
            return self._final_cleanup(t)

        solution = self._extract_stage(t, stage="solution")
        aging = self._extract_stage(t, stage="aging")
        anneal = self._extract_stage(t, stage="annealing")

        parts = []
        if solution:
            parts.append(solution)
        if aging:
            parts.append(aging)
        if anneal:
            parts.append(anneal)

        if not parts:
            return self._final_cleanup(t)

        return self._final_cleanup(" ".join(parts))

    def _extract_stage(self, text: str, stage: str) -> Optional[str]:
        stage_alias = {
            "solution": r"(solution|sol\.?|固溶)",
            "aging": r"(aging|age|时效)",
            "annealing": r"(annealing|anneal|退火)",
        }[stage]

        # 只在该 stage 周围提取，避免跨段误配
        m_stage = re.search(stage_alias, text, flags=re.IGNORECASE)
        if not m_stage:
            return None

        sub = text[m_stage.start():]
        temp = self._extract_temperature(sub)
        hour = self._extract_hour(sub)
        cool_name, cool_code = self._extract_cooling(sub)

        if stage == "solution":
            label = "Solution"
        elif stage == "aging":
            label = "Aging"
        else:
            label = "Annealing"

        temp_s = f"{temp:.1f}" if temp is not None else "900.0"
        hour_s = f"{hour:.1f}" if hour is not None else "1.0"

        if cool_name and cool_code:
            return f"{label}: {temp_s}°C for {hour_s}h, cooled by {cool_name} ({cool_code})."
        return f"{label}: {temp_s}°C for {hour_s}h."

    def _extract_temperature(self, text: str) -> Optional[float]:
        m = re.search(r"(\d+(?:\.\d+)?)\s*°?\s*c", text, flags=re.IGNORECASE)
        if m:
            return float(m.group(1))
        return None

    def _extract_hour(self, text: str) -> Optional[float]:
        # 如 6h / 6 h / 0.5h
        m_h = re.search(r"(\d+(?:\.\d+)?)\s*h\b", text, flags=re.IGNORECASE)
        if m_h:
            return float(m_h.group(1))

        # 如 30 min -> 0.5h
        m_m = re.search(r"(\d+(?:\.\d+)?)\s*min", text, flags=re.IGNORECASE)
        if m_m:
            return float(m_m.group(1)) / 60.0
        return None

    def _extract_cooling(self, text: str) -> tuple[Optional[str], Optional[str]]:
        t = text.lower()
        if re.search(r"\b(wq|water quench|水淬)\b", t):
            return "Water Quench", "WQ"
        if re.search(r"\b(ac|air cool|空冷)\b", t):
            return "Air Cool", "AC"
        if re.search(r"\b(fc|furnace cool|炉冷)\b", t):
            return "Furnace Cool", "FC"
        return None, None

    def _normalize_input(self, text: str) -> str:
        t = text.replace("；", ";").replace("。", ".")
        t = re.sub(r"\s+", " ", t).strip()
        return t

    def _final_cleanup(self, text: str) -> str:
        t = re.sub(r"\s+", " ", text).strip()
        t = t.replace(" .", ".")
        return t

    def _rewrite_by_llm(self, text: str) -> Optional[str]:
        """
        轻量 LLM 可选路径（需要联网下载模型，首次会慢）。
        设置 PROCESS_REWRITE_USE_LLM=1 后启用。
        """
        try:
            if self._llm is None:
                from transformers import pipeline

                self._llm = pipeline(
                    "text2text-generation",
                    model="google/flan-t5-small",
                    max_new_tokens=128,
                )

            prompt = (
                "Rewrite titanium alloy process text to dataset style. "
                "Use patterns like: "
                "'Solution: 900.0°C for 1.0h, cooled by Water Quench (WQ). "
                "Aging: 550.0°C for 6.0h, cooled by Air Cool (AC).' "
                "Only return rewritten process sentence.\n"
                f"Input: {text}"
            )
            out = self._llm(prompt, do_sample=False)
            if not out:
                return None
            gen = out[0].get("generated_text", "").strip()
            if not gen:
                return None
            return self._final_cleanup(gen)
        except Exception:
            return None


_GLOBAL_REWRITER = ProcessRewriter()


def rewrite_process_text(raw_text: str) -> str:
    return _GLOBAL_REWRITER.rewrite(raw_text)

