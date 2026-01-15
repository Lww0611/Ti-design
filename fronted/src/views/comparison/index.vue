<template>
  <div class="page-container">
    <!-- 顶部标题 (固定高度) -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">方案对比 <span class="en-title">Scheme Comparison</span></h1>
        <p class="page-desc">多维度对比不同合金配方与工艺方案的性能指标，辅助最优决策。</p>
      </div>
    </div>

    <!-- 主体内容 (自适应剩余高度) -->
    <div class="main-content">
      <el-row :gutter="20" class="full-height-row">
        <!-- 左侧：方案选择列表 -->
        <el-col :span="7" class="full-height-col">
          <div class="modern-card">
            <div class="card-header-bar">
              <span class="header-title">选择方案</span>
              <div class="header-actions">
                <el-button type="primary" link icon="Plus" size="small" @click="dialogVisible = true">新建</el-button>
              </div>
            </div>
            <!-- 滚动区域：仅在此处出现滚动条 -->
            <div class="card-body scrollable-y">
              <div class="form-section">
                <div class="section-title">
                  <span class="icon-box blue-icon"><el-icon><List /></el-icon></span>
                  待选列表
                </div>

                <div v-if="availableSchemes.length === 0" class="empty-list">
                  暂无方案，请点击新建
                </div>

                <el-checkbox-group v-model="selectedSchemes" class="scheme-list">
                  <div v-for="item in availableSchemes" :key="item.id"
                       :class="['scheme-item', { active: selectedSchemes.includes(item.id) }]">
                    <div class="scheme-content">
                      <el-checkbox :label="item.id" size="large" @change="handleSelectionChange">
                        <span class="scheme-name">{{ item.name }}</span>
                      </el-checkbox>
                      <div class="scheme-tags">
                        <el-tag size="small" type="info">{{ item.type }}</el-tag>
                        <span class="date">{{ item.date }}</span>
                      </div>
                    </div>
                    <!-- 删除按钮 -->
                    <el-button
                        class="delete-btn"
                        type="danger"
                        link
                        icon="Delete"
                        @click.stop="handleDelete(item.id)"
                    />
                  </div>
                </el-checkbox-group>
              </div>
            </div>
          </div>
        </el-col>

        <!-- 右侧：对比图表与数据 -->
        <el-col :span="17" class="full-height-col">
          <div class="modern-card">
            <div class="card-header-bar">
              <span class="header-title">对比分析</span>
              <span class="header-subtitle">Analysis</span>
              <div class="header-actions">
                <el-radio-group v-model="viewMode" size="small" fill="#764ba2">
                  <el-radio-button label="chart">雷达图</el-radio-button>
                  <el-radio-button label="table">详细数据</el-radio-button>
                </el-radio-group>
              </div>
            </div>

            <!-- 右侧内容区：Flex 布局撑满高度 -->
            <div class="card-body no-padding result-layout">
              <!-- 图表视图 -->
              <div v-show="viewMode === 'chart'" class="chart-wrapper">
                <!-- 使用 ref 获取 DOM -->
                <div ref="chartRef" class="chart-container"></div>
              </div>

              <!-- 表格视图 -->
              <div v-if="viewMode === 'table'" class="table-wrapper">
                <!-- height="100%" 让表格自动撑满容器并固定表头 -->
                <el-table
                    :data="currentComparisonData"
                    border
                    style="width: 100%; height: 100%;"
                    :header-cell-style="{background:'#f8fafc', color:'#64748b'}"
                >
                  <el-table-column prop="name" label="方案名称" width="150" fixed />
                  <el-table-column prop="Rm" label="抗拉强度 (MPa)" align="center" />
                  <el-table-column prop="A" label="延伸率 (%)" align="center" />
                  <el-table-column prop="Cost" label="成本指数" align="center" />
                  <el-table-column prop="Density" label="密度 (g/cm³)" align="center" />
                </el-table>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 新建方案弹窗 -->
    <el-dialog v-model="dialogVisible" title="新建方案" width="400px">
      <el-form :model="newSchemeForm" label-width="80px">
        <el-form-item label="名称">
          <el-input v-model="newSchemeForm.name" placeholder="例如: Ti-New-01" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="newSchemeForm.type" style="width: 100%">
            <el-option label="Forging" value="Forging" />
            <el-option label="Casting" value="Casting" />
            <el-option label="Rolling" value="Rolling" />
          </el-select>
        </el-form-item>
        <!-- 模拟数据输入 -->
        <el-form-item label="强度 Rm">
          <el-input-number v-model="newSchemeForm.Rm" :min="0" />
        </el-form-item>
        <el-form-item label="延伸率 A">
          <el-input-number v-model="newSchemeForm.A" :min="0" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleAddScheme" color="#667eea">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import * as echarts from 'echarts'
import { List, Delete, Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const viewMode = ref('chart')
const selectedSchemes = ref([1, 2])
const dialogVisible = ref(false)
const chartRef = ref(null) // 使用 ref
let chartInstance = null

// 模拟完整数据源
const availableSchemes = ref([
  { id: 1, name: 'Ti-6Al-4V (基准)', type: 'Forging', date: '2023-10-01', Rm: 950, A: 14, Cost: 100, Density: 4.43 },
  { id: 2, name: 'Ti-High-Str Opt', type: 'Rolling', date: '2023-10-05', Rm: 1100, A: 10, Cost: 120, Density: 4.50 },
  { id: 3, name: 'Ti-Low-Cost V1', type: 'Casting', date: '2023-10-12', Rm: 850, A: 18, Cost: 80, Density: 4.40 },
  { id: 4, name: 'Ti-Ductility Plus', type: 'Forging', date: '2023-10-15', Rm: 900, A: 22, Cost: 110, Density: 4.45 },
])

const newSchemeForm = reactive({
  name: '',
  type: 'Forging',
  Rm: 900,
  A: 15,
  Cost: 100,
  Density: 4.5
})

// 根据选中项计算当前对比数据
const currentComparisonData = computed(() => {
  return availableSchemes.value.filter(item => selectedSchemes.value.includes(item.id))
})

// 监听数据变化刷新图表
watch(currentComparisonData, () => {
  if (viewMode.value === 'chart') {
    updateChart()
  }
}, { deep: true })

// 监听视图切换
watch(viewMode, (val) => {
  if (val === 'chart') {
    // 切换回图表时，需要等待 DOM 渲染并 resize
    nextTick(() => {
      if (!chartInstance) initChart()
      else {
        chartInstance.resize()
        updateChart()
      }
    })
  }
})

const handleSelectionChange = () => {
  // 触发 computed 更新，进而触发 watch
}

const handleAddScheme = () => {
  if(!newSchemeForm.name) return ElMessage.warning('请输入名称')

  const newId = Math.max(...availableSchemes.value.map(i => i.id), 0) + 1
  availableSchemes.value.push({
    id: newId,
    name: newSchemeForm.name,
    type: newSchemeForm.type,
    date: new Date().toISOString().split('T')[0],
    Rm: newSchemeForm.Rm,
    A: newSchemeForm.A,
    Cost: 100, // 默认
    Density: 4.5 // 默认
  })

  // 自动选中新建的
  selectedSchemes.value.push(newId)
  dialogVisible.value = false
  ElMessage.success('添加成功')

  // 重置表单
  newSchemeForm.name = ''
}

const handleDelete = (id) => {
  ElMessageBox.confirm('确定删除该方案吗？', '提示', { type: 'warning' }).then(() => {
    availableSchemes.value = availableSchemes.value.filter(item => item.id !== id)
    selectedSchemes.value = selectedSchemes.value.filter(sid => sid !== id)
    ElMessage.success('删除成功')
  }).catch(() => {})
}

const initChart = () => {
  if (chartRef.value) {
    // 安全检查：如果容器没有宽高，稍后重试
    if (chartRef.value.clientWidth === 0 || chartRef.value.clientHeight === 0) {
      console.warn('Chart container has 0 dimensions, retrying in 100ms...')
      setTimeout(initChart, 100)
      return
    }

    // 销毁旧实例防止内存泄漏或重复渲染
    if (echarts.getInstanceByDom(chartRef.value)) {
      echarts.getInstanceByDom(chartRef.value).dispose()
    }
    chartInstance = echarts.init(chartRef.value)
    updateChart()
  }
}

const updateChart = () => {
  if (!chartInstance) return

  const data = currentComparisonData.value

  if (data.length === 0) {
    chartInstance.clear()
    return
  }

  chartInstance.setOption({
    color: ['#667eea', '#764ba2', '#fccb90', '#48bb78', '#f56565'],
    tooltip: {},
    legend: {
      bottom: 0,
      data: data.map(i => i.name),
      icon: 'circle'
    },
    radar: {
      // --- 修改开始：添加 radius 和 center ---
      radius: '60%', // 控制大小，65% 比较适中
      center: ['50%', '50%'], // 居中显示
      // --- 修改结束 ---

      indicator: [
        { name: '抗拉强度 (Rm)', max: 1500 },
        { name: '延伸率 (A)', max: 30 },
        { name: '成本 (Cost)', max: 150 },
        { name: '密度 (Density)', max: 5 },
        { name: '硬度 (HV)', max: 400 }
      ],
      splitNumber: 4,
      axisName: {
        color: '#64748b',
        fontWeight: 'bold'
      },
      splitArea: {
        areaStyle: {
          color: ['#f8fafc', '#fff']
        }
      }
    },
    series: [{
      name: '方案对比',
      type: 'radar',
      data: data.map(item => ({
        value: [item.Rm, item.A, item.Cost, item.Density, 300],
        name: item.name,
        areaStyle: { opacity: 0.2 }
      }))
    }]
  })
}


const handleResize = () => {
  chartInstance && chartInstance.resize()
}

onMounted(() => {
  // 使用 setTimeout 确保布局计算完成
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
  align-items: center;
  background: #fff;
  justify-content: space-between;
}
.header-title { font-size: 15px; font-weight: 700; color: #334155; }
.header-subtitle { font-size: 11px; color: #cbd5e1; margin-left: 8px; font-weight: 500; text-transform: uppercase; }

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
.scrollable-y::-webkit-scrollbar { width: 6px; }
.scrollable-y::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }
.scrollable-y::-webkit-scrollbar-track { background: transparent; }

/* 左侧列表样式 */
.icon-box {
  width: 22px; height: 22px; border-radius: 5px;
  display: flex; align-items: center; justify-content: center;
  margin-right: 8px; color: white;
  font-size: 12px;
}
.blue-icon { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.section-title {
  font-size: 13px; font-weight: 600; color: #475569;
  margin-bottom: 12px; display: flex; align-items: center;
}

.scheme-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.scheme-item {
  background: #f8fafc;
  border: 1px solid #f1f5f9;
  border-radius: 8px;
  padding: 8px 12px;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.scheme-item:hover, .scheme-item.active {
  background: white;
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
}
.scheme-content {
  flex: 1;
}
.scheme-name {
  font-weight: 600;
  color: #334155;
  display: block;
  margin-bottom: 2px;
  font-size: 13px;
}
.scheme-tags {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: 24px; /* 对齐 checkbox 文字 */
}
.date {
  font-size: 11px;
  color: #94a3b8;
}
.delete-btn {
  opacity: 0;
  transition: opacity 0.2s;
}
.scheme-item:hover .delete-btn {
  opacity: 1;
}

/* 右侧布局 */
.result-layout {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chart-wrapper {
  flex: 1;
  width: 100%;
  height: 100%;
  padding: 10px;
  display: flex;
}
.chart-container {
  width: 100%;
  height: 100%;
  min-height: 300px; /* 确保有最小高度 */
}

.table-wrapper {
  flex: 1;
  height: 100%;
  overflow: hidden; /* 表格内部滚动 */
}

.empty-list {
  text-align: center;
  color: #94a3b8;
  padding: 20px;
  font-size: 13px;
}
</style>
