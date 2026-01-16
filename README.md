# 🧪 Ti-Design Platform
> 钛合金性能预测与逆向设计智能平台（Prototype System）

一个面向 **钛合金材料设计** 的智能化原型平台，集成了：

- ✅ 材料性能正向预测
  > 成分 + 工艺 → 抗拉强度、屈服强度、延伸率等性能预测
- ✅ 性能驱动的逆向设计
  > 目标性能 → 推荐可行成分 / 工艺组合
- ✅ 结果可视化与任务记录
- ✅ 多模型协同验证（传统 ML + 创新模型）

该平台用于验证 **机器学习驱动的材料智能设计流程**，支持算法对比、模型评估和平台化展示。

---

## 📌 项目背景

钛合金因其优异的强度、耐腐蚀性和生物相容性，被广泛应用于航空航天、生物医疗和高端制造领域。
传统材料设计依赖大量实验试错，周期长、成本高。

本项目尝试引入：

- 数据驱动建模
- 机器学习性能预测
- 目标性能约束的逆向设计
- 可视化平台集成

构建一个可扩展的 **钛合金智能设计原型平台**。

---

## 🧱 系统架构
Frontend (Vue3 + Vite + Element Plus + ECharts)
|
| REST API (Axios)
|
Backend (FastAPI + Pydantic)
|
| ML Models (RF / XGBoost / SVM / MLP / LightGBM ...)
|
Dataset / Feature Engineering


---

## ⚙️ 技术栈

### 🔹 前端
- Vue 3
- Vite
- Element Plus
- ECharts
- Axios

### 🔹 后端
- FastAPI
- RESTful API
- Pydantic

### 🔹 算法
- Random Forest
- XGBoost
- LightGBM
- SVM
- MLP
- 特征工程与数据增强方法

---

## 🚀 功能模块

### 1️⃣ 性能正向预测模块
- 输入：
    - 化学成分（Ti, Al, V, Mo, Nb, ...）
    - 工艺参数（热处理、热加工等，可选）
- 输出：
    - 抗拉强度
    - 屈服强度
    - 延伸率
    - 预测置信度（可扩展）

---

### 2️⃣ 逆向设计模块
- 输入：
    - 目标性能区间
- 输出：
    - 可行成分组合推荐
    - 工艺参数建议
    - 多解对比与排序

---

### 3️⃣ 可视化与任务管理
- 参数表单交互
- 预测结果图表展示
- 多次实验结果对比
- 任务记录与导出（规划中）

---

## 🛠️ 本地运行

### ✅ 前端启动

```bash
cd fronted
npm install
npm run dev
```

### 浏览器访问：

http://localhost:5173

✅ 后端启动
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

接口地址：

http://127.0.0.1:8000

📁 项目结构示例
```bash
Ti-design
├── fronted/                 # 前端工程
│   ├── src/
│   ├── styles/
│   └── vite.config.js
├── backend/                 # 后端接口
│   ├── main.py
│   ├── models/
│   └── services/
├── dataset/                 # 数据集
├── experiments/             # 实验脚本
└── README.md
```