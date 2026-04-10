<template>
  <div class="page-container">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">数据集管理 <span class="en-title">Dataset Manager</span></h1>
        <p class="page-desc">管理平台内置与用户上传的数据集。</p>
      </div>

      <div class="header-right" v-if="isFromWorkflow">
        <el-button type="warning" plain @click="handleBackToWorkflow">
          <el-icon style="margin-right: 4px;"><ArrowLeft /></el-icon>
          返回工作流 (步骤 {{ parseInt(route.query.step) + 1 }})
        </el-button>
      </div>
    </div>

    <div class="main-content">
      <div class="modern-card">
        <div class="card-body table-layout">

          <div class="table-wrapper">
            <div class="table-header-bar">
              <h4>系统数据集（只读）</h4>
            </div>

            <el-table
                :data="systemDatasets"
                stripe
                height="100%"
                v-loading="loading"
            >
              <el-table-column type="index" label="ID" width="70"/>
              <el-table-column prop="name" label="名称"/>
              <el-table-column prop="n_rows" label="行数" width="90"/>
              <el-table-column prop="n_columns" label="列数" width="90"/>
              <el-table-column prop="missing_rate" label="缺失率" width="90"/>
              <el-table-column label="操作" width="160">
                <template #default="scope">
                  <el-button link type="primary" @click="viewDetail(scope.row)">详情</el-button>
                  <el-button v-if="isFromWorkflow" link type="success" @click="selectAndReturn(scope.row)">选择此数据</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <div class="table-wrapper">
            <div class="table-header-bar">
              <h4>用户上传数据集</h4>

              <div class="user-actions">
                <el-upload
                    :show-file-list="false"
                    :auto-upload="false"
                    accept=".csv"
                    @change="handleUpload"
                >
                  <el-button type="primary" size="small">上传数据集</el-button>
                </el-upload>

                <el-input
                    v-model="searchKeyword"
                    placeholder="搜索名称"
                    size="small"
                    style="width:180px"
                />
              </div>
            </div>

            <el-table
                :data="filteredUserDatasets"
                stripe
                height="100%"
                v-loading="loading"
            >
              <el-table-column type="index" label="ID" width="70"/>
              <el-table-column prop="name" label="名称"/>
              <el-table-column prop="n_rows" label="行数" width="90"/>
              <el-table-column prop="n_columns" label="列数" width="90"/>
              <el-table-column prop="missing_rate" label="缺失率" width="90"/>
              <el-table-column label="操作" width="220">
                <template #default="scope">
                  <el-button link type="primary" @click="viewDetail(scope.row)">详情</el-button>
                  <el-button v-if="isFromWorkflow" link type="success" @click="selectAndReturn(scope.row)">选择</el-button>
                  <el-button link type="danger" @click="deleteDataset(scope.row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>

          </div>

        </div>
      </div>
    </div>

    <el-dialog
        v-model="detailVisible"
        title="数据集详情"
        width="700px"
        custom-class="scientific-dialog"
    >
      <el-descriptions :column="2" border>
        <el-descriptions-item label="ID">{{ datasetDetail.id }}</el-descriptions-item>
        <el-descriptions-item label="名称">{{ datasetDetail.name }}</el-descriptions-item>
        <el-descriptions-item label="文件名">{{ datasetDetail.filename }}</el-descriptions-item>
        <el-descriptions-item label="来源">{{ datasetDetail.source_type }}</el-descriptions-item>
        <el-descriptions-item label="行数">{{ datasetDetail.n_rows }}</el-descriptions-item>
        <el-descriptions-item label="列数">{{ datasetDetail.n_columns }}</el-descriptions-item>
        <el-descriptions-item label="缺失率">{{ datasetDetail.missing_rate }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ datasetDetail.created_at }}</el-descriptions-item>
      </el-descriptions>

      <div class="detail-tags-section">
        <h4 class="tag-title">数值列 (Numeric)</h4>
        <div class="tag-container">
          <el-tag v-for="col in datasetDetail.numeric_columns || []" :key="col" size="small" type="success" effect="plain">{{ col }}</el-tag>
        </div>

        <h4 class="tag-title" style="margin-top:16px">可能目标列 (Target Candidates)</h4>
        <div class="tag-container">
          <el-tag v-for="col in datasetDetail.target_candidates || []" :key="col" size="small" type="warning" effect="plain">{{ col }}</el-tag>
        </div>
      </div>
    </el-dialog>

  </div>
</template>


<script setup>
import {ref, computed, onMounted} from 'vue'
import {useRouter, useRoute} from 'vue-router' // 必须引入
import axios from 'axios'
import {ElMessage, ElMessageBox} from 'element-plus'
import {ArrowLeft} from '@element-plus/icons-vue'
import { API_ROOT } from '@/config/api'

const router = useRouter()
const route = useRoute()

/* ================= 配置 ================= */
const API_BASE = API_ROOT

/* ================= 状态 ================= */
const loading = ref(false)
const datasets = ref([])
const searchKeyword = ref('')

/* ================= 路由交互逻辑 (方案 B) ================= */

// 判断是否从工作流跳转而来
const isFromWorkflow = computed(() => route.query.from === 'cases')

// 仅执行返回操作
const handleBackToWorkflow = () => {
  router.push({path: '/cases', query: route.query})
}

// 选择某条数据并携带 ID 返回
const selectAndReturn = (row) => {
  ElMessage.success(`已选中: ${row.name}`)
  router.push({
    path: '/cases',
    query: {
      ...route.query,
      selectedId: row.id
    }
  })
}

/* ================= 计算属性 ================= */
const systemDatasets = computed(() =>
    datasets.value.filter(d => d.source_type === 'system')
)

const userDatasets = computed(() =>
    datasets.value.filter(d => d.source_type === 'user')
)

const filteredUserDatasets = computed(() => {
  if (!searchKeyword.value) return userDatasets.value
  return userDatasets.value.filter(d =>
      d.name.toLowerCase().includes(searchKeyword.value.toLowerCase())
  )
})

/* ================= API 调用 ================= */

const fetchDatasets = async () => {
  loading.value = true
  try {
    const res = await axios.get(`${API_BASE}/v1/datasets`)
    datasets.value = res.data.data || res.data
  } catch (err) {
    ElMessage.error('加载数据集失败')
  } finally {
    loading.value = false
  }
}

const handleUpload = async (file) => {
  const formData = new FormData()
  formData.append('file', file.raw)
  try {
    loading.value = true
    await axios.post(`${API_BASE}/v1/datasets/upload`, formData)
    ElMessage.success('上传成功')
    fetchDatasets()
  } catch (err) {
    ElMessage.error('上传失败')
  } finally {
    loading.value = false
  }
}

const detailVisible = ref(false)
const datasetDetail = ref({})
const viewDetail = async (row) => {
  try {
    const res = await axios.get(`${API_BASE}/v1/datasets/${row.id}`)
    datasetDetail.value = res.data.data || res.data
    detailVisible.value = true
  } catch {
    ElMessage.error('获取详情失败')
  }
}

const deleteDataset = async (row) => {
  try {
    await ElMessageBox.confirm(`确认删除数据集 "${row.name}" ?`, '危险操作', {type: 'warning'})
    await axios.delete(`${API_BASE}/v1/datasets/${row.id}`)
    ElMessage.success('删除成功')
    fetchDatasets()
  } catch {
  }
}

onMounted(() => {
  fetchDatasets()
})
</script>

<style scoped>
/* 保持你的 flex 布局结构 */
.page-container {
  height: calc(100vh - 84px);
  padding: 16px 24px;
  background: #f8fafc; /* 稍微调浅一点，更有高级感 */
  display: flex;
  flex-direction: column;
}

.page-header {
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: 22px;
  font-weight: 800;
  color: #1e293b;
  margin: 0;
}

.en-title {
  font-size: 13px;
  margin-left: 10px;
  color: #94a3b8;
  font-weight: 500;
  letter-spacing: 1px;
}

.page-desc {
  font-size: 13px;
  color: #64748b;
  margin-top: 4px;
}

.main-content {
  flex: 1;
  min-height: 0;
}

.modern-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.card-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.table-layout {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;
}

.table-wrapper {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;

  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
  border: 1px solid #e2e8f0;
}

.table-header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.table-header-bar h4 {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: #334155;
  border-left: 4px solid #3b82f6;
  padding-left: 10px;
}

.user-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* 详情弹窗微调 */
.detail-tags-section {
  margin-top: 20px;
}

.tag-title {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 8px;
}

.tag-container {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

/* 覆盖 Element 表格的一些默认样式使其更清爽 */
:deep(.el-table) {
  --el-table-header-bg-color: #f1f5f9;
  font-size: 13px;
}

:deep(.el-table__header th) {
  color: #475569;
  font-weight: 700;
}
</style>