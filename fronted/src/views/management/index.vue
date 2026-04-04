<template>
  <div class="page-container">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title">模型注册 <span class="en-title">Model Registry</span></h1>
        <p class="page-desc">
          上传预训练模型并定义特征契约。确保勾选的特征列与模型训练时的维度完全一致。
        </p>
      </div>

      <div class="header-right" v-if="isFromWorkflow">
        <el-button type="warning" plain @click="handleBackToWorkflow">
          <el-icon style="margin-right: 4px;"><ArrowLeft /></el-icon>
          返回工作流 (步骤 {{ parseInt(route.query.step) + 1 }})
        </el-button>
      </div>
    </div>

    <div class="main-content">
      <div class="modern-card glass-effect">
        <div class="card-body">

          <div class="tool-bar">
            <el-button type="info" plain icon="Download" size="small" @click="downloadStandardHeader">
              下载系统标准表头 (.csv)
            </el-button>
            <el-tag type="warning" class="hint-tag" effect="light">
              提示：模型输入维度必须与下方注册的特征列对齐
            </el-tag>
          </div>

          <div class="form-wrapper">
            <el-form :model="form" ref="formRef" label-position="top" class="model-form" size="small">
              <el-row :gutter="20">
                <el-col :span="6">
                  <el-form-item label="模型名称" prop="model_name" required>
                    <el-input v-model="form.model_name" placeholder="例如：GBDT-强度预测"></el-input>
                  </el-form-item>
                </el-col>

                <el-col :span="12">
                  <el-form-item label="特征列 (特征契约定义)" prop="features" required>
                    <el-select
                        v-model="form.features"
                        multiple
                        filterable
                        collapse-tags
                        collapse-tags-indicator
                        placeholder="请勾选该模型使用的特征列"
                        style="width: 100%"
                    >
                      <el-option v-for="item in availableColumns" :key="item" :label="item" :value="item" />
                    </el-select>
                  </el-form-item>
                </el-col>

                <el-col :span="6">
                  <el-form-item label="预测目标 (Target)" prop="target">
                    <el-select v-model="form.target" placeholder="选择目标列" style="width: 100%">
                      <el-option v-for="item in availableColumns" :key="item" :label="item" :value="item" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>

              <el-row :gutter="20" align="bottom">
                <el-col :span="10">
                  <el-form-item label="描述信息">
                    <el-input v-model="form.description" placeholder="简述模型算法或参数版本"></el-input>
                  </el-form-item>
                </el-col>
                <el-col :span="10">
                  <el-form-item label="模型文件 (.pkl)">
                    <div class="upload-area">
                      <input type="file" @change="handleFileChange" accept=".pkl" id="file-input" />
                    </div>
                  </el-form-item>
                </el-col>
                <el-col :span="4" style="text-align: right; padding-bottom: 12px;">
                  <el-button type="primary" size="default" @click="submitForm" icon="CirclePlus" :loading="submitLoading">
                    确认注册
                  </el-button>
                </el-col>
              </el-row>
            </el-form>
          </div>

          <div class="table-wrapper">
            <div class="table-header-bar">
              <h4>已注册模型仓库</h4>
            </div>

            <el-table :data="models" stripe height="100%" v-loading="loading" class="custom-table">
              <el-table-column type="index" label="#" width="50"/>
              <el-table-column prop="model_name" label="模型名称" min-width="150" show-overflow-tooltip/>
              <el-table-column label="输入维度" width="100">
                <template #default="scope">
                  <el-tooltip :content="scope.row.features.join(', ')" placement="top">
                    <el-tag size="small" effect="plain">{{ scope.row.features?.length || 0 }} 维</el-tag>
                  </el-tooltip>
                </template>
              </el-table-column>
              <el-table-column prop="target" label="目标" width="100" />
              <el-table-column prop="status" label="状态" width="100">
                <template #default="scope">
                  <el-tag size="small" :type="scope.row.status === 'evaluated' ? 'success' : 'info'">
                    {{ scope.row.status }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="R² 评分" min-width="120">
                <template #default="scope">
                  <el-tooltip
                    v-if="scope.row.metrics?.r2_score != null && scope.row.metrics?.r2_score !== undefined"
                    :disabled="scope.row.metrics?.r2_score_strength == null"
                    placement="top"
                  >
                    <template #content>
                      <span v-if="scope.row.metrics?.r2_score_strength != null">
                        强度 R²: {{ scope.row.metrics.r2_score_strength.toFixed(4) }}<br/>
                        延伸率 R²: {{ scope.row.metrics.r2_score_elongation.toFixed(4) }}<br/>
                        样本数: {{ scope.row.metrics.n_samples ?? '-' }}
                      </span>
                    </template>
                    <span class="r2-score">{{ Number(scope.row.metrics.r2_score).toFixed(4) }}</span>
                  </el-tooltip>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column label="注册时间" width="160">
                <template #default="scope">
                  {{ new Date(scope.row.created_at).toLocaleString() }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="220" fixed="right">
                <template #default="scope">
                  <el-button v-if="isFromWorkflow" type="success" link @click="selectAndReturn(scope.row)">选择模型</el-button>
                  <el-button link type="primary" @click="evaluateModel(scope.row)">重新评估</el-button>
                  <el-divider direction="vertical" />
                  <el-button link type="danger" @click="handleDelete(scope.row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>

        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, Warning, Upload, CirclePlus, ArrowLeft } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()

/* ================= 状态 ================= */
const formRef = ref(null)
const form = ref({
  model_name: '',
  features: [],
  target: '',
  description: '',
  model_file: null,
})

const models = ref([])
const availableColumns = ref([])
const loading = ref(false)
const submitLoading = ref(false)

const API_BASE = 'http://127.0.0.1:8000/api/v1/models'
const config = {
  headers: { 'token': localStorage.getItem('token') }
}

/* ================= 路由联动逻辑 (方案 B) ================= */

// 判断是否从工作流跳转而来
const isFromWorkflow = computed(() => route.query.from === 'cases')

// 返回工作流
const handleBackToWorkflow = () => {
  router.push({ path: '/cases', query: route.query })
}

// 选择并返回 ID
const selectAndReturn = (row) => {
  ElMessage.success(`已应用模型: ${row.model_name}`)
  router.push({
    path: '/cases',
    query: {
      ...route.query,
      selectedId: row.id // 同样传回 selectedId
    }
  })
}

/* ================= API 调用 ================= */

async function fetchColumns() {
  try {
    const res = await axios.get(`${API_BASE}/columns`, config)
    availableColumns.value = res.data.columns
  } catch (err) {
    ElMessage.error('无法获取特征库列表')
  }
}

function downloadStandardHeader() {
  if (availableColumns.value.length === 0) return
  const content = availableColumns.value.join(',')
  const blob = new Blob([content], { type: 'text/csv' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.setAttribute('download', 'system_standard_header.csv')
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

function handleFileChange(event) {
  const files = event.target.files
  if (files.length > 0) form.value.model_file = files[0]
}

async function submitForm() {
  if (!form.value.model_name || !form.value.model_file || form.value.features.length === 0) {
    ElMessage.warning('请填写模型名称并上传 .pkl 文件')
    return
  }

  submitLoading.value = true
  const formData = new FormData()
  formData.append('model_file', form.value.model_file)
  formData.append('model_name', form.value.model_name)
  formData.append('features', form.value.features.join(','))
  formData.append('target', form.value.target)
  formData.append('description', form.value.description)

  try {
    await axios.post(`${API_BASE}/register`, formData, {
      headers: { ...config.headers, 'Content-Type': 'multipart/form-data' },
    })
    ElMessage.success('模型注册成功')
    resetForm()
    fetchModels()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '注册失败')
  } finally {
    submitLoading.value = false
  }
}

async function fetchModels() {
  loading.value = true
  try {
    const res = await axios.get(API_BASE, config)
    models.value = res.data.data || []
  } catch (err) {
    ElMessage.error('加载列表失败')
  } finally {
    loading.value = false
  }
}

async function evaluateModel(model) {
  try {
    await axios.post(`${API_BASE}/${model.id}/evaluate`, {}, config)
    ElMessage.success(`评估完成`)
    fetchModels()
  } catch (err) {
    ElMessage.error('评估失败')
  }
}

async function handleDelete(model) {
  try {
    await ElMessageBox.confirm(`确定删除 "${model.model_name}" 吗？`, '警告', { type: 'warning' })
    await axios.delete(`${API_BASE}/${model.id}`, config)
    ElMessage.success('已删除')
    fetchModels()
  } catch {}
}

function resetForm() {
  form.value = { model_name: '', features: [], target: '', description: '', model_file: null }
  const fileInput = document.getElementById('file-input')
  if (fileInput) fileInput.value = ''
}

onMounted(() => {
  fetchColumns()
  fetchModels()
})
</script>

<style scoped>
/* 延续 Dataset 页面的 Flex 布局 */
.page-container {
  height: calc(100vh - 84px);
  padding: 16px 24px;
  background: #f8fafc;
  display: flex;
  flex-direction: column;
}

.page-header {
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title { font-size: 22px; font-weight: 800; color: #1e293b; margin: 0; }
.en-title { font-size: 13px; margin-left: 10px; color: #94a3b8; font-weight: 500; letter-spacing: 1px; }
.page-desc { font-size: 13px; color: #64748b; margin-top: 4px; }

.main-content {
  flex: 1;
  min-height: 0;
}

.modern-card {
  height: 100%;
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 4px 12px rgba(0,0,0,0.03);
  display: flex;
  flex-direction: column;
}

.card-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 20px;
  min-height: 0;
}

.tool-bar {
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.hint-tag {
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.form-wrapper {
  background: #fcfdfe;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  border: 1px solid #f1f5f9;
}

.table-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.table-header-bar {
  margin-bottom: 12px;
  border-left: 4px solid #3b82f6;
  padding-left: 10px;
}
.table-header-bar h4 { margin: 0; font-size: 15px; color: #334155; }

.r2-score { font-weight: 700; color: #3b82f6; }

.upload-area {
  border: 1px dashed #cbd5e1;
  padding: 4px 10px;
  border-radius: 4px;
  background: #f8fafc;
  font-size: 12px;
}

.custom-table :deep(.el-table__header th) {
  background-color: #f8fafc !important;
  color: #475569;
  font-weight: 700;
  font-size: 13px;
}

.glass-effect { background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(8px); }
</style>