<template>
  <div class="page-container">
    <!-- 顶部标题 (固定高度) -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">实验历史记录 <span class="en-title">Experiment History</span></h1>
        <p class="page-desc">查看过往的预测记录与实验数据，支持导出与回溯分析。</p>
      </div>
    </div>

    <!-- 主体内容 (自适应剩余高度) -->
    <div class="main-content">
      <div class="modern-card">
        <div class="card-header-bar">
          <div class="header-left">
            <span class="header-title">数据列表</span>
            <span class="header-subtitle">Database</span>
          </div>

          <!-- 顶部筛选工具栏 -->
          <div class="filter-bar">
            <el-input
                v-model="searchKeyword"
                placeholder="搜索成分或编号..."
                prefix-icon="Search"
                size="small"
                style="width: 200px; margin-right: 10px;"
            />
            <el-date-picker
                v-model="dateRange"
                type="daterange"
                range-separator="To"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                size="small"
                style="width: 240px; margin-right: 10px;"
            />
            <el-button type="primary" size="small" color="#667eea" icon="Search">查询</el-button>
            <el-button size="small" icon="Download">导出</el-button>
          </div>
        </div>

        <!-- 卡片内容区：Flex 纵向布局 -->
        <div class="card-body no-padding table-layout">
          <!-- 表格区域：Flex 1 撑满剩余空间 -->
          <div class="table-wrapper">
            <!-- height="100%" 是实现表头固定、内部滚动的关键 -->
            <el-table
                :data="tableData"
                style="width: 100%; height: 100%;"
                :header-cell-style="{background:'#f8fafc', color:'#64748b', fontWeight:'600'}"
                stripe
            >
              <el-table-column prop="id" label="编号" width="80" align="center" />

              <el-table-column label="合金成分" min-width="180">
                <template #default="scope">
                  <div class="composition-tag">
                    <span class="main-el">Ti</span>
                    <span class="sub-el">{{ scope.row.composition }}</span>
                  </div>
                </template>
              </el-table-column>

              <el-table-column label="工艺类型" width="120">
                <template #default="scope">
                  <el-tag :type="getProcessTagType(scope.row.process)" effect="light" size="small">
                    {{ scope.row.process }}
                  </el-tag>
                </template>
              </el-table-column>

              <el-table-column label="预测结果" width="200">
                <template #default="scope">
                  <div class="result-mini-grid">
                    <span>Rm: <b>{{ scope.row.rm }}</b></span>
                    <span>A: <b>{{ scope.row.a }}%</b></span>
                  </div>
                </template>
              </el-table-column>

              <!-- 模型列：加宽并支持 tooltip -->
              <el-table-column prop="model" label="使用模型" width="180" show-overflow-tooltip>
                <template #default="scope">
                  <span class="model-badge">{{ scope.row.model }}</span>
                </template>
              </el-table-column>

              <el-table-column prop="date" label="时间" width="160" sortable />

              <el-table-column label="操作" width="150" align="center" fixed="right">
                <template #default>
                  <el-button link type="primary" size="small">详情</el-button>
                  <el-button link type="danger" size="small">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <!-- 分页区域：固定在底部 -->
          <div class="pagination-wrapper">
            <el-pagination background layout="prev, pager, next" :total="100" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Search, Download } from '@element-plus/icons-vue'

const searchKeyword = ref('')
const dateRange = ref([])

const tableData = ref([
  { id: '1001', composition: '-6Al-4V', process: 'Forging', rm: 950, a: 14.5, model: 'XGBoost-Optimized-V2', date: '2023-10-20 14:30' },
  { id: '1002', composition: '-5Al-2.5Sn', process: 'Rolling', rm: 820, a: 18.2, model: 'RandomForest-Ensemble', date: '2023-10-19 09:15' },
  { id: '1003', composition: '-10V-2Fe-3Al', process: 'HeatTreat', rm: 1150, a: 8.5, model: 'SVM-Kernel-RBF', date: '2023-10-18 16:45' },
  { id: '1004', composition: '-6Al-4V', process: 'Forging', rm: 960, a: 14.0, model: 'XGBoost', date: '2023-10-18 11:20' },
  { id: '1005', composition: '-3Al-2.5V', process: 'Casting', rm: 700, a: 22.0, model: 'BERT-Regression-Large', date: '2023-10-17 10:00' },
  { id: '1006', composition: '-6Al-4V', process: 'Forging', rm: 955, a: 14.2, model: 'XGBoost', date: '2023-10-16 09:30' },
  { id: '1007', composition: '-5Al-2.5Sn', process: 'Rolling', rm: 810, a: 18.5, model: 'RandomForest', date: '2023-10-15 14:15' },
  { id: '1008', composition: '-10V-2Fe-3Al', process: 'HeatTreat', rm: 1160, a: 8.2, model: 'SVM', date: '2023-10-14 11:45' },
  { id: '1009', composition: '-6Al-4V', process: 'Forging', rm: 945, a: 14.8, model: 'XGBoost', date: '2023-10-13 16:20' },
  { id: '1010', composition: '-3Al-2.5V', process: 'Casting', rm: 710, a: 21.5, model: 'BERT-Reg', date: '2023-10-12 10:00' },
])

const getProcessTagType = (process) => {
  const map = { 'Forging': 'primary', 'Rolling': 'success', 'HeatTreat': 'warning', 'Casting': 'info' }
  return map[process] || 'info'
}
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
.header-left {
  display: flex;
  align-items: baseline;
}
.header-title { font-size: 15px; font-weight: 700; color: #334155; }
.header-subtitle { font-size: 11px; color: #cbd5e1; margin-left: 8px; font-weight: 500; text-transform: uppercase; }

/* Card Body Layout */
.card-body {
  flex: 1;
  min-height: 0;
  position: relative;
}
.no-padding {
  padding: 0;
}
.table-layout {
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* Table Wrapper */
.table-wrapper {
  flex: 1;
  overflow: hidden; /* 让 el-table 处理滚动 */
}

/* Filter Bar */
.filter-bar {
  display: flex;
  align-items: center;
}

/* Custom Column Styles */
.composition-tag {
  font-family: 'Roboto Mono', monospace;
  color: #475569;
}
.main-el { font-weight: bold; color: #764ba2; }
.sub-el { color: #64748b; }

.result-mini-grid {
  display: flex;
  gap: 15px;
  font-size: 13px;
  color: #64748b;
}
.result-mini-grid b { color: #334155; }

.model-badge {
  background: #f1f5f9;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  color: #64748b;
  border: 1px solid #e2e8f0;
  white-space: nowrap;
}

/* Pagination */
.pagination-wrapper {
  flex-shrink: 0;
  padding: 12px 20px;
  border-top: 1px solid #f1f5f9;
  display: flex;
  justify-content: flex-end;
  background: #fff;
}
</style>
