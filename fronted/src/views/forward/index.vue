<template>
  <div class="page-container">
    <!-- 顶部标题 (固定高度) -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">性能正向预测 <span class="en-title">Performance Prediction</span></h1>
        <p class="page-desc">基于多模型协同算法，精准预测钛合金在不同成分与工艺下的力学性能。</p>
      </div>
    </div>

    <!-- 主体内容 (自适应剩余高度) -->
    <div class="main-content">
      <el-row :gutter="20" class="full-height-row">
        <!-- 左侧：参数配置 -->
        <el-col :span="11" class="full-height-col">
          <div class="modern-card input-card">
            <div class="card-header-bar">
              <span class="header-title">参数配置</span>
              <span class="header-subtitle">Configuration</span>
            </div>

            <!-- 滚动区域：仅在此处出现滚动条 -->
            <div class="card-body scrollable-y">
              <el-form :model="form" label-position="top" class="modern-form">

                <!-- 1. 化学成分模块 -->
                <div class="form-section">
                  <div class="section-title">
                    <span class="icon-box blue-icon"><el-icon><Operation /></el-icon></span>
                    化学成分 (wt.%)
                  </div>
                  <div class="elements-grid">
                    <el-row :gutter="10">
                      <el-col :span="8" v-for="(range, el) in elementConfig" :key="el" class="element-col">
                        <div class="element-item-compact">
                          <span class="el-name">{{ el }}</span>
                          <el-input-number
                              v-model="form.elements[el]"
                              :precision="range.p"
                              :step="range.s"
                              :min="0"
                              :max="range.max"
                              controls-position="right"
                              size="small"
                              class="mini-input"
                          />
                        </div>
                      </el-col>
                    </el-row>
                  </div>
                </div>

                <!-- 下半部分：工艺参数 + 模型选择 -->
                <el-row :gutter="16">
                  <!-- 左列：工艺参数 -->
                  <el-col :span="14">
                    <div class="form-section">
                      <div class="section-title">
                        <span class="icon-box purple-icon"><el-icon><Tools /></el-icon></span>
                        工艺参数配置
                      </div>

                      <div class="process-mode-content text-mode-panel">
                        <el-input
                          v-model="form.heatTreatmentText"
                          type="textarea"
                          :rows="10"
                          resize="none"
                          placeholder="请输入热处理参数文本，例如：solution 950C 1h WQ; aging 550C 6h AC"
                          class="custom-textarea"
                        />
                      </div>
                    </div>
                  </el-col>

                  <!-- 右列：模型选择 + 按钮 -->
                  <el-col :span="10" class="right-col-flex">
                    <div class="form-section full-height-section">
                      <div class="section-title">
                        <span class="icon-box green-icon"><el-icon><Cpu /></el-icon></span>
                        模型选择
                      </div>

                      <div class="model-select-container">
                        <el-checkbox-group v-model="form.selectedModels" class="vertical-checkbox-group">
                          <el-checkbox label="BERT-XGB-v2" border size="default" class="model-checkbox-block">
                            BERT-XGB-v2
                          </el-checkbox>
                        </el-checkbox-group>
                      </div>

                      <div class="predict-btn-wrapper">
                        <el-button class="predict-btn" type="primary" size="large" @click="handlePredict" :loading="loading">
                          启动预测
                        </el-button>
                      </div>
                    </div>
                  </el-col>
                </el-row>

              </el-form>
            </div>
          </div>
        </el-col>

        <!-- 右侧：结果展示 -->
        <el-col :span="13" class="full-height-col">
          <div class="modern-card result-card">
            <div class="card-header-bar">
              <span class="header-title">预测结果评估</span>
              <span class="header-subtitle">Evaluation</span>
            </div>

            <!-- 右侧卡片内容区：Flex 纵向布局，防止图表被挤出 -->
            <div class="card-body no-padding result-layout">

              <!-- 上半部分：表格 (限制高度，内部滚动) -->
              <div class="result-table-section">
                <transition name="el-fade-in">
                  <div v-if="predictionResults && predictionResults.length > 0" class="table-inner-container">
                    <el-table
                        :data="predictionResults"
                        style="width: 100%"
                        :header-cell-style="{background:'#f8fafc', color:'#64748b'}"
                        border
                        size="small"
                    >
                      <el-table-column prop="model" label="模型" width="120">
                        <template #default="scope">
                          <el-tag size="small" effect="plain">{{ scope.row.model }}</el-tag>
                        </template>
                      </el-table-column>

                      <!-- 抗拉强度 -->
                      <el-table-column label="抗拉强度(MPa)" align="center">
                        <template #default="scope">
                          <span class="value-text">{{ scope.row.strength }}</span>
                        </template>
                      </el-table-column>

                      <!-- 延伸率 -->
                      <el-table-column label="延伸率(%)" align="center">
                        <template #default="scope">
                          <span class="value-text">{{ scope.row.elongation }}</span>
                        </template>
                      </el-table-column>

<!--                      &lt;!&ndash; 可选：误差值，数据库暂不存 &ndash;&gt;-->
<!--                      <el-table-column label="抗拉强度误差" align="center">-->
<!--                        <template #default="scope">-->
<!--                          <span class="value-text">{{ scope.row.raw?.strength_err ?? '-' }}</span>-->
<!--                        </template>-->
<!--                      </el-table-column>-->

<!--                      <el-table-column label="延伸率误差" align="center">-->
<!--                        <template #default="scope">-->
<!--                          <span class="value-text">{{ scope.row.raw?.elongation_err ?? '-' }}</span>-->
<!--                        </template>-->
<!--                      </el-table-column>-->
                    </el-table>
                  </div>

                  <div v-else class="empty-state">
                    <div class="empty-icon-bg">
                      <el-icon><DataAnalysis /></el-icon>
                    </div>
                    <p>暂无预测数据</p>
                    <span>请配置参数并启动</span>
                  </div>
                </transition>
              </div>

              <!-- 下半部分：图表 (占据剩余空间) -->
              <div class="result-chart-section">
                <div ref="chartRef" class="chart-container"></div>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { Operation, Tools, Cpu, DataAnalysis } from '@element-plus/icons-vue'
import request from '@/utils/request'

const loading = ref(false)
const chartRef = ref(null)
let chartInstance = null

// 13 种元素配置
const elementConfig = {
  Al: {p:1, s:0.1, max:10}, Sn: {p:1, s:0.1, max:10}, V: {p:1, s:0.1, max:10},
  Zr: {p:1, s:0.1, max:10}, Mo: {p:1, s:0.1, max:10}, Cr: {p:1, s:0.1, max:10},
  Nb: {p:1, s:0.1, max:10}, Ta: {p:1, s:0.1, max:10}, Fe: {p:2, s:0.05, max:2},
  Si: {p:2, s:0.05, max:1}, O: {p:3, s:0.01, max:0.5}, C: {p:3, s:0.01, max:0.5}, N: {p:3, s:0.01, max:0.5}
}

const form = reactive({
  elements: { Al:6.0, V:4.0, Sn:0, Zr:0, Mo:0, Cr:0, Nb:0, Ta:0, Fe:0.1, Si:0, O:0.15, C:0.01, N:0.01 },
  hotWorking: { enabled: false, type: 'Forging', temperature: 950, deformation: 50, passes: 1 },
  heatTreatmentMode: 'text',
  heatTreatment: { enabled: false, stages: [] },
  heatTreatmentText: '',
  selectedModels: ['BERT-XGB-v2']
})

const predictionResults = ref([])

const handlePredict = async () => {
  if (form.selectedModels.length === 0) {
    ElMessage.warning('请至少选择一个预测模型')
    return
  }

  loading.value = true
  try {
    const res = await request.post('/predict', form)
    console.log('res:', res)  // ✅ 这里打印后端返回的原始数据

    let finalData = []
    if (Array.isArray(res)) {
      finalData = res
    } else if (res && Array.isArray(res.data)) {
      finalData = res.data
    } else if (res && res.data && Array.isArray(res.data.data)) {
      finalData = res.data.data
    }
    console.log('finalData:', finalData) // ✅ 打印处理后的数组

    predictionResults.value = finalData

    await nextTick()
    updateChart()

    if (finalData.length === 0) {
      ElMessage.warning('预测结果为空')
    } else {
      ElMessage.success('预测成功')
    }

  } catch (e) {
    console.error('预测出错:', e)
    predictionResults.value = []
  } finally {
    loading.value = false
  }
}

const initChart = () => {
  if (chartRef.value) {
    if (chartRef.value.clientWidth === 0 || chartRef.value.clientHeight === 0) {
      console.warn('Chart container has 0 dimensions, retrying in 100ms...')
      setTimeout(initChart, 100)
      return
    }

    if (echarts.getInstanceByDom(chartRef.value)) {
      echarts.getInstanceByDom(chartRef.value).dispose()
    }
    chartInstance = echarts.init(chartRef.value)
    updateChart()
  }
}

const updateChart = () => {
  if (!chartInstance) return

  const data = predictionResults.value || []

  // ✅ 修改点：使用 strength / elongation
  const seriesData = data.map(item => [item.elongation, item.strength])

  chartInstance.setOption({
    grid: { top: 40, right: 30, bottom: 30, left: 50, containLabel: true },
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255, 255, 255, 0.9)',
      borderColor: '#eee',
      textStyle: { color: '#333' },
      formatter: (params) => {
        if (params.seriesType === 'scatter') {
          const item = data[params.dataIndex]
          return `<b>${item ? item.model : ''}</b><br/>Strength: ${item.strength} MPa<br/>Elongation: ${item.elongation} %`
        }
        return ''
      }
    },
    xAxis: {
      name: '延伸率 (%)',
      nameLocation: 'middle',
      nameGap: 25,
      min: 0, max: 25,
      splitLine: { lineStyle: { type: 'dashed', color: '#eee' } }
    },
    yAxis: {
      name: '抗拉强度 (MPa)',
      min: 400, max: 1500,
      splitLine: { lineStyle: { type: 'dashed', color: '#eee' } }
    },
    series: [
      {
        type: 'line',
        data: [[5, 1300], [15, 800], [22, 500]],
        smooth: true,
        areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{offset: 0, color: 'rgba(102, 126, 234, 0.2)'}, {offset: 1, color: 'rgba(102, 126, 234, 0)'}]) },
        symbol: 'none',
        lineStyle: { type: 'dashed', color: '#a0cfff' }
      },
      {
        type: 'scatter',
        symbolSize: 18,
        data: seriesData,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 1, [{offset: 0, color: '#667eea'}, {offset: 1, color: '#764ba2'}]),
          shadowBlur: 10,
          shadowColor: 'rgba(118, 75, 162, 0.5)'
        },
        label: { show: true, formatter: (p) => {
            const item = data[p.dataIndex]
            return item ? item.model : ''
          }, position: 'top', color: '#666', fontSize: 10 }
      }
    ]
  })
}

const handleResize = () => {
  chartInstance && chartInstance.resize()
}

onMounted(() => {
  setTimeout(() => {
    initChart()
    window.addEventListener('resize', handleResize)
  }, 200)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (chartInstance) {
    chartInstance.dispose()
  }
})
</script>

<style scoped>
.page-container {
  height: calc(100vh - 84px); /* 假设顶部导航栏约 84px，根据实际情况调整 */
  background-color: #f8fafc;
  padding: 16px 24px;
  display: flex;
  flex-direction: column;
  overflow: hidden; /* 禁止页面级滚动 */
  box-sizing: border-box;
}

/* Header 固定高度 */
.page-header {
  flex-shrink: 0;
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
}
.page-title {
  font-size: 22px;
  color: #1e293b;
  font-weight: 700;
  margin: 0 0 4px 0;
  display: flex;
  align-items: baseline;
}
.en-title {
  font-size: 13px;
  color: #94a3b8;
  font-weight: 400;
  margin-left: 10px;
}
.page-desc {
  color: #64748b;
  font-size: 13px;
  margin: 0;
}

/* Main Content 占据剩余高度 */
.main-content {
  flex: 1;
  min-height: 0; /* 关键：允许 flex 子项小于内容高度 */
  display: flex;
  flex-direction: column;
}
.full-height-row {
  height: 100%;
}
.full-height-col {
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* Modern Card 撑满列高 */
.modern-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.03);
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  border: 1px solid #f1f5f9;
}

.card-header-bar {
  flex-shrink: 0;
  padding: 12px 20px;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  align-items: baseline;
  background: #fff;
}
.header-title {
  font-size: 15px;
  font-weight: 700;
  color: #334155;
}
.header-subtitle {
  font-size: 11px;
  color: #cbd5e1;
  margin-left: 8px;
  font-weight: 500;
  text-transform: uppercase;
}

/* Card Body: 核心滚动区域 */
.card-body {
  flex: 1;
  min-height: 0;
  position: relative;
}
.scrollable-y {
  overflow-y: auto;
  padding: 20px;
}
.no-padding {
  padding: 0;
}

/* 美化滚动条 */
.scrollable-y::-webkit-scrollbar {
  width: 6px;
}
.scrollable-y::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}
.scrollable-y::-webkit-scrollbar-track {
  background: transparent;
}

/* Form Styling */
.form-section {
  margin-bottom: 20px;
}
.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
}
.icon-box {
  width: 22px;
  height: 22px;
  border-radius: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 8px;
  color: white;
  font-size: 12px;
}
.blue-icon { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.purple-icon { background: linear-gradient(135deg, #fccb90 0%, #d57eeb 100%); }
.green-icon { background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%); }

/* Elements Grid */
.elements-grid {
  background: #f8fafc;
  padding: 8px;
  border-radius: 8px;
  border: 1px solid #f1f5f9;
}
.element-col {
  margin-bottom: 6px;
}
.element-item-compact {
  display: flex;
  align-items: center;
  background: white;
  padding: 4px;
  border-radius: 4px;
  border: 1px solid #e2e8f0;
}
.el-name {
  width: 30px;
  font-weight: bold;
  color: #64748b;
  font-size: 11px;
  text-align: right;
  margin-right: 6px;
}
.mini-input {
  flex: 1;
}
:deep(.el-input-number.mini-input .el-input__wrapper) {
  padding-left: 2px;
  padding-right: 25px;
}
/* 模式切换按钮容器 */
.mode-switch-bar {
  display: flex;
  gap: 10px;              /* 👈 明确分离 */
  margin-bottom: 12px;
}

/* 普通态 */
.mode-btn {
  flex: 1;
  height: 32px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  background: #f8fafc;
  color: #64748b;
  border: 1px solid #e2e8f0;
  transition: all 0.25s ease;
}

/* Hover */
.mode-btn:hover {
  background: #eef2ff;
  border-color: #c7d2fe;
  color: #4338ca;
}

/* 选中态（当前模式） */
.mode-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
  border-color: transparent;
  box-shadow: 0 4px 12px rgba(118, 75, 162, 0.35);
}

/* Process Panel */
.sub-panel {
  background: #f8fafc;
  border-radius: 8px;
  padding: 10px;
  border: 1px solid #f1f5f9;
  margin-bottom: 8px;
}
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  margin-bottom: 8px;
}
.compact-form-item {
  margin-bottom: 6px;
}
:deep(.compact-form-item .el-form-item__label) {
  font-size: 11px;
  padding-bottom: 0px;
  color: #64748b;
  line-height: 1.5;
}

/* Vertical Stage Item */
.stage-item-vertical {
  background: white;
  padding: 6px;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
  margin-bottom: 6px;
}
.stage-header-row {
  display: flex;
  align-items: center;
  margin-bottom: 4px;
}
.stage-inputs-row {
  display: flex;
  align-items: center;
  gap: 4px;
}
.stage-badge {
  width: 16px;
  height: 16px;
  background: #e2e8f0;
  color: #64748b;
  border-radius: 50%;
  font-size: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 5px;
}
.unit {
  font-size: 11px;
  color: #94a3b8;
}
.add-btn {
  width: 100%;
  border-style: dashed;
  height: 28px;
  font-size: 12px;
}

/* Right Column (Model Select) */
.right-col-flex {
  display: flex;
  flex-direction: column;
}
.full-height-section {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.model-select-container {
  flex: 1;
  background: #f8fafc;
  border-radius: 8px;
  padding: 10px;
  border: 1px solid #f1f5f9;
  margin-bottom: 10px;
  overflow-y: auto; /* 模型多时可滚动 */
}
.vertical-checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.model-checkbox-block {
  margin-left: 0 !important;
  width: 100%;
  background: white;
  height: 32px;
}
.predict-btn-wrapper {
  display: flex;
  justify-content: center;
  flex-shrink: 0;
}
.predict-btn {
  width: 100%;
  height: 40px;
  font-size: 14px;
  font-weight: 600;
  border-radius: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(118, 75, 162, 0.3);
  transition: all 0.3s;
}
.predict-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(118, 75, 162, 0.4);
}
/* 数值 / 文本模式 与下方工艺面板的统一间距 */
.process-mode-content {
  margin-top: 16px;   /* 👈 拉开与“数值 / 文本切换”的距离 */
}

/* 热加工 与 热处理 面板之间的距离 */
.process-mode-content .sub-panel + .sub-panel {
  margin-top: 12px;
}

/* 文本模式下 textarea 与标题的距离 */
.text-mode-panel {
  margin-top: 16px;
}

/* Result Layout (Right Side) */
.result-layout {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden; /* 内部管理滚动 */
}

.result-table-section {
  flex-shrink: 0;
  max-height: 45%; /* 表格最多占 45% 高度 */
  display: flex;
  padding: 8px 10px;
  box-sizing: border-box;
  flex-direction: column;
  border-bottom: 1px solid #f1f5f9;
}

.table-inner-container {
  overflow-y: auto; /* 表格内部滚动 */
  max-height: 100%;
}
/* 表格滚动条美化 */
.table-inner-container::-webkit-scrollbar { width: 6px; }
.table-inner-container::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }

.result-chart-section {
  flex: 1; /* 图表占据剩余所有空间 */
  min-height: 0; /* 允许 flex 压缩 */
  padding: 10px;
  background: #fff;
  position: relative;
}

.chart-container {
  width: 100%;
  height: 100%;
}

.empty-state {
  padding: 30px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #cbd5e1;
}
.empty-icon-bg {
  width: 60px;
  height: 60px;
  background: #f8fafc;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  margin-bottom: 10px;
  color: #94a3b8;
}
.empty-state p {
  font-size: 14px;
  color: #64748b;
  margin: 0 0 4px 0;
  font-weight: 600;
}
.value-text {
  font-weight: 700;
  color: #334155;
}

/* Transitions */
.fade-slide-enter-active, .fade-slide-leave-active {
  transition: all 0.3s ease;
}
.fade-slide-enter-from, .fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
