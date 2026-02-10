# services/model_service/evaluator.py

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score


def evaluate_model_on_csv(
    model,
    csv_path: str,
    target_col: str,
    test_size: float = 0.2,
    random_state: int = 42
) -> float:
    """
    使用 CSV 数据评估模型，返回 R²
    """

    df = pd.read_csv(csv_path)

    if target_col not in df.columns:
        raise ValueError(f"Target column {target_col} not in dataset")

    X = df.drop(columns=[target_col])
    y = df[target_col]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=random_state
    )

    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    return float(r2_score(y_test, y_pred))
