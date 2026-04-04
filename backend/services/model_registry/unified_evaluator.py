"""
通用模型评估入口：模型管理「重新评估」与工作流「模型评估」共用同一套逻辑
（均通过 POST /api/v1/models/{id}/evaluate，由 model_manager 调用本模块）。

扩展方式：
  在应用启动后调用 register_evaluation_strategy(strategy_id, handler)，或在本文件末尾
  的 _BUILTIN_MODEL_STRATEGY 中为新的内置模型增加映射。

handler 签名: (model_rec: Model, df: pd.DataFrame) -> dict
返回 dict 需至少包含业务需要的键；模型管理列表目前读取 metrics.r2_score。
"""
from __future__ import annotations

import io
from typing import Callable

import joblib
import pandas as pd

from db.db_models.model import Model
from services.model_registry.evaluator import (
    evaluate_bert_xgb_v2_on_dataframe,
    evaluate_matscibert_xgb_on_dataframe,
    evaluate_model_on_data,
)

EvaluationHandler = Callable[[Model, pd.DataFrame], dict]

_STRATEGIES: dict[str, EvaluationHandler] = {}

# 内置模型名 -> 策略 id（无 content、权重在磁盘等情况）
_BUILTIN_MODEL_STRATEGY: dict[str, str] = {
    "BERT-XGB-v2": "pipeline_bert_xgb_v2",
    "MatSciBERT-XGB": "pipeline_matscibert_xgb",
}


def register_evaluation_strategy(strategy_id: str, handler: EvaluationHandler) -> None:
    """注册一种评估策略，供 resolve 命中时使用。"""
    _STRATEGIES[strategy_id] = handler


def list_evaluation_strategies() -> list[str]:
    return sorted(_STRATEGIES.keys())


def resolve_strategy_id(model_rec: Model) -> str:
    """
    根据数据库记录解析应使用的评估策略。
    后续若 Model 增加 evaluation_backend 字段，可优先读取该字段。
    """
    backend = getattr(model_rec, "evaluation_backend", None)
    if backend and isinstance(backend, str) and backend in _STRATEGIES:
        return backend

    if model_rec.status == "builtin" and model_rec.model_name in _BUILTIN_MODEL_STRATEGY:
        return _BUILTIN_MODEL_STRATEGY[model_rec.model_name]

    if model_rec.content:
        return "pickle_tabular_regressor"

    raise ValueError(
        f"无法选择评估策略：模型「{model_rec.model_name}」既无 content，也不是已注册的内置模型。"
    )


def evaluate_model_record(model_rec: Model, df: pd.DataFrame) -> dict:
    """
    对单条 Model 记录在给定 DataFrame（通常为系统评估集）上计算指标。
    模型管理与工作流评估应只依赖此函数，而不各自实现分支逻辑。
    """
    strategy_id = resolve_strategy_id(model_rec)
    handler = _STRATEGIES.get(strategy_id)
    if handler is None:
        raise ValueError(f"未注册的评估策略: {strategy_id}")
    return handler(model_rec, df)


def _handler_pickle_tabular_regressor(model_rec: Model, df: pd.DataFrame) -> dict:
    if not model_rec.content:
        raise ValueError("pickle 评估需要 model.content 非空")
    model_obj = joblib.load(io.BytesIO(model_rec.content))
    r2 = evaluate_model_on_data(
        model_obj=model_obj,
        df=df,
        features=model_rec.features,
        target_col=model_rec.target,
    )
    return {"r2_score": r2}


def _handler_pipeline_bert_xgb_v2(model_rec: Model, df: pd.DataFrame) -> dict:
    # model_rec 预留：后续可按记录覆盖权重路径等
    _ = model_rec
    return evaluate_bert_xgb_v2_on_dataframe(df)


def _handler_pipeline_matscibert_xgb(model_rec: Model, df: pd.DataFrame) -> dict:
    _ = model_rec
    return evaluate_matscibert_xgb_on_dataframe(df)


def _register_builtin_strategies() -> None:
    register_evaluation_strategy("pickle_tabular_regressor", _handler_pickle_tabular_regressor)
    register_evaluation_strategy("pipeline_bert_xgb_v2", _handler_pipeline_bert_xgb_v2)
    register_evaluation_strategy("pipeline_matscibert_xgb", _handler_pipeline_matscibert_xgb)


_register_builtin_strategies()
