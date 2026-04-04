<template>
  <div class="page-container">
    <!-- 顶部标题 (固定高度) -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">成分逆向设计 <span class="en-title">Inverse Design</span></h1>
        <p class="page-desc">输入目标性能范围，算法将自动反演最优的化学成分配比与工艺方案。</p>
      </div>
    </div>

    <!-- 主体内容 (自适应剩余高度) -->
    <div class="main-content">
      <el-row :gutter="20" class="full-height-row">
        <!-- 左侧：约束配置 -->
        <el-col :span="11" class="full-height-col">
          <div class="modern-card input-card">
            <div class="card-header-bar">
              <span class="header-title">设计约束配置</span>
              <span class="header-subtitle">Constraints</span>
            </div>

            <!-- 滚动区域：仅在此处出现滚动条 -->
            <div class="card-body scrollable-y">
              <el-form :model="form" label-position="top" class="modern-form">

                <!-- 1. 目标性能 -->
                <div class="form-section">
                  <div class="section-title">
                    <span class="icon-box purple-icon"><el-icon><Aim /></el-icon></span>
                    目标性能范围
                  </div>
                  <div class="target-panel">
                    <div class="slider-item">
                      <span class="slider-label">抗拉强度 Rm (MPa)</span>
                      <el-slider v-model="form.targetRm" range :min="400" :max="1800" :step="10" />
                      <div class="range-val">{{ form.targetRm[0] }} - {{ form.targetRm[1] }} MPa</div>
                    </div>
                    <div class="slider-item">
                      <span class="slider-label">延伸率 A (%)</span>
                      <el-slider v-model="form.targetA" range :min="0" :max="40" :step="0.5" />
                      <div class="range-val">{{ form.targetA[0] }} - {{ form.targetA[1] }} %</div>
                    </div>
                  </div>
                </div>

                <!-- 2. 元素范围约束 -->
                <div class="form-section">
                  <div class="section-title">
                    <span class="icon-box green-icon"><el-icon><Operation /></el-icon></span>
                    元素含量约束 (wt.%)
                  </div>
                  <div class="elements-grid">
                    <el-row :gutter="12">
                      <el-col :span="12" v-for="(range, el) in elementConfig" :key="el" class="element-col">
                        <div class="element-item-compact">
                          <span class="el-name">{{ el }}</span>
                          <div class="el-inputs">
                            <el-input-number
                                v-model="form.constraints[el][0]"
                                :min="0"
                                :max="form.constraints[el][1]"
                                size="small"
                                :controls="false"
                                class="mini-input"
                            />
                            <span class="sep">-</span>
                            <el-input-number
                                v-model="form.constraints[el][1]"
                                :min="form.constraints[el][0]"
                                :max="range.max"
                                size="small"
                                :controls="false"
                                class="mini-input"
                            />
                          </div>
                        </div>
                      </el-col>
                    </el-row>
                  </div>
                </div>

                <div class="form-section no-bg">
                  <el-button class="predict-btn" type="primary" size="large" @click="handleInverse" :loading="loading">
                    <el-icon class="el-icon--left"><MagicStick /></el-icon> 生成推荐方案
                  </el-button>
                </div>

              </el-form>
            </div>
          </div>
        </el-col>

        <!-- 右侧：推荐结果 -->
        <el-col :span="13" class="full-height-col">
          <div class="modern-card result-card">
            <div class="card-header-bar">
              <span class="header-title">AI 推荐方案 (Top 5)</span>
              <span class="header-subtitle">Recommendations</span>
            </div>

            <!-- 右侧布局：Flex 纵向，防止图表被挤出 -->
            <div class="card-body no-padding result-layout">

              <!-- 上半部分：表格 (自适应高度，内部滚动) -->
              <div class="result-table-section">
                <div v-if="inverseResults.length > 0" class="table-inner-container">
                  <el-table :data="inverseResults" :row-key="(row) => row.rank" style="width: 100%" border stripe size="small">
                    <el-table-column prop="rank" label="排名" width="60" align="center">
                      <template #default="scope">
                        <div class="rank-badge" :class="'rank-'+scope.row.rank">{{ scope.row.rank }}</div>
                      </template>
                    </el-table-column>

                    <el-table-column label="推荐成分 (wt.%)" min-width="180">
                      <template #default="scope">
                        <div class="composition-tags">
                          <span v-for="(val, key) in filterElements(scope.row.elements)" :key="key" class="comp-tag">
                            <b>{{ key }}</b>{{ val }}
                          </span>
                        </div>
                      </template>
                    </el-table-column>

                    <el-table-column label="预测性能" width="140">
                      <template #default="scope">
                        <div class="perf-cell">
                          <div>抗拉强度: <b>{{ scope.row.predicted_strength }}</b></div>
                          <div>延伸率: <b>{{ scope.row.predicted_elongation }}</b> %</div>
                        </div>
                      </template>
                    </el-table-column>

                    <el-table-column label="匹配得分" width="100" align="center">
                      <template #default="scope">
                        <el-progress type="dashboard" :percentage="scope.row.score" :width="40" :stroke-width="3" :color="getScoreColor(scope.row.score)">
                          <template #default="{ percentage }">
                            <span class="score-text">{{ percentage }}</span>
                          </template>
                        </el-progress>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>

                <div v-else class="empty-state">
                  <div class="empty-icon-bg">
                    <el-icon><Search /></el-icon>
                  </div>
                  <p>等待启动设计</p>
                  <span>请配置约束条件并点击启动按钮</span>
                </div>
              </div>

              <!-- 下半部分：雷达图 (固定高度或占据剩余空间) -->
              <div class="result-chart-section">
                <p class="chart-title" v-if="inverseResults.length > 0">最佳方案性能雷达图</p>
                <!-- 使用 ref 获取 DOM -->
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
import { ElMessage } from 'element-plus'
import { Aim, Operation, MagicStick, Search } from '@element-plus/icons-vue'
import request from '@/utils/request'
import * as echarts from 'echarts'

const loading = ref(false)
const inverseResults = ref([])
const chartRef = ref(null)
let chartInstance = null

const elementConfig = {
  Al: {max:10}, Sn: {max:10}, V: {max:10}, Zr: {max:10}, Mo: {max:10},
  Cr: {max:10}, Nb: {max:10}, Ta: {max:10}, Fe: {max:2},
  Si: {max:1}, O: {max:0.5}, C: {max:0.5}, N: {max:0.5}
}

const initConstraints = {}
for (const key in elementConfig) {
  initConstraints[key] = [0, elementConfig[key].max]
}
initConstraints['Al'] = [5.5, 6.8]
initConstraints['V'] = [3.5, 4.5]

const form = reactive({
  targetRm: [900, 1100],
  targetA: [10, 20],
  constraints: initConstraints
})

const handleInverse = async () => {
  loading.value = true
  try {
    // 封装请求在 status===success 时已解包为 res.data（即 Top5 结果数组）
    const res = await request.post('/inverse', form)
    const data = Array.isArray(res) ? res : []

    inverseResults.value = data

    if (data.length > 0) {
      ElMessage.success(`成功生成 ${data.length} 个推荐方案`)
      // 数据更新后刷新图表
      nextTick(() => {
        initRadarChart(data[0])
      })
    } else {
      ElMessage.warning('未能生成符合条件的方案')
    }

  } catch (e) {
    console.error(e)
    ElMessage.error('算法运行出错')
  } finally {
    loading.value = false
  }
}

const filterElements = (elements) => {
  const res = {}
  for (const k in elements) {
    if (elements[k] > 0.01) res[k] = elements[k]
  }
  return res
}

const getScoreColor = (score) => {
  if (score >= 90) return '#67C23A'
  if (score >= 80) return '#409EFF'
  return '#E6A23C'
}

const initRadarChart = (top1) => {
  if (!chartRef.value) return

  // 销毁旧实例
  if (echarts.getInstanceByDom(chartRef.value)) {
    echarts.getInstanceByDom(chartRef.value).dispose()
  }

  chartInstance = echarts.init(chartRef.value)

  // 如果没有数据，显示空图表或不显示
  if (!top1) {
    chartInstance.clear()
    return
  }

  chartInstance.setOption({
    tooltip: {},
    radar: {
      indicator: [
        {name: '抗拉强度', max: 1800},
        {name: '延伸率', max: 30},
        {name: '匹配度', max: 100},
        {name: '成本(模拟)', max: 100},
        {name: '工艺性(模拟)', max: 100}
      ],
      splitArea: {
        areaStyle: {
          color: ['#f8fafc', '#fff']
        }
      }
    },
    series: [{
      name: '最佳方案性能',
      type: 'radar',
      data: [
        {
          value: [top1.predicted_strength, top1.predicted_elongation, top1.score, 80, 85],
          name: 'Top 1 方案',
          areaStyle: {color: 'rgba(64, 158, 255, 0.2)'},
          itemStyle: {color: '#409EFF'}
        }
      ]
    }]
  })
}

const handleResize = () => {
  chartInstance && chartInstance.resize()
}

onMounted(() => {
  // 延迟初始化，确保布局计算完成
  setTimeout(() => {
    // 初始化一个空图表占位，或者等待数据
    if (inverseResults.value.length > 0) {
      initRadarChart(inverseResults.value[0])
    }
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
/*
  核心布局重构：
  1. page-container 固定高度，禁止溢出
  2. main-content 占据剩余空间
  3. 内部元素全部 height: 100% 传递
*/
.page-container {
  height: calc(100vh - 84px);
  background-color: #f8fafc;
  padding: 16px 24px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-sizing: border-box;
}

.page-header {
  flex-shrink: 0;
  margin-bottom: 16px;
}

.page-title {
  font-size: 22px;
  color: #1e293b;
  font-weight: 700;
  margin: 0 0 4px 0;
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

/* Main Content */
.main-content {
  flex: 1;
  min-height: 0;
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

/* Modern Card */
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

/* Card Body & Scrolling */
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
.scrollable-y::-webkit-scrollbar,
.table-inner-container::-webkit-scrollbar {
  width: 6px;
}
.scrollable-y::-webkit-scrollbar-thumb,
.table-inner-container::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}
.scrollable-y::-webkit-scrollbar-track,
.table-inner-container::-webkit-scrollbar-track {
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

.purple-icon { background: linear-gradient(135deg, #fccb90 0%, #d57eeb 100%); }
.green-icon { background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%); }

.target-panel {
  background: #f8fafc;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid #f1f5f9;
}

.slider-item {
  margin-bottom: 12px;
}
.slider-item:last-child { margin-bottom: 0; }

.slider-label {
  font-size: 12px;
  color: #64748b;
  display: block;
  margin-bottom: 2px;
}

.range-val {
  font-size: 11px;
  color: #764ba2;
  text-align: right;
  font-weight: bold;
  margin-top: -5px;
}

.elements-grid {
  background: #f8fafc;
  padding: 8px;
  border-radius: 8px;
  border: 1px solid #f1f5f9;
}

.element-item-compact {
  display: flex;
  align-items: center;
  margin-bottom: 6px;
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

.el-inputs {
  flex: 1;
  display: flex;
  align-items: center;
}

.mini-input {
  width: 100%;
}

:deep(.el-input-number.mini-input .el-input__wrapper) {
  padding-left: 2px;
  padding-right: 2px;
}

.sep {
  margin: 0 4px;
  color: #cbd5e1;
  font-size: 12px;
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

/* Result Layout (Right Side) */
.result-layout {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.result-table-section {
  flex: 1; /* 表格占据主要空间 */
  min-height: 0;
  display: flex;
  flex-direction: column;
  border-bottom: 1px solid #f1f5f9;
  overflow: hidden;
}

.table-inner-container {
  padding: 8px 10px;
  box-sizing: border-box;
  overflow-y: auto;
  height: 100%;
}

.result-chart-section {
  flex-shrink: 0;
  height: 300px; /* 固定图表区域高度 */
  padding: 10px;
  background: #fff;
  display: flex;
  flex-direction: column;
}

.chart-container {
  width: 100%;
  flex: 1;
  min-height: 200px;
}

.chart-title {
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  margin: 0 0 10px 0;
  text-align: center;
}

/* Table Styles */
.rank-badge {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #e2e8f0;
  color: #64748b;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 11px;
  margin: 0 auto;
}
.rank-1 { background: #FFD700; color: white; box-shadow: 0 2px 5px rgba(255, 215, 0, 0.4); }
.rank-2 { background: #C0C0C0; color: white; }
.rank-3 { background: #CD7F32; color: white; }

.composition-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.comp-tag {
  background: #f0f9eb;
  color: #67c23a;
  padding: 1px 5px;
  border-radius: 3px;
  font-size: 11px;
}

.perf-cell {
  font-size: 12px;
  line-height: 1.4;
}

.score-text {
  font-size: 10px;
  font-weight: bold;
}

.empty-state {
  flex: 1;
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
</style>
