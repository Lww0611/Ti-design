import os
from pathlib import Path

# 1. 动态获取 backend 根目录 (D:\vueproject\Ti-design\backend)
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. 定义统一的数据根目录，不要再手动写 "backend" 字符串
# 修改前：DATA_DIR = BASE_DIR / "backend" / "data" (这会导致嵌套)
# 修改后：
DATA_DIR = BASE_DIR / "data"

# 3. 具体业务目录
SYSTEM_DATASET_DIR = DATA_DIR / "datasets" / "system"
SYSTEM_DATASET_PATH = SYSTEM_DATASET_DIR / "newdata3.csv"
MODEL_SAVE_DIR = DATA_DIR / "models"

# 确保必要的目录存在
SYSTEM_DATASET_DIR.mkdir(parents=True, exist_ok=True)