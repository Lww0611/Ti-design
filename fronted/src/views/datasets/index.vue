<template>
  <div class="page-container">
    <!-- 标题 -->
    <div class="page-header">
      <h1 class="page-title">数据集管理 <span class="en-title">Dataset Manager</span></h1>
      <p class="page-desc">管理平台内置与用户上传的数据集。</p>
    </div>

    <div class="main-content">
      <div class="modern-card">
        <div class="card-body table-layout">

          <!-- ================= 系统数据集 ================= -->
          <div class="table-wrapper">
            <div class="table-header-bar">
              <h4>系统数据集（只读）</h4>
            </div>

            <el-table
                :data="systemDatasets"
                stripe
                height="260"
                v-loading="loading"
            >
              <el-table-column type="index" label="ID" width="70"/>
              <el-table-column prop="name" label="名称"/>
              <el-table-column prop="n_rows" label="行数" width="90"/>
              <el-table-column prop="n_columns" label="列数" width="90"/>
              <el-table-column prop="missing_rate" label="缺失率" width="90"/>
              <el-table-column prop="created_at" label="创建时间" width="160"/>
              <el-table-column label="操作" width="140">
                <template #default="scope">
                  <el-button link type="primary" @click="viewDetail(scope.row)">详情</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <!-- ================= 用户数据集 ================= -->
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
                  <el-button type="primary">上传</el-button>
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
                height="320"
                v-loading="loading"
            >
              <el-table-column type="index" label="ID" width="70"/>
              <el-table-column prop="name" label="名称"/>
              <el-table-column prop="n_rows" label="行数" width="90"/>
              <el-table-column prop="n_columns" label="列数" width="90"/>
              <el-table-column prop="missing_rate" label="缺失率" width="90"/>
              <el-table-column prop="created_at" label="创建时间" width="160"/>
              <el-table-column label="操作" width="200">
                <template #default="scope">
                  <el-button link type="primary" @click="viewDetail(scope.row)">详情</el-button>
                  <el-button link type="danger" @click="deleteDataset(scope.row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>

          </div>

        </div>
      </div>
    </div>

    <!-- ================= 详情弹窗 ================= -->
    <el-dialog
        v-model="detailVisible"
        title="数据集详情"
        width="700px"
    >
      <el-descriptions :column="2" border>
        <el-descriptions-item label="ID">{{ datasetDetail.id }}</el-descriptions-item>
        <el-descriptions-item label="名称">{{ datasetDetail.name }}</el-descriptions-item>
        <el-descriptions-item label="文件名">{{ datasetDetail.filename }}</el-descriptions-item>
        <el-descriptions-item label="来源">{{ datasetDetail.source_type }}</el-descriptions-item>
        <el-descriptions-item label="行数">{{ datasetDetail.n_rows }}</el-descriptions-item>
        <el-descriptions-item label="列数">{{ datasetDetail.n_columns }}</el-descriptions-item>
        <el-descriptions-item label="缺失率">
          {{ datasetDetail.missing_rate }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ datasetDetail.created_at }}
        </el-descriptions-item>
      </el-descriptions>

      <el-divider />

      <div>
        <h4>数值列</h4>
        <div class="tag-container">
          <el-tag
              v-for="col in datasetDetail.numeric_columns || []"
              :key="col"
              size="small"
              type="success"
          >
            {{ col }}
          </el-tag>
        </div>
      </div>

      <div style="margin-top:12px">
        <h4>文本列</h4>
        <div class="tag-container">
          <el-tag
              v-for="col in datasetDetail.text_columns || []"
              :key="col"
              size="small"
              type="info"
          >
            {{ col }}
          </el-tag>
        </div>
      </div>

      <div style="margin-top:12px">
        <h4>可能目标列</h4>
        <div class="tag-container">
          <el-tag
              v-for="col in datasetDetail.target_candidates || []"
              :key="col"
              size="small"
              type="warning"
          >
            {{ col }}
          </el-tag>
        </div>
      </div>
    </el-dialog>

  </div>
</template>


<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

/* ================= 配置 ================= */
const API_BASE = 'http://127.0.0.1:8000/api'

/* ================= 状态 ================= */
const loading = ref(false)
const datasets = ref([])
const searchKeyword = ref('')

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

// 获取数据集列表
const fetchDatasets = async () => {
  loading.value = true
  try {
    const res = await axios.get(`${API_BASE}/datasets`)
    datasets.value = res.data.data || res.data
  } catch (err) {
    ElMessage.error('加载数据集失败')
  } finally {
    loading.value = false
  }
}

// 上传数据集
const handleUpload = async (file) => {
  const formData = new FormData()
  formData.append('file', file.raw)

  try {
    loading.value = true
    await axios.post(`${API_BASE}/datasets/upload`, formData)
    ElMessage.success('上传成功')
    fetchDatasets()
  } catch (err) {
    ElMessage.error('上传失败')
  } finally {
    loading.value = false
  }
}

// 查看详情
const detailVisible = ref(false)
const datasetDetail = ref({})

const viewDetail = async (row) => {
  try {
    const res = await axios.get(`${API_BASE}/datasets/${row.id}`)
    datasetDetail.value = res.data.data || res.data
    detailVisible.value = true
  } catch {
    ElMessage.error('获取详情失败')
  }
}

// 删除数据集
const deleteDataset = async (row) => {
  try {
    await ElMessageBox.confirm(
        `确认删除数据集 "${row.name}" ?`,
        '危险操作',
        { type: 'warning' }
    )

    await axios.delete(`${API_BASE}/datasets/${row.id}`)
    ElMessage.success('删除成功')
    fetchDatasets()
  } catch {
    // 用户取消不提示错误
  }
}

/* ================= 生命周期 ================= */
onMounted(() => {
  fetchDatasets()
})
</script>

<style scoped>
.page-container {
  height: calc(100vh - 84px);
  padding: 4px 24px;
  background: #f5f7fa;
  display: flex;
  flex-direction: column;
}

.page-header {
  margin-bottom: 12px;
}

.page-title {
  font-size: 22px;
  font-weight: 700;
}

.en-title {
  font-size: 13px;
  margin-left: 10px;
  color: #888;
}

.page-desc {
  font-size: 13px;
  color: #666;
}

.main-content {
  flex: 1;
  min-height: 0;   /* ⭐ 必须 */
}

.modern-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;   /* ⭐ 必须 */
}

.card-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;   /* ⭐ 必须 */
}

.table-layout {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;   /* ⭐ 必须 */
}

.table-wrapper {
  flex: 1;               /* ⭐ 平分高度 */
  min-height: 0;         /* ⭐ 允许内部滚动 */
  overflow: hidden;      /* 防止自身撑开 */
  display: flex;
  flex-direction: column;

  background: #fff;
  border-radius: 12px;
  padding: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,.06);
}


.table-header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.table-header-bar h4 {
  margin: 0;
  font-weight: 700;
}

.user-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.tag-container {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

</style>
