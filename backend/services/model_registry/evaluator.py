import pandas as pd
from sklearn.metrics import r2_score

def evaluate_model_on_data(model_obj, df: pd.DataFrame, features: list, target_col: str):
    """
    核心评估逻辑：传入模型对象、DataFrame、特征列表和目标列名
    """
    if target_col not in df.columns:
        raise ValueError(f"目标列 {target_col} 不在数据集中")

    # 执行精准切片
    X = df[features]
    y = df[target_col]

    # 执行预测
    y_pred = model_obj.predict(X)

    # 计算评分
    return float(r2_score(y, y_pred))