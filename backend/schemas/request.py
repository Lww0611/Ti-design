from pydantic import BaseModel
from typing import Dict, List, Optional

# --- 支撑模型：保持原始嵌套逻辑 ---

class HotWorking(BaseModel):
    enabled: bool
    type: str
    temperature: float
    deformation: float
    passes: int

class HTStage(BaseModel):
    type: str
    temperature: float
    duration: float
    coolingMode: str

class HeatTreatment(BaseModel):
    enabled: bool
    stages: List[HTStage]

# --- 主请求模型 ---

class PredictRequest(BaseModel):
    elements: Dict[str, float]
    hotWorking: HotWorking

    # 模式：'structured' (数值设定) 或 'text' (文本输入)
    heatTreatmentMode: str = 'structured'

    # 模式 A: 数值设定
    heatTreatment: Optional[HeatTreatment] = None

    # 模式 B: 文本输入
    heatTreatmentText: Optional[str] = None

    # 用户选择的模型列表
    selectedModels: List[str] = []

class InverseRequest(BaseModel):
    # 约束是范围 [min, max]
    constraints: Dict[str, List[float]]

    # 目标属性
    targetRm: List[float]
    targetA: List[float]

    strategy: str = 'balanced'