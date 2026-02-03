<template>
  <div class="page-container">
    <!-- 顶部标题 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">实验历史记录 <span class="en-title">Experiment History</span></h1>
        <p class="page-desc">查看过往的预测记录与实验数据，支持导出与回溯分析。</p>
      </div>
    </div>

    <!-- 主体内容 -->
    <div class="main-content">
      <div class="modern-card">
        <div class="card-header-bar">
          <div class="header-left">
            <span class="header-title">数据列表</span>
            <span class="header-subtitle">Database</span>
          </div>

          <!-- 筛选工具栏 -->
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
            <el-button type="primary" size="small" color="#667eea" icon="Search" @click="fetchTasks(1)">查询</el-button>
            <el-button size="small" icon="Download">导出</el-button>
          </div>
        </div>

        <!-- 卡片内容 -->
        <div class="card-body no-padding table-layout">
          <div class="table-wrapper">
            <el-table
                :data="tasks"
                style="width: 100%; height: 100%;"
                stripe
            >
              <el-table-column label="编号" width="80" align="center">
                <template #default="scope">{{ (currentPage - 1) * pageSize + scope.$index + 1 }}</template>
              </el-table-column>

              <!-- 任务标题 + 类型标签 -->
              <el-table-column label="任务标题" min-width="200">
                <template #default="scope">
                  {{ scope.row.title }}
                  <el-tag v-if="scope.row.task_type === 'forward'" type="success" size="small" style="margin-left: 6px;">性能预测</el-tag>
                  <el-tag v-else-if="scope.row.task_type === 'inverse'" type="warning" size="small" style="margin-left: 6px;">逆向设计</el-tag>
                  <el-tag v-else type="info" size="small" style="margin-left: 6px;">其他</el-tag>
                </template>
              </el-table-column>

              <el-table-column prop="status" label="状态" width="100" />
              <el-table-column prop="created_at" label="创建时间" width="180" />

              <el-table-column label="操作" width="120">
                <template #default="scope">
                  <el-button link type="primary" size="small" @click="viewDetail(scope.row)">详情</el-button>
                </template>
              </el-table-column>
            </el-table>

            <!-- 任务详情弹窗 -->
            <el-dialog
                v-model="detailVisible"
                :title="selectedTask ? (selectedTask.task_type === 'forward' ? '性能预测结果' : '逆向设计结果') : '任务详情'"
                width="800px"
            >
              <div v-if="selectedTask">
                <p><b>任务类型：</b>{{ selectedTask.task_type === 'forward' ? '性能预测' : selectedTask.task_type === 'inverse' ? '逆向设计' : '其他' }}</p>
                <p><b>创建时间：</b> {{ selectedTask.created_at }}</p>

                <!-- 性能预测结果 -->
                <div v-if="selectedTask.task_type === 'forward'">
                  <el-table :data="detailResults" stripe style="margin-top: 10px;">
                    <el-table-column prop="model_name" label="模型" />
                    <el-table-column prop="strength" label="强度" />
                    <el-table-column prop="elongation" label="延伸率" />
                  </el-table>
                </div>

                <!-- 逆向设计结果 -->
                <div v-else-if="selectedTask.task_type === 'inverse'">
                  <el-table :data="detailResults" stripe style="margin-top: 10px;">
                    <el-table-column prop="rank" label="排名" width="80"/>
                    <el-table-column prop="predicted_strength" label="预测强度"/>
                    <el-table-column prop="predicted_elongation" label="预测延伸率"/>
                    <el-table-column prop="score" label="评分"/>
                  </el-table>
                </div>

                <div v-else>
                  暂无详细结果
                </div>
              </div>
            </el-dialog>
          </div>

          <!-- 分页 -->
          <div class="pagination-wrapper">
            <el-pagination
                background
                layout="prev, pager, next"
                :total="totalTasks"
                :current-page="currentPage"
                :page-size="pageSize"
                @current-change="fetchTasks"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const API_BASE = 'http://127.0.0.1:8000/api'

const tasks = ref([])
const totalTasks = ref(0)
const currentPage = ref(1)
const pageSize = ref(30)
const detailVisible = ref(false)
const selectedTask = ref(null)
const detailResults = ref([])
const searchKeyword = ref('')
const dateRange = ref([])

// 获取任务列表（分页）
const fetchTasks = async (page = 1) => {
  currentPage.value = page
  try {
    const res = await axios.get(`${API_BASE}/tasks`, {
      params: {
        page: page,
        page_size: pageSize.value,
        keyword: searchKeyword.value,
        start_date: dateRange.value[0] || '',
        end_date: dateRange.value[1] || ''
      }
    })
    tasks.value = res.data.items
    totalTasks.value = res.data.total
  } catch {
    ElMessage.error('获取任务列表失败')
  }
}

// 查看详情
const viewDetail = async (task) => {
  selectedTask.value = task
  detailVisible.value = true

  try {
    if (task.task_type === 'forward') {
      const res = await axios.get(`${API_BASE}/tasks/${task.id}/results`)
      detailResults.value = res.data
    } else if (task.task_type === 'inverse') {
      const res = await axios.get(`${API_BASE}/tasks/${task.id}/inverse-results`)
      detailResults.value = res.data
    } else {
      detailResults.value = []
    }
  } catch {
    ElMessage.error('获取详情失败')
  }
}

onMounted(() => {
  fetchTasks(1)
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