import pandas as pd
import pickle
from xgboost import XGBRegressor
from pathlib import Path

# =============================
# 1. 读取数据集
# =============================
data_path = Path("D:\\vueproject\Ti-design\\backend\data\datasets\system\\newdata3.csv")
df = pd.read_csv(data_path)

# =============================
# 2. 选择特征和目标
# =============================
# 不使用 Process 列
features = [
    "Ti (wt%)","Mo (wt%)","Al (wt%)","Sn (wt%)","V (wt%)","Zr (wt%)",
    "Cr (wt%)","Nb (wt%)","Ta (wt%)","Fe (wt%)","W (wt%)","Si (wt%)",
    "O (wt%)","C (wt%)","N (wt%)","H (wt%)","Ni (wt%)","Cu (wt%)",
    "B (wt%)","Mn (wt%)","Y (wt%)","Zn (wt%)","transition temperature (°C)"
]
target = "Strength (MPa)"

X = df[features]
y = df[target]

# =============================
# 3. 训练简单 XGB 回归模型
# =============================
model = XGBRegressor(
    n_estimators=100,
    max_depth=3,
    learning_rate=0.1,
    random_state=42,
    objective="reg:squarederror"
)
model.fit(X, y)

# =============================
# 4. 保存模型
# =============================
save_dir = Path("backend/data/models/simple_xgb")
save_dir.mkdir(parents=True, exist_ok=True)

model_path = save_dir / "xgb_model.pkl"
with open(model_path, "wb") as f:
    pickle.dump(model, f)

print(f"✅ Model saved to: {model_path}")
