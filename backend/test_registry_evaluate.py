
import pickle
import json
from pathlib import Path
import pandas as pd
from sklearn.metrics import r2_score
from datetime import datetime

# ------------------------
# 配置路径
# ------------------------
model_file_path = r"D:\vueproject\Ti-design\backend\backend\data\models\simple_xgb\xgb_model.pkl"
dataset_path ="D:\\vueproject\Ti-design\\backend\data\datasets\system\\newdata3.csv"
save_base_dir = Path("backend/data/models")
save_base_dir.mkdir(parents=True, exist_ok=True)

# -----------------------------
# 1️⃣ 读取数据
# -----------------------------
df = pd.read_csv(dataset_path)

# 忽略 Process 和 source 列，只取数值特征和目标
feature_cols = [
    "Ti (wt%)","Mo (wt%)","Al (wt%)","Sn (wt%)","V (wt%)","Zr (wt%)",
    "Cr (wt%)","Nb (wt%)","Ta (wt%)","Fe (wt%)","W (wt%)","Si (wt%)",
    "O (wt%)","C (wt%)","N (wt%)","H (wt%)","Ni (wt%)","Cu (wt%)","B (wt%)",
    "Mn (wt%)","Y (wt%)","Zn (wt%)","transition temperature (°C)"
]
target_col = "Strength (MPa)"

X = df[feature_cols]
y = df[target_col]

# -----------------------------
# 2️⃣ 加载模型
# -----------------------------
with open(model_file_path, "rb") as f:
    model = pickle.load(f)

print("✅ Loaded model:", type(model))

# -----------------------------
# 3️⃣ 临时保存模型和 metadata
# -----------------------------
timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
model_dir = save_base_dir / f"model_{timestamp}"
model_dir.mkdir(parents=True, exist_ok=True)

# 保存模型
saved_model_path = model_dir / "model.pkl"
with open(saved_model_path, "wb") as f:
    pickle.dump(model, f)

# 创建 metadata
metadata = {
    "model_name": "simple_xgb",
    "features": feature_cols,
    "target": target_col,
    "framework": "xgboost",
    "model_format": "pickle",
    "created_at": timestamp
}

# 保存 metadata
metadata_path = model_dir / "metadata.json"
with open(metadata_path, "w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=2, ensure_ascii=False)

print(f"✅ Model saved to: {saved_model_path}")
print(f"✅ Metadata saved to: {metadata_path}")

# -----------------------------
# 4️⃣ 测试预测和评估
# -----------------------------
y_pred = model.predict(X)
score = r2_score(y, y_pred)

print(f"✅ Prediction complete. R² score: {score:.4f}")
print("First 10 predictions:", y_pred[:10])