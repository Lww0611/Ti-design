<template>
  <el-container class="layout-container">
    <!-- 左侧侧边栏 -->
    <Sidebar :is-collapse="isCollapse" />

    <!-- 右侧区域 -->
    <el-container class="right-section">
      <Navbar
          :is-collapse="isCollapse"
          @toggle-collapse="isCollapse = !isCollapse"
      />

      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref } from 'vue'
import Sidebar from './components/Sidebar.vue'
import Navbar from './components/Navbar.vue'

const isCollapse = ref(false)
</script>

<style scoped>
/* Layout 文件的修改 */
.layout-container {
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  /* 关键点 1：将底色改为深色，这样就算侧边栏没撑满，下方也是深色的 */
  background-color: #001529;
}

/* 如果你的侧边栏组件没有自动撑满，给它强制高度 */
:deep(.el-aside) {
  height: 100%;
  background-color: #001529; /* 确保颜色与侧边栏一致 */
}

.right-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  /* 关键：把背景图从子页面移到这里，让 Navbar 也能共用背景 */
  background:
      linear-gradient(to bottom right, rgba(15, 23, 42, 0.8), rgba(15, 23, 42, 0.9)),
      url('@/assets/forward-bg.jpg') no-repeat center center / cover;
}

.navbar {
  background: transparent !important; /* 导航栏设为透明 */
  border-bottom: 1px solid rgba(255, 255, 255, 0.1); /* 添加极细的白边分割 */
  color: #fff; /* 文字改白色 */
}

.app-main {
  padding: 0; /* 彻底移除间距 */
  background: transparent; /* 移除原来的灰色背景 */
}
</style>
