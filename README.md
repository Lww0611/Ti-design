# Ti-Design

钛合金性能预测与逆向设计原型平台：Vue 3 前端 + FastAPI 后端，REST API 位于 `/api/v1`。

---

## 环境要求

| 组件 | 说明 |
|------|------|
| **Node.js** | 建议 **18 LTS 或 20 LTS**（需自带 `npm`） |
| **Python** | 建议 **3.10 或 3.11**（与 `torch==2.5.1` 等依赖一致） |
| **MySQL** | 本地开发默认使用 MySQL 8.x（见下文连接串） |

---

## 1. 准备数据库（必做）

后端启动时会连库并执行建表、导入内置数据；**数据库未就绪会直接启动失败**。

1. 安装并启动 MySQL。
2. 创建空库（名称需与连接串一致）：

```sql
CREATE DATABASE ti_alloy_ai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

3. 默认连接（未设置环境变量时）见 `backend/db/session.py`：

   `mysql+pymysql://root:root@127.0.0.1:3306/ti_alloy_ai`

若本机账号不是 `root` / 密码不是 `root`，在启动后端前设置：

```bash
export DATABASE_URL="mysql+pymysql://你的用户:你的密码@127.0.0.1:3306/ti_alloy_ai"
```

调试 SQL 时可（可选）：

```bash
export DB_ECHO=true
```

---

## 2. 启动后端

在仓库根目录执行（路径按你本机克隆位置调整）：

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

依赖里含 **PyTorch**，首次安装可能较慢。请保持 **`requirements.txt` 中的 `xgboost>=2.1.4`**：与 `scikit-learn==1.6.1` 配套，否则部分模型（含 BERT-v3 的 XGB 分支）在 `predict` 时会报错。

启动 API（**务必**排除虚拟环境目录，避免热重载不断扫描 `site-packages`）：

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000 --reload-exclude '.venv'
```

- 接口根地址：http://127.0.0.1:8000  
- Swagger：http://127.0.0.1:8000/docs  
- 业务路由前缀：`/api/v1`

可选环境变量（见 `backend/main.py`）：

- `HOST` / `PORT`：使用 `python main.py` 时生效；默认 `0.0.0.0:8000`，本地开发若用 `python main.py` 可设 `RELOAD=true` 开启热重载。
- `CORS_ORIGINS`：生产环境建议设为前端域名列表，逗号分隔；本地默认 `*` 即可。

---

## 3. 启动前端

**新开一个终端**：

```bash
cd fronted
npm install
npm run dev
```

- 开发地址：http://localhost:5173（端口见 `fronted/vite.config.js`）

未配置时，开发模式下前端默认请求 **http://127.0.0.1:8000**（见 `fronted/src/config/api.js`）。若后端不在本机 8000 端口，可复制 `fronted/.env.example` 为 `.env.development` 并修改 `VITE_API_ORIGIN`。

---

## 4. 自检清单

按顺序确认：

1. MySQL 已启动，且已创建 `ti_alloy_ai`（或你已正确设置 `DATABASE_URL`）。
2. 后端终端无报错，浏览器能打开 http://127.0.0.1:8000/docs 。
3. 前端能打开 http://localhost:5173 ，且浏览器控制台无大面积跨域或连不上 API 的错误。

---

## 5. BERT-v3 与 TensorFlow（仅在使用该模型时需要）

BERT-v3 会**子进程**调用 `backend/models/legacy_bert_runtime/extract_features.py`，依赖 **带 `tf.compat.v1.estimator` 的 TensorFlow**（一般需 **TensorFlow 低于 2.16**，例如 2.13～2.15 线）。主虚拟环境里的 `torch` 与独立 TF 环境分开即可。

1. 在 `backend` 下单独建一个仅用于 BERT 子进程的虚拟环境（示例名 `.tfenv`），安装例如：`pip install "tensorflow>=2.13,<2.16"`（版本需与本机 CPU/GPU 轮子匹配）。
2. 指定解释器（优先于自动探测）：

```bash
export BERT_V3_TF_PYTHON="/绝对路径/Ti-design/backend/.tfenv/bin/python"
```

再启动 `uvicorn`。若未设置，代码会依次尝试当前 `sys.executable`、`BERT_V3_TF_PYTHON`、`backend/.tfenv/bin/python` 等路径，**第一个能 `import tensorflow` 成功的**即被采用（见 `backend/models/forward/bert_v3_model.py`）。

若日志里出现 HuggingFace `tokenizers` 与 fork 的提示，可忽略或设置：

```bash
export TOKENIZERS_PARALLELISM=false
```

---

## 6. 常见问题

| 现象 | 处理 |
|------|------|
| `WatchFiles detected changes in '.venv/...'` 刷屏、不停 Reload | 使用上文 `--reload-exclude '.venv'`，或把 venv 建到 `backend` 目录外。 |
| `'super' object has no attribute '__sklearn_tags__'` | 升级 XGBoost：`pip install "xgboost>=2.1.4,<3"`，与当前 `requirements.txt` 一致后重装依赖。 |
| `tf.compat.v1` 没有 `estimator` | BERT-v3 子进程用的 TensorFlow 过新，换 **TF 2.13–2.15** 环境并设 `BERT_V3_TF_PYTHON`。 |
| 数据库连接失败 | 检查 MySQL 是否监听、`DATABASE_URL` 用户名密码库名是否与实例一致。 |

---

## 7. 生产构建（前端）

生产构建**必须**配置 API 根地址，否则打包后仍可能指向 `127.0.0.1`：

在部署平台设置环境变量 **`VITE_API_ORIGIN`**（无尾斜杠），例如 `https://你的后端域名`，**重新构建**后生效。说明见 `fronted/.env.example`。

---

## 8. 技术栈与目录结构

**前端**：Vue 3、Vite、Element Plus、ECharts、Axios。  
**后端**：FastAPI、Pydantic、SQLAlchemy；机器学习侧含 scikit-learn、XGBoost、PyTorch 等（以 `backend/requirements.txt` 为准）。

```
Ti-design
├── fronted/          # 前端（目录名为 fronted）
├── backend/          # 后端 API、模型权重与脚本
│   ├── main.py
│   ├── api/
│   ├── db/
│   ├── models/
│   └── requirements.txt
├── dataset/          # 数据集（如有）
└── experiments/      # 实验脚本（如有）
```

---

## 9. 功能概览

- **正向预测**：成分与工艺等输入 → 强度、延伸率等预测。  
- **逆向设计**：目标性能区间 → 推荐成分 / 工艺组合（见前端对应页面）。  
- **多模型**：可在界面中选择不同已注册模型；部分模型依赖额外权重或上述 BERT/TF 环境。

按 **第二节 → 第三节** 顺序操作，并满足数据库与依赖版本要求，即可在本地稳定跑通主流程。
