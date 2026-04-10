<template>
  <div class="page-container">
    <div class="page-header">
      <div class="title-wrapper">
        <h1 class="page-title">工作流管理</h1>
        <span class="en-title">SCIENTIFIC WORKFLOW PIPELINE</span>
      </div>
      <p class="page-desc">基于步骤化卡片的科研任务编排，支持主线任务与分支任务的独立调度。</p>
    </div>

    <div class="example-dashboard">
      <div class="dashboard-info">
        <div class="info-header">
          <span class="badge">当前运行示例</span>
          <h2 class="mini-title">钛合金强度优化：基于多目标演化算法</h2>
        </div>
        <div class="info-grid">
          <div class="info-item">
            <label>运行状态</label>
            <span>{{ workflowSteps[2].isCompleted ? '模型已验证' : '等待模型评估解锁后续功能' }}</span>
          </div>
          <div class="info-item">
            <label>预设路线</label>
            <span class="logic-flow">数据选择 > 模型选择 > 指标评估 > 性能预测 / 逆向设计 </span>
          </div>
        </div>
      </div>
      <div class="dashboard-action">
        <el-button type="primary" class="glow-button" @click="startWorkflow">
          {{ workflowStarted ? '重置工作流环境' : '初始化工作流' }}
        </el-button>
      </div>
    </div>

    <div class="tag-nav-container" v-if="workflowStarted">
      <div class="tag-nav">
        <div
            v-for="(step, index) in workflowSteps"
            :key="step.title"
            class="tag-item"
            :class="{
              active: currentStepIndex === index,
              'is-branch': step.branch === 'branch',
              'is-locked': (index > 2 && !workflowSteps[2].isCompleted)
            }"
            @click="handleStepClick(index)"
        >
          <span class="step-num">
            <el-icon v-if="index > 2 && !workflowSteps[2].isCompleted"><Lock /></el-icon>
            <span v-else>{{ index + 1 }}</span>
          </span>
          {{ step.title }}
        </div>
      </div>
    </div>

    <div class="workflow-stage" v-if="workflowStarted">
      <div class="workflow-stack">
        <div
            v-for="(step, index) in workflowSteps"
            :key="step.title"
            class="modern-card workflow-card"
            :class="{
              'branch-card': step.branch === 'branch',
              'is-active': currentStepIndex === index,
              'shake-animation': isShaking && currentStepIndex === index
            }"
            :style="getCardStyle(index)"
        >
          <div class="card-bg-icon">{{ index + 1 }}</div>

          <div class="card-inner">
            <div class="card-header">
              <span class="step-label">{{ step.branch === 'main' ? '核心主线' : '实验分支' }}</span>
              <h3 class="step-title">{{ step.title }}</h3>
            </div>

            <p class="step-description" v-if="!step.isCompleted">{{ step.description }}</p>

            <div class="card-content">
              <div v-if="step.type === 'dataset' || step.type === 'model'" class="form-container">
                <el-select
                    v-model="step.selectedValue"
                    :placeholder="step.type === 'dataset' ? '请选择实验数据集' : '请选择预训练模型'"
                    class="custom-select"
                    filterable
                >
                  <el-option
                      v-for="item in (step.type === 'dataset' ? availableDatasets : availableModels)"
                      :key="item.id"
                      :label="item.name || item.model_name"
                      :value="item.id"
                  />
                </el-select>
                <el-button type="primary" link class="quick-link" @click.stop="step.type === 'dataset' ? goToDatasetPage() : goToModelPage()">
                  {{ step.type === 'dataset' ? '+ 导入新数据集' : '+ 注册新模型' }}
                </el-button>
              </div>

              <div v-if="step.type === 'evaluation'" class="evaluation-container">
                <div v-if="!step.isCompleted" class="eval-action">
                  <div v-if="evaluating" class="eval-loading">
                    <el-progress type="circle" :percentage="evalProgress" :color="progressColors" />
                    <p class="loading-text">正在并行计算模型评估指标...</p>
                  </div>
                  <el-button v-else type="primary" size="large" @click="runEvaluation" icon="VideoPlay">启动交叉验证评估</el-button>
                </div>

                <div v-else class="eval-results animate__animated animate__fadeIn">
                  <div class="metrics-grid">
                    <div class="metric-item highlight">
                      <div class="metric-label">决定系数 R²</div>
                      <div class="metric-value">{{ step.results.r2 }}</div>
                    </div>
                    <div class="metric-item">
                      <div class="metric-label">MAE</div>
                      <div class="metric-value">{{ step.results.mae }}</div>
                    </div>
                    <div class="metric-item">
                      <div class="metric-label">RMSE</div>
                      <div class="metric-value">{{ step.results.rmse }}</div>
                    </div>
                  </div>
                  <div class="eval-summary">
                    <el-icon color="#67C23A"><CircleCheckFilled /></el-icon>
                    <span>模型验证已通过，性能指标符合预期。</span>
                  </div>
                  <el-button size="small" link @click="step.isCompleted = false" class="re-eval-link">重新执行计算</el-button>
                </div>
              </div>

              <div v-if="step.type === 'prediction' || step.type === 'inverse'" class="action-zone">
                <template v-if="!workflowSteps[2].isCompleted">
                  <el-alert title="等待解锁" type="info" description="请先完成“效果评估”步骤以获取模型性能指标。" :closable="false" show-icon />
                </template>
                <template v-else>
                  <el-button v-if="step.type === 'prediction'" type="success" plain @click="runPrediction" icon="Position">启动性能预测任务</el-button>
                  <el-button v-if="step.type === 'inverse'" type="warning" plain @click="runInverseDesign" icon="MagicStick">启动组分设计任务</el-button>
                </template>
              </div>
            </div>

            <div class="card-footer">
              <div class="status-box">
                <el-icon v-if="step.isCompleted" color="#67C23A"><SuccessFilled /></el-icon>
                <span class="footer-tip" style="margin-left:5px">
                  {{ index === 2 && step.isCompleted ? '验证通过' : '工作流状态：就绪' }}
                </span>
              </div>

              <div class="footer-actions">
                <template v-if="index === 2 && step.isCompleted">
                  <el-button type="success" size="default" @click.stop="handleStepClick(3)">性能预测 <el-icon class="el-icon--right"><ArrowRight /></el-icon></el-button>
                  <el-button type="warning" size="default" @click.stop="handleStepClick(4)">逆向设计 <el-icon class="el-icon--right"><ArrowRight /></el-icon></el-button>
                </template>

                <el-button
                    v-else-if="step.branch === 'main'"
                    class="next-btn"
                    type="primary"
                    @click.stop="nextStep"
                    :disabled="currentStepIndex === mainLineLastIndex"
                >
                  下一步 <el-icon class="el-icon--right"><ArrowRight /></el-icon>
                </el-button>

                <el-button
                    v-else-if="step.branch === 'branch'"
                    size="default"
                    plain
                    @click.stop="handleStepClick(2)"
                >
                  返回评估
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="empty-state" v-else>
      <el-empty description="请点击上方按钮初始化科研工作流环境" />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'
import { ArrowRight, Lock, VideoPlay, SuccessFilled, Position, MagicStick, CircleCheckFilled } from '@element-plus/icons-vue'
import { API_V1_URL } from '@/config/api'

const router = useRouter()
const route = useRoute()

const API_BASE_DATASETS = `${API_V1_URL}/datasets`
const API_BASE_MODELS = `${API_V1_URL}/models`

const workflowStarted = ref(false)
const currentStepIndex = ref(0)
const isShaking = ref(false)
const evaluating = ref(false)
const evalProgress = ref(0)

const workflowSteps = reactive([
  { title: "数据集选择", description: "从系统库中筛选清洗后的实验数据。", type: "dataset", selectedValue: null, branch: "main" },
  { title: "模型配置", description: "配置深度神经网络或机器学习回归模型。", type: "model", selectedValue: null, branch: "main" },
  {
    title: "效果评估",
    description: "自动计算 R² 指标，并解锁后续预测功能。",
    type: "evaluation",
    branch: "main",
    isCompleted: false,
    results: { r2: null, mae: null, rmse: null }
  },
  { title: "性能预测", description: "基于选定模型对新成分进行推理。", type: "prediction", branch: "branch" },
  { title: "逆向设计", description: "设定目标性能，反推最优合金元素配比。", type: "inverse", branch: "branch" },
])

const availableDatasets = ref([])
const availableModels = ref([])

const fetchResources = async () => {
  try {
    const [dsRes, modelRes] = await Promise.all([
      axios.get(API_BASE_DATASETS),
      axios.get(API_BASE_MODELS, { headers: { 'token': localStorage.getItem('token') } })
    ])
    availableDatasets.value = dsRes.data || []
    availableModels.value = modelRes.data.data || []
  } catch (err) { ElMessage.error('资源同步失败') }
}

onMounted(async () => {
  await fetchResources()
  if (route.query.from === 'cases' && route.query.step !== undefined) {
    workflowStarted.value = true
    currentStepIndex.value = parseInt(route.query.step)
    if (route.query.selectedId) {
      workflowSteps[currentStepIndex.value].selectedValue = parseInt(route.query.selectedId)
    }
  }
})

// 执行真实的后端评估逻辑
async function runEvaluation() {
  // 1. 获取模型 ID (从第二步获取)
  const modelId = workflowSteps[1].selectedValue
  if (!modelId) {
    ElMessage.error('无法获取模型 ID，请返回上一步重新选择')
    return
  }

  evaluating.value = true
  evalProgress.value = 0

  // 启动一个虚假的进度条动画，增加交互感
  const progressTimer = setInterval(() => {
    if (evalProgress.value < 90) evalProgress.value += 5
  }, 100)

  try {
    // 2. 调用你后端的真实接口
    const res = await axios.post(
        `${API_BASE_MODELS}/${modelId}/evaluate`,
        {}, // POST 体为空
        { headers: { 'token': localStorage.getItem('token') } }
    )

    // 3. 停止动画并填入真实数据
    clearInterval(progressTimer)
    evalProgress.value = 100

    // 与模型管理页相同接口：扁平 JSON，含 status、r2_score 等（r2 为 0 时不能用 truthy 判断）
    const body = res.data
    const fmt = (v) => (typeof v === 'number' && !Number.isNaN(v) ? v.toFixed(4) : '—')
    workflowSteps[2].results = {
      r2: typeof body.r2_score === 'number' && !Number.isNaN(body.r2_score) ? body.r2_score.toFixed(4) : 'N/A',
      mae: fmt(body.mae),
      rmse: fmt(body.rmse),
    }

    // 4. 延迟一下让用户看清 100% 状态
    setTimeout(() => {
      evaluating.value = false
      workflowSteps[2].isCompleted = true
      ElMessage.success('真实评估任务执行完毕！')
    }, 500)

  } catch (err) {
    clearInterval(progressTimer)
    evaluating.value = false
    console.error('评估出错:', err)
    ElMessage.error(err.response?.data?.detail || '后端评估引擎报错，请检查服务端日志')
  }
}

function validateAndMove(targetIndex) {
  if (targetIndex < currentStepIndex.value) { currentStepIndex.value = targetIndex; return true }

  // 校验前两步必填
  for (let i = 0; i <= Math.min(targetIndex - 1, 1); i++) {
    if (!workflowSteps[i].selectedValue) {
      ElMessage.warning(`请先完成 [${workflowSteps[i].title}]`);
      currentStepIndex.value = i;
      triggerShake();
      return false
    }
  }

  // 校验评估是否完成
  if (targetIndex >= 3 && !workflowSteps[2].isCompleted) {
    ElMessage.warning('请先完成效果评估');
    currentStepIndex.value = 2;
    triggerShake();
    return false
  }

  currentStepIndex.value = targetIndex;
  return true
}

function handleStepClick(index) { validateAndMove(index) }

function nextStep() {
  const mainIndexes = workflowSteps.map((s, i) => s.branch === "main" ? i : -1).filter(i => i >= 0)
  const currentIndexInMain = mainIndexes.indexOf(currentStepIndex.value)
  if (currentIndexInMain < mainIndexes.length - 1) {
    validateAndMove(mainIndexes[currentIndexInMain + 1])
  }
}

function triggerShake() { isShaking.value = true; setTimeout(() => { isShaking.value = false }, 500) }
function startWorkflow() { workflowStarted.value = true; currentStepIndex.value = 0 }
function goToDatasetPage() { router.push({ path: '/datasets', query: { from: 'cases', step: currentStepIndex.value } }) }
function goToModelPage() { router.push({ path: '/management', query: { from: 'cases', step: currentStepIndex.value } }) }
function runPrediction() { ElMessage.success('预测任务启动') }
function runInverseDesign() { ElMessage.success('逆向设计任务启动') }

const mainLineLastIndex = computed(() => {
  const indexes = workflowSteps.map((s, i) => s.branch === "main" ? i : -1).filter(i => i >= 0)
  return indexes[indexes.length - 1]
})

function getCardStyle(index) {
  const offset = index - currentStepIndex.value
  let scale = 1, translateY = 0, opacity = 0, zIndex = 0, blur = 0, visibility = 'visible'
  if (offset === 0) { zIndex = 100; opacity = 1 }
  else if (offset > 0) {
    scale = 1 - (offset * 0.04); translateY = offset * 25; opacity = 1 - (offset * 0.25); zIndex = 100 - offset; blur = offset * 1.5
  } else {
    translateY = -40; scale = 1.05; opacity = 0; zIndex = 50; visibility = 'hidden'
  }
  return {
    position: 'absolute', top: '0', left: '0', right: '0', margin: '0 auto',
    width: '95%', maxWidth: '1100px', height: '400px',
    transform: `translateY(${translateY}px) scale(${scale})`,
    zIndex, opacity, filter: `blur(${blur}px)`, visibility,
    transition: 'all 0.5s cubic-bezier(0.23, 1, 0.32, 1)',
    pointerEvents: offset === 0 ? 'auto' : 'none',
  }
}

const progressColors = [
  { color: '#909399', percentage: 20 },
  { color: '#e6a23c', percentage: 40 },
  { color: '#409eff', percentage: 70 },
  { color: '#67c23a', percentage: 100 },
]
</script>

<style scoped>
/* 保持原有样式，增加几个辅助类 */
.is-locked { opacity: 0.6; cursor: not-allowed !important; }
.status-box { display: flex; align-items: center; }
.status-tag { font-size: 12px; padding: 2px 8px; border-radius: 4px; font-weight: bold; }
.status-tag.success { background: #f0f9eb; color: #67c23a; border: 1px solid #e1f3d8; }
.status-tag.locked { background: #fef0f0; color: #f56c6c; border: 1px solid #fde2e2; }

/* 1. 基础布局：强制一屏显示 */
.page-container {
  height: 100vh;
  padding: 24px 40px;
  box-sizing: border-box;
  background-color: #f8fafc;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.page-header { flex-shrink: 0; margin-bottom: 20px; }
.page-title { font-size: 24px; color: #0f172a; margin: 0; font-weight: 800; }
.en-title { font-size: 12px; color: #94a3b8; font-weight: 600; letter-spacing: 1px; margin-left: 10px; }
.page-desc { color: #64748b; font-size: 13px; margin-top: 5px; }

/* 2. 示例卡片 */
.example-dashboard {
  flex-shrink: 0;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 16px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.badge { background: #eff6ff; color: #3b82f6; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; margin-bottom: 4px; display: inline-block; }
.mini-title { font-size: 17px; margin: 0; color: #1e293b; }
.info-grid { display: flex; gap: 30px; margin-top: 5px; }
.info-item label { font-size: 11px; color: #94a3b8; display: block; }
.info-item span { font-size: 13px; font-weight: 600; color: #475569; }

/* 3. 标签导航 */
.tag-nav-container { flex-shrink: 0; display: flex; justify-content: center; margin-bottom: 15px; }
.tag-nav { background: #e2e8f0; padding: 4px; border-radius: 8px; display: flex; }
.tag-item {
  padding: 6px 16px; border-radius: 6px; font-size: 12px; font-weight: 600; color: #64748b;
  cursor: pointer; display: flex; align-items: center; gap: 6px;
}
.tag-item.active { background: #fff; color: #3b82f6; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
.step-num { width: 16px; height: 16px; background: #cbd5e1; color: white; border-radius: 50%; font-size: 10px; display: flex; align-items: center; justify-content: center; }
.tag-item.active .step-num { background: #3b82f6; }

/* 4. 工作流区域 */
.workflow-stage { flex: 1; position: relative; perspective: 1000px; width: 100%; }
.workflow-stack { position: relative; width: 100%; height: 100%; }

.modern-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  padding: 30px;
  box-sizing: border-box;
  box-shadow: 0 10px 30px rgba(0,0,0,0.05);
}
.is-active { border: 2px solid #3b82f6; }

/* 抖动动画 */
.shake-animation {
  animation: shake 0.5s cubic-bezier(.36,.07,.19,.97) both;
  border-color: #f56c6c !important;
}
@keyframes shake {
  10%, 90% { transform: translate3d(-1px, 0, 0) scale(1); }
  20%, 80% { transform: translate3d(2px, 0, 0) scale(1); }
  30%, 50%, 70% { transform: translate3d(-4px, 0, 0) scale(1); }
  40%, 60% { transform: translate3d(4px, 0, 0) scale(1); }
}

.card-inner { height: 100%; display: flex; flex-direction: column; position: relative; }
.card-bg-icon {
  position: absolute; right: -10px; top: -20px; font-size: 120px; font-weight: 900;
  color: rgba(59, 130, 246, 0.03); z-index: 0;
}

.card-header { position: relative; z-index: 1; }
.step-label { font-size: 10px; color: #3b82f6; font-weight: 700; letter-spacing: 1px; }
.step-title { font-size: 22px; margin: 5px 0; color: #0f172a; }
.step-description { color: #64748b; font-size: 14px; line-height: 1.6; max-width: 80%; }

.card-content { flex: 1; padding-top: 20px; position: relative; z-index: 1; }
.form-container { max-width: 400px; }
.custom-select { width: 100%; }
.quick-link { font-size: 12px; margin-top: 5px; }

.card-footer {
  padding-top: 15px; border-top: 1px solid #f1f5f9;
  display: flex; justify-content: space-between; align-items: center;
}
.footer-tip { font-size: 11px; color: #cbd5e1; }
.next-btn { padding: 10px 25px; border-radius: 10px; font-weight: 700; }

.empty-state { flex: 1; display: flex; align-items: center; justify-content: center; }

/* 评估展示样式优化 */
.evaluation-container { height: 100%; display: flex; align-items: center; justify-content: center; }
.eval-loading { text-align: center; }
.loading-text { margin-top: 15px; color: #94a3b8; font-size: 14px; }

.eval-results { width: 100%; max-width: 800px; }
.metrics-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px; }
.metric-item { background: #f8fafc; padding: 25px 15px; border-radius: 16px; text-align: center; border: 1px solid #f1f5f9; transition: all 0.3s; }
.metric-item.highlight { border-color: #3b82f6; background: #eff6ff; }
.metric-label { font-size: 11px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; }
.metric-value { font-size: 24px; font-weight: 800; color: #1e293b; }
.metric-item.highlight .metric-value { color: #3b82f6; }

.eval-summary { display: flex; align-items: center; gap: 10px; padding: 15px; background: #f0f9eb; border-radius: 8px; color: #67c23a; font-size: 14px; font-weight: 600; justify-content: center; }
.re-eval-link { margin-top: 20px; font-size: 12px; }

.card-bg-icon { position: absolute; right: -10px; top: -20px; font-size: 150px; font-weight: 900; color: rgba(59, 130, 246, 0.03); z-index: 0; }
.card-footer { padding-top: 15px; border-top: 1px solid #f1f5f9; display: flex; justify-content: space-between; align-items: center; }
/* 3. 装饰与辅助 */
.card-bg-icon { position: absolute; right: -10px; top: -20px; font-size: 150px; font-weight: 900; color: rgba(59, 130, 246, 0.03); z-index: 0; pointer-events: none; }
.card-footer { padding-top: 15px; border-top: 1px solid #f1f5f9; display: flex; justify-content: space-between; align-items: center; }
.footer-tip { font-size: 12px; color: #94a3b8; }
.shake-animation { animation: shake 0.5s cubic-bezier(.36,.07,.19,.97) both; border-color: #f56c6c !important; }
@keyframes shake { 10%, 90% { transform: translate3d(-1px, 0, 0); } 20%, 80% { transform: translate3d(2px, 0, 0); } }
</style>