<template>
  <div class="login-page">
    <!-- 全屏背景遮罩 -->
    <div class="bg-overlay"></div>

    <!-- 左侧平台介绍 -->
    <div class="login-left">
      <h1>Ti-Design</h1>
      <h3>钛合金智能设计与性能预测平台</h3>
      <p>
        面向材料科学与工程应用的科研平台，<br />
        支持钛合金成分设计、热加工与热处理工艺建模，<br />
        以及力学性能的智能预测与逆向设计。
      </p>
    </div>

    <!-- 右侧登录功能面板 -->
    <div class="login-right">
      <div class="right-header">
        <h2>欢迎使用</h2>
        <p>Ti-Design Research Platform</p>
      </div>

      <div class="right-main">
        <el-tabs v-model="activeTab" stretch>
          <el-tab-pane label="账号登录" name="login">
            <el-form :model="loginForm" label-position="top">
              <el-form-item label="用户名 / 邮箱">
                <el-input v-model="loginForm.username" />
              </el-form-item>
              <el-form-item label="密码">
                <el-input
                    v-model="loginForm.password"
                    type="password"
                    show-password
                />
              </el-form-item>
              <el-button
                  type="primary"
                  class="submit-btn btn-primary"
                  @click="handleLogin"
              >
                进入系统
              </el-button>
            </el-form>
          </el-tab-pane>

          <el-tab-pane label="申请注册" name="register">
            <el-form :model="registerForm" label-position="top">
              <el-form-item label="姓名">
                <el-input v-model="registerForm.name" />
              </el-form-item>
              <el-form-item label="所属实验室 / 机构">
                <el-input v-model="registerForm.lab" />
              </el-form-item>
              <el-form-item label="设置密码">
                <el-input v-model="registerForm.password" type="password" />
              </el-form-item>
              <el-button class="submit-btn btn-register" @click="handleRegister">
                提交注册申请
              </el-button>
            </el-form>
          </el-tab-pane>
        </el-tabs>
      </div>

      <div class="right-footer">
        <el-checkbox v-model="rememberMe">记住登录状态</el-checkbox>
        <span>© Ti-Design Materials Lab</span>
      </div>
    </div>
  </div>
</template>


<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const router = useRouter()
const activeTab = ref('login')
const rememberMe = ref(true)

/* =========================
   ✅ 创建 axios 实例
========================= */
const request = axios.create({
  baseURL: 'http://127.0.0.1:8000',
  timeout: 10000
})

/* =========================
   ✅ 请求拦截器（自动带 token）
========================= */
request.interceptors.request.use(
    config => {
      const token = localStorage.getItem('token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
      return config
    },
    error => Promise.reject(error)
)

/* =========================
   表单数据
========================= */
const loginForm = reactive({
  username: '',
  password: ''
})

const registerForm = reactive({
  name: '',
  lab: '',
  password: ''
})

/* =========================
   登录
========================= */
const handleLogin = async () => {
  if (!loginForm.username || !loginForm.password) {
    return ElMessage.warning('请输入账号和密码')
  }

  try {
    const res = await request.post('/api/v1/auth/login', {
      username: loginForm.username,
      password: loginForm.password
    })

    const { access_token, username } = res.data

    localStorage.setItem('token', access_token)

    ElMessage.success(`登录成功，欢迎 ${username}`)
    router.push('/dashboard')
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '登录失败')
  }
}

/* =========================
   注册
========================= */
const handleRegister = async () => {
  if (!registerForm.name || !registerForm.password) {
    return ElMessage.warning('请填写完整注册信息')
  }

  try {
    await request.post('/api/v1/auth/register', {
      username: registerForm.name,
      password: registerForm.password,
      lab: registerForm.lab
    })

    ElMessage.success('注册成功，请登录')
    activeTab.value = 'login'
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '注册失败')
  }
}
</script>

<style scoped>
/* 全屏背景 */
.login-page {
  position: relative;
  height: 100vh;
  width: 100%;
  background-image: url('@/assets/login-bg.jpg'); /* 你的蓝色背景图 */
  background-size: cover;
  background-position: center;
  overflow: hidden;
}

/* 深蓝渐变遮罩（科研风） */
.bg-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(
      120deg,
      rgba(10, 25, 45, 0.78),
      rgba(20, 40, 70, 0.55)
  );
}

/* 左侧平台介绍 */
.login-left {
  position: absolute;
  left: 0;
  top: 0;
  width: calc(100% - 560px); /* 给右侧让位 */
  height: 100%;
  padding: 100px 80px;
  box-sizing: border-box;
  z-index: 1;

  display: flex;
  flex-direction: column;
  justify-content: center;
}

.login-left h1 {
  font-size: 44px;
  font-weight: 600;
  letter-spacing: 1px;
  color: #ffffff;
}

.login-left h3 {
  margin-top: 16px;
  font-size: 22px;
  font-weight: 400;
  color: #cfe4ff; /* 浅蓝，和背景统一 */
}

.login-left p {
  margin-top: 36px;
  font-size: 16px;
  line-height: 1.9;
  color: rgba(255, 255, 255, 0.85);
  max-width: 520px;
}

/* 右侧半透明登录面板 */
.login-right {
  position: absolute;
  right: 0;
  top: 0;
  width: 560px;
  height: 100vh;
  z-index: 2;

  background: rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);

  display: flex;
  flex-direction: column;
  padding: 48px 42px;
  box-sizing: border-box;

  border-left: 1px solid rgba(255, 255, 255, 0.25);
  box-shadow: -20px 0 40px rgba(0, 0, 0, 0.35);
}

/* 右侧标题 */
.right-header h2 {
  font-size: 26px;
  font-weight: 600;
  color: #ffffff;
}

.right-header p {
  margin-top: 6px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.75);
}

/* 主区 */
.right-main {
  flex: 1;
  margin-top: 40px;
}

/* 表单适配深色背景 */
:deep(.el-form-item__label) {
  color: rgba(255, 255, 255, 0.85);
}

:deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.9);
}

/* 按钮 */
.submit-btn {
  width: 100%;
  height: 42px;
  font-size: 16px;
}

/* 底部 */
.right-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.75);
}

/* ===== 按钮整体 ===== */
.submit-btn {
  width: 100%;
  height: 44px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 8px;
  letter-spacing: 0.5px;
}

/* ===== 登录主按钮（科研蓝） ===== */
.btn-primary {
  background: linear-gradient(
      135deg,
      #2f74ff,
      #4b8cff
  );
  border: none;
  color: #ffffff;
}

.btn-primary:hover {
  background: linear-gradient(
      135deg,
      #245fd6,
      #3f7ce0
  );
}

/* ===== 注册按钮（青蓝科研色） ===== */
.btn-register {
  background: linear-gradient(
      135deg,
      #3bbcd6,
      #4cc9f0
  );
  border: none;
  color: #ffffff;
}

.btn-register:hover {
  background: linear-gradient(
      135deg,
      #30a7bf,
      #3fb6dc
  );
}

/* ===== Tabs 标题颜色优化 ===== */
:deep(.el-tabs__item) {
  color: rgba(255, 255, 255, 0.65);
  font-size: 15px;
}

:deep(.el-tabs__item.is-active) {
  color: #ffffff;
  font-weight: 500;
}

/* ===== 表单输入文字 ===== */
:deep(.el-input__inner) {
  color: #1f2d3d;
  font-size: 14px;
}

/* ===== Checkbox 文本 ===== */
:deep(.el-checkbox__label) {
  color: rgba(255, 255, 255, 0.8);
}

/* ===== Checkbox 未选中 ===== */
:deep(.el-checkbox__inner) {
  width: 16px;
  height: 16px;
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.45);
  background-color: transparent;
}

/* ===== Checkbox 选中 ===== */
:deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background-color: #2f74ff;   /* 科研蓝 */
  border-color: #2f74ff;
}

/* 勾选对号颜色 */
:deep(.el-checkbox__inner::after) {
  border-color: #ffffff;
}

/* Hover 状态 */
:deep(.el-checkbox__input:hover .el-checkbox__inner) {
  border-color: #4b8cff;
}

/* Checkbox 文本 */
:deep(.el-checkbox__label) {
  color: rgba(255, 255, 255, 0.8);
  font-size: 13px;
}

/* 选中时文本微强调 */
:deep(.el-checkbox__input.is-checked + .el-checkbox__label) {
  color: #ffffff;
}


</style>


