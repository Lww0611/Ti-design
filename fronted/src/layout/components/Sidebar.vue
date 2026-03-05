<template>
  <el-aside
      :width="isCollapse ? '64px' : '220px'"
      class="sidebar-container"
  >
    <!-- Logo 区 -->
    <div class="logo-area" @click="goHome">
      <el-icon class="logo-icon" :size="22">
        <OfficeBuilding />
      </el-icon>

      <div v-if="!isCollapse" class="logo-text-group">
        <div class="logo-title">Ti-Design</div>
        <div class="logo-subtitle">Titanium Alloy Lab</div>
      </div>
    </div>

    <!-- 菜单 -->
    <el-menu
        :default-active="$route.path"
        :collapse="isCollapse"
        router
        class="el-menu-vertical"
    >

      <el-menu-item index="/cases">
        <el-icon><Compass /></el-icon>
        <template #title>工作流管理</template>
      </el-menu-item>

      <el-menu-item index="/datasets">
        <el-icon><Compass /></el-icon>
        <template #title>数据集管理</template>
      </el-menu-item>

      <el-menu-item index="/management">
        <el-icon><Compass /></el-icon>
        <template #title>模型管理</template>
      </el-menu-item>

      <el-menu-item index="/forward">
        <el-icon><Compass /></el-icon>
        <template #title>性能正向预测</template>
      </el-menu-item>

      <el-menu-item index="/inverse">
        <el-icon><Odometer /></el-icon>
        <template #title>成分逆向设计</template>
      </el-menu-item>

      <el-menu-item index="/comparison">
        <el-icon><Histogram /></el-icon>
        <template #title>方案对比分析</template>
      </el-menu-item>

      <el-menu-item index="/history">
        <el-icon><Collection /></el-icon>
        <template #title>实验历史记录</template>
      </el-menu-item>

    </el-menu>
  </el-aside>
</template>

<script setup>
import {useRouter} from "vue-router"
import {
  OfficeBuilding,
  Compass,
  Odometer,
  Histogram,
  Collection
} from "@element-plus/icons-vue"

defineProps({
  isCollapse:{
    type:Boolean,
    default:false
  }
})

const router=useRouter()
const goHome=()=>{
  router.push("/dashboard")
}
</script>

<style scoped>
.sidebar-container{
  height:100%;
  background:linear-gradient(180deg,#1f2a37 0%,#111827 100%);
  transition:width 0.25s ease;
  overflow:hidden;
  box-shadow:inset -1px 0 0 rgba(255,255,255,0.05);
}

.logo-area{
  height:72px;
  display:flex;
  align-items:center;
  padding:0 16px;
  gap:12px;
  color:#fff;
  background:rgba(255,255,255,0.02);
  cursor:pointer;
}

.logo-area:hover{
  background:rgba(255,255,255,0.06);
}

.logo-icon{
  color:#60a5fa;
}

.logo-text-group{
  display:flex;
  flex-direction:column;
  line-height:1.1;
}

.logo-title{
  font-size:16px;
  font-weight:600;
  letter-spacing:1px;
}

.logo-subtitle{
  font-size:12px;
  color:#94a3b8;
}

.el-menu-vertical{
  border-right:none;
  background:transparent;
  margin-top:8px;
}

:deep(.el-menu-item){
  height:56px;
  line-height:56px;
  margin:4px 8px;
  border-radius:8px;
  color:#94a3b8;
  font-size:15px;
  transition:all 0.2s ease;
}

:deep(.el-menu-item .el-icon){
  color:#60a5fa;
  font-size:18px;
  margin-right:6px;
}

:deep(.el-menu-item:hover){
  background:rgba(255,255,255,0.06);
  color:#e5e7eb;
}

:deep(.el-menu-item.is-active){
  background:rgba(59,130,246,0.15);
  color:#ffffff;
  position:relative;
}

:deep(.el-menu-item.is-active::before){
  content:'';
  position:absolute;
  left:-8px;
  top:10%;
  width:3px;
  height:80%;
  background:#3b82f6;
  border-radius:2px;
}

:deep(.el-menu-item.is-active .el-icon){
  color:#93c5fd;
}
</style>