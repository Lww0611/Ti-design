<template>
  <el-header class="navbar">
    <!-- 左侧 -->
    <div class="header-left">
      <el-button type="text" @click="$emit('toggle-collapse')">
        <el-icon :size="22">
          <Fold v-if="!isCollapse" />
          <Expand v-else />
        </el-icon>
      </el-button>

      <el-breadcrumb separator="/">
        <el-breadcrumb-item>系统</el-breadcrumb-item>
        <el-breadcrumb-item>
          {{ $route.meta.title }}
        </el-breadcrumb-item>
      </el-breadcrumb>
    </div>

    <!-- 右侧 -->
    <div class="header-right">
      <el-tag class="version-tag" effect="plain">Beta · v1.2</el-tag>

      <el-dropdown trigger="click" @command="handleCommand">
        <div class="user-profile">
          <el-avatar :size="28" icon="UserFilled" />
          <span class="user-name">Researcher</span>
          <el-icon><ArrowDown /></el-icon>
        </div>

        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">
              <el-icon><User /></el-icon>
              个人中心
            </el-dropdown-item>
            <el-dropdown-item command="logout" divided>
              <el-icon><SwitchButton /></el-icon>
              退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </el-header>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { ElMessageBox, ElMessage } from 'element-plus'
import {
  Fold,
  Expand,
  ArrowDown,
  User,
  SwitchButton
} from '@element-plus/icons-vue'

defineProps({
  isCollapse: Boolean
})

const router = useRouter()

const handleCommand = (command) => {
  if (command === 'logout') {
    ElMessageBox.confirm(
        '您确定要退出钛合金科研平台吗？',
        '提示',
        { type: 'warning' }
    ).then(() => {
      router.push('/login')
      ElMessage.success('已安全退出')
    })
  }
}
</script>

<style scoped>
.navbar {
  height: 64px;
  background: linear-gradient(180deg, #ffffff, #f7f9fc);
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
}

.header-left,
.header-right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.version-tag {
  font-size: 12px;
  opacity: 0.7;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}

.user-name {
  font-size: 14px;
  color: #374151;
}

/* 面包屑 */
:deep(.el-breadcrumb__inner) {
  font-size: 15px;
  color: #6b7280;
}

:deep(.el-breadcrumb__item:last-child .el-breadcrumb__inner) {
  color: #111827;
  font-weight: 600;
}
</style>
