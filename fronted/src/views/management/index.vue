<template>
  <div class="page-container">
    <!-- 标题 -->
    <div class="page-header">
      <h1 class="page-title">模型注册 <span class="en-title">Model Registry</span></h1>
      <p class="page-desc">上传并注册模型，填写元信息后可保存到系统。</p>
    </div>

    <div class="main-content">
      <div class="modern-card">
        <div class="card-body">

          <!-- ================= 模型表单 ================= -->
          <div class="form-wrapper">
            <el-form :model="form" ref="formRef" label-width="120px" class="model-form">
              <el-form-item label="模型名称" prop="model_name">
                <el-input v-model="form.model_name" placeholder="输入模型名称"></el-input>
              </el-form-item>

              <el-form-item label="特征列" prop="features">
                <el-input
                    v-model="form.features"
                    placeholder="以逗号分隔，例如 Ti (wt%),Mo (wt%),Al (wt%)"
                ></el-input>
              </el-form-item>

              <el-form-item label="目标列" prop="target">
                <el-input v-model="form.target" placeholder="输入目标列"></el-input>
              </el-form-item>

              <el-form-item label="模型文件" prop="model_file">
                <input type="file" @change="handleFileChange" />
              </el-form-item>

              <el-form-item>
                <el-button type="primary" @click="submitForm">注册模型</el-button>
              </el-form-item>
            </el-form>
          </div>

          <!-- ================= 模型列表 ================= -->
          <div class="table-wrapper">
            <div class="table-header-bar">
              <h4>已注册模型</h4>
            </div>

            <el-table
                :data="models"
                stripe
                height="300"
                v-loading="loading"
            >
              <el-table-column type="index" label="ID" width="70"/>
              <el-table-column prop="model_name" label="模型名称"/>
              <el-table-column prop="features" label="特征"/>
              <el-table-column prop="target" label="目标"/>
              <el-table-column prop="status" label="状态"/>
              <el-table-column label="R²" width="100">
                <template #default="scope">
                  {{ scope.row.metrics?.r2_score ?? '-' }}
                </template>
              </el-table-column>
              <el-table-column label="MAE" width="100">
                <template #default="scope">
                  {{ scope.row.metrics?.mae ?? '-' }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="120">
                <template #default="scope">
                  <el-button link type="primary" @click="evaluateModel(scope.row)">评估</el-button>
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
import { ElMessage } from 'element-plus'

const formRef = ref(null)
const form = ref({
  model_name: '',
  features: '',
  target: '',
  model_file: null,
})

const models = ref([])
const loading = ref(false)

function handleFileChange(event) {
  const files = event.target.files
  if (files.length > 0) form.value.model_file = files[0]
}

// 上传模型
async function submitForm() {
  if (!form.value.model_file) {
    ElMessage.warning('请上传模型文件！')
    return
  }

  const formData = new FormData()
  formData.append('model_file', form.value.model_file)
  formData.append('model_name', form.value.model_name)
  formData.append('features', form.value.features)
  formData.append('target', form.value.target)

  try {
    const res = await axios.post('http://127.0.0.1:8000/api/models/register', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        'token': localStorage.getItem('token')
      },
    })
    ElMessage.success('模型注册成功')
    resetForm()
    fetchModels()
  } catch (err) {
    console.error(err)
    ElMessage.error(err.response?.data?.detail || '模型注册失败')
  }
}

function resetForm() {
  form.value.model_name = ''
  form.value.features = ''
  form.value.target = ''
  form.value.model_file = null
  if (formRef.value) formRef.value.resetFields()
}

// 获取模型列表
async function fetchModels() {
  loading.value = true
  try {
    const res = await axios.get('http://127.0.0.1:8000/api/models')
    models.value = Array.isArray(res.data.data) ? res.data.data : []
  } catch (err) {
    console.error(err)
    ElMessage.error('加载模型列表失败')
    models.value = []
  } finally {
    loading.value = false
  }
}

// 评估模型
async function evaluateModel(model) {
  try {
    const res = await axios.post(`http://127.0.0.1:8000/api/models/evaluate/${model.model_id}`)
    ElMessage.success(`模型 "${model.model_name}" 评估完成`)
    fetchModels()  // 刷新表格显示最新评估结果
  } catch (err) {
    console.error(err)
    ElMessage.error(err.response?.data?.detail || '模型评估失败')
  }
}

onMounted(() => {
  fetchModels()
})
</script>

<style scoped>
/* 样式保持不变 */
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
  min-height: 0;
}

.modern-card {
  display: flex;
  flex-direction: column;
}

.card-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;
}

.form-wrapper {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,.06);
}

.table-wrapper {
  flex: 1;
  min-height: 0;
  overflow: auto;
  background: #fff;
  border-radius: 12px;
  padding: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,.06);
}
</style>
