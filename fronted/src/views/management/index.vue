<template>
  <div class="page-container">
    <div class="page-header">
      <h1 class="page-title">模型注册 <span class="en-title">Model Registry</span></h1>
      <p class="page-desc">
        上传模型并与系统数据集对齐。通过勾选标准特征列，建立模型评估的“契约”。
      </p>
    </div>

    <div class="main-content">
      <div class="modern-card">
        <div class="card-body">

          <div class="tool-bar">
            <el-button type="info" plain icon="Download" @click="downloadStandardHeader">
              下载系统标准表头 (.csv)
            </el-button>
            <el-tag type="warning" class="hint-tag">注意：注册模型时选择的特征必须与训练该模型时的输入维度完全一致</el-tag>
          </div>

          <div class="form-wrapper">
            <el-form :model="form" ref="formRef" label-position="top" class="model-form">
              <el-row :gutter="20">
                <el-col :span="6">
                  <el-form-item label="模型名称" prop="model_name">
                    <el-input v-model="form.model_name" placeholder="例如：GBDT-强度预测模型"></el-input>
                  </el-form-item>
                </el-col>

                <el-col :span="12">
                  <el-form-item label="特征列 (多选)" prop="features">
                    <el-select
                        v-model="form.features"
                        multiple
                        filterable
                        collapse-tags
                        collapse-tags-indicator
                        placeholder="请勾选该模型使用的特征列"
                        style="width: 100%"
                    >
                      <el-option
                          v-for="item in availableColumns"
                          :key="item"
                          :label="item"
                          :value="item"
                      />
                    </el-select>
                  </el-form-item>
                </el-col>

                <el-col :span="6">
                  <el-form-item label="目标列 (预测目标)" prop="target">
                    <el-select v-model="form.target" placeholder="请选择预测目标" style="width: 100%">
                      <el-option
                          v-for="item in availableColumns"
                          :key="item"
                          :label="item"
                          :value="item"
                      />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>

              <el-row :gutter="20" align="bottom">
                <el-col :span="12">
                  <el-form-item label="描述信息">
                    <el-input v-model="form.description" placeholder="可选：简述模型算法或参数"></el-input>
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="模型文件 (.pkl)">
                    <div class="upload-area">
                      <input type="file" @change="handleFileChange" accept=".pkl" id="file-input" />
                    </div>
                  </el-form-item>
                </el-col>
                <el-col :span="4" style="text-align: right; padding-bottom: 18px;">
                  <el-button type="primary" size="large" @click="submitForm" icon="Upload" :loading="submitLoading">
                    确认注册
                  </el-button>
                </el-col>
              </el-row>
            </el-form>
          </div>

          <div class="table-wrapper">
            <div class="table-header-bar">
              <h4>已注册模型列表</h4>
            </div>

            <el-table :data="models" stripe height="350" v-loading="loading">
              <el-table-column type="index" label="序号" width="60"/>
              <el-table-column prop="model_name" label="模型名称" min-width="150"/>
              <el-table-column label="特征维度" width="100">
                <template #default="scope">
                  <el-tooltip :content="scope.row.features.join(', ')" placement="top">
                    <el-tag>{{ scope.row.features?.length || 0 }} 维</el-tag>
                  </el-tooltip>
                </template>
              </el-table-column>
              <el-table-column prop="target" label="目标列" width="120" />
              <el-table-column prop="status" label="状态" width="100">
                <template #default="scope">
                  <el-tag :type="scope.row.status === 'evaluated' ? 'success' : 'info'">
                    {{ scope.row.status }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="R² 结果" width="120">
                <template #default="scope">
                  <span class="r2-score" v-if="scope.row.metrics?.r2_score">
                    {{ scope.row.metrics.r2_score.toFixed(4) }}
                  </span>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column label="创建时间" width="180">
                <template #default="scope">
                  {{ new Date(scope.row.created_at).toLocaleString() }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="180" fixed="right">
                <template #default="scope">
                  <el-button link type="primary" @click="evaluateModel(scope.row)">评估</el-button>
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
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const formRef = ref(null)
const form = ref({
  model_name: '',
  features: [], // 现在是数组形式
  target: '',
  description: '',
  model_file: null,
})

const models = ref([])
const availableColumns = ref([]) // 存储从后端获取的 newdata3.csv 表头
const loading = ref(false)
const submitLoading = ref(false)

const API_BASE = 'http://127.0.0.1:8000/api/v1/models'
const config = {
  headers: { 'token': localStorage.getItem('token') }
}

// --- 新增逻辑：获取系统可用列名 ---
async function fetchColumns() {
  try {
    const res = await axios.get(`${API_BASE}/columns`, config)
    availableColumns.value = res.data.columns
  } catch (err) {
    ElMessage.error('无法获取系统特征列表，请检查后端连接')
  }
}

// --- 新增逻辑：下载标准表头供用户训练参考 ---
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

// 1. 上传并注册模型 (发送前将数组转为逗号字符串)
async function submitForm() {
  if (!form.value.model_name || !form.value.model_file || form.value.features.length === 0) {
    ElMessage.warning('请完整填写模型信息（包含特征勾选）！')
    return
  }

  submitLoading.value = true
  const formData = new FormData()
  formData.append('model_file', form.value.model_file)
  formData.append('model_name', form.value.model_name)
  // 将选中的数组转回后端需要的 CSV 格式字符串
  formData.append('features', form.value.features.join(','))
  formData.append('target', form.value.target)
  formData.append('description', form.value.description)

  try {
    await axios.post(`${API_BASE}/register`, formData, {
      headers: { ...config.headers, 'Content-Type': 'multipart/form-data' },
    })
    ElMessage.success('模型已通过校验并成功注册')
    resetForm()
    fetchModels()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '注册失败')
  } finally {
    submitLoading.value = false
  }
}

// 2. 获取模型列表
async function fetchModels() {
  loading.value = true
  try {
    const res = await axios.get(API_BASE, config)
    models.value = res.data.data || []
  } catch (err) {
    ElMessage.error('加载模型列表失败')
  } finally {
    loading.value = false
  }
}

// 3. 评估模型
async function evaluateModel(model) {
  try {
    await axios.post(`${API_BASE}/${model.id}/evaluate`, {}, config)
    ElMessage.success(`模型 "${model.model_name}" 评估完成`)
    fetchModels()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '评估失败')
  }
}

// 4. 删除模型
async function handleDelete(model) {
  try {
    await ElMessageBox.confirm(`确定删除模型 "${model.model_name}" 吗？`, '警告', { type: 'warning' })
    await axios.delete(`${API_BASE}/${model.id}`, config)
    ElMessage.success('删除成功')
    fetchModels()
  } catch (err) {
    if (err !== 'cancel') ElMessage.error('删除失败')
  }
}

function resetForm() {
  form.value = { model_name: '', features: [], target: '', description: '', model_file: null }
  const fileInput = document.getElementById('file-input')
  if (fileInput) fileInput.value = ''
}

onMounted(() => {
  fetchColumns() // 挂载时加载可用特征
  fetchModels()
})
</script>

<style scoped>
.page-container {
  height: calc(100vh - 84px);
  padding: 16px 24px;
  background: #f5f7fa;
  display: flex;
  flex-direction: column;
}

.page-title { font-size: 24px; font-weight: 700; color: #1a1a1a; margin: 0; }
.en-title { font-size: 14px; margin-left: 10px; color: #909399; font-weight: 400; }
.page-desc { font-size: 14px; color: #606266; margin-top: 8px; margin-bottom: 20px;}

.tool-bar {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.hint-tag { font-weight: normal; }

.form-wrapper {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  border: 1px solid #ebeef5;
}

.table-wrapper {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.05);
  flex: 1;
  display: flex;
  flex-direction: column;
}

.table-header-bar {
  margin-bottom: 16px;
  border-left: 4px solid #409eff;
  padding-left: 12px;
}

.r2-score { font-weight: bold; color: #409eff; }

.upload-area {
  border: 1px dashed #dcdfe6;
  padding: 5px 10px;
  border-radius: 4px;
  background: #fafafa;
}

:deep(.el-form-item__label) {
  font-weight: 600;
  padding-bottom: 4px !important;
}
</style>