from pydantic import BaseModel
from typing import Dict, List, Optional

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

class PredictRequest(BaseModel):
    elements: Dict[str, float]
    hotWorking: HotWorking
    
    # 模式：'structured' (数值设定) 或 'text' (文本输入)
    heatTreatmentMode: str = 'structured' 
    
    # 模式 A: 原有的数值设定
    heatTreatment: Optional[HeatTreatment] = None
    
    # 模式 B: 新增文本输入
    heatTreatmentText: Optional[str] = None
    
    # 用户选择的模型列表
    selectedModels: List[str] = []

# --- 修改这里 ---
class InverseRequest(BaseModel):
    # 约束是范围，所以是 List[float] (例如 [min, max])
    constraints: Dict[str, List[float]]

    # 前端发的是 targetRm 和 targetA
    targetRm: List[float]
    targetA: List[float]

    strategy: str = 'balanced'
