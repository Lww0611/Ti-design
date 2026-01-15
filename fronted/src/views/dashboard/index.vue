<template>
  <div class="dashboard-hero">
    <!-- Hero 区 -->
    <section class="hero-section">
      <div class="hero-content">
        <h1 class="hero-title">钛合金智能研发平台</h1>
        <p class="hero-subtitle">
          Intelligent Titanium Alloy Design & Performance Prediction System
        </p>
        <div class="hero-tag">
          <el-tag effect="dark" round type="info">AI Powered</el-tag>
          <el-tag
              effect="dark"
              round
              type="primary"
              style="margin-left: 12px"
          >
            Data Driven
          </el-tag>
        </div>
      </div>
    </section>

    <!-- 功能导航 -->
    <section class="nav-grid-container">
      <el-row :gutter="28">
        <el-col
            :span="6"
            v-for="(item, index) in navs"
            :key="index"
        >
          <div class="nav-card" @click="$router.push(item.path)">
            <div
                class="nav-icon-wrapper"
                :style="{ background: item.color }"
            >
              <el-icon>
                <component :is="item.icon" />
              </el-icon>
            </div>

            <h3 class="nav-title">{{ item.title }}</h3>
            <p class="nav-desc">{{ item.desc }}</p>

            <div class="nav-arrow">
              <el-icon><Right /></el-icon>
            </div>
          </div>
        </el-col>
      </el-row>
    </section>

    <!-- 系统状态 -->
    <footer class="system-footer">
      <span class="status-item">
        <span class="dot pulse"></span>
        Compute Cluster: Online
      </span>
      <span class="status-item">
        <span class="dot"></span>
        DB Schema: v2.4.0
      </span>
      <span class="status-item">
        <span class="dot"></span>
        Active Node: GPU-Node-01
      </span>
    </footer>
  </div>
</template>

<script setup>
import {
  Compass,
  Odometer,
  Histogram,
  Collection,
  Right
} from '@element-plus/icons-vue'

const navs = [
  {
    title: '性能正向预测',
    desc: '基于给定成分与工艺条件，预测力学性能。',
    path: '/forward',
    icon: Compass,
    color: 'linear-gradient(135deg, #4f8cff 0%, #3b5bdc 100%)'
  },
  {
    title: '成分逆向设计',
    desc: '输入目标性能指标，反推出可行的合金成分设计方案。',
    path: '/inverse',
    icon: Odometer,
    color: 'linear-gradient(135deg, #4f8cff 0%, #3b5bdc 100%)'
  },
  {
    title: '多方案对比分析',
    desc: '对不同设计方案进行可视化对比分析，辅助科研决策。',
    path: '/comparison',
    icon: Histogram,
    color: 'linear-gradient(135deg, #3aaed8 0%, #2b7de9 100%)'
  },
  {
    title: '实验历史回溯',
    desc: '集中管理历史预测与设计记录，支持筛选与导出。',
    path: '/history',
    icon: Collection,
    color: 'linear-gradient(135deg, #3aaed8 0%, #2b7de9 100%)'
  }
]
</script>

<style scoped>
/* 整体布局 */
.dashboard-hero {
  min-height: calc(100vh - 110px);
  display: flex;
  padding:16px;
  flex-direction: column;
  background-color: #f8fafc;
}

/* Hero 区 */
.hero-section {
  height: 420px;
  background:
      linear-gradient(rgba(15, 23, 42, 0.55), rgba(15, 23, 42, 0.55)),
      url('@/assets/hero-bg.jpg') center/cover no-repeat;
  border-radius: 16px;
  display: flex;
  align-items: center;
  padding: 0 64px;
  margin-bottom: 42px;
  color: #fff;
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.25);
}

.hero-title {
  font-size: 40px;
  font-weight: 600;
  margin: 0;
  letter-spacing: 1px;
}

.hero-subtitle {
  margin: 14px 0 26px;
  font-size: 17px;
  font-weight: 300;
  opacity: 0.88;
}

/* 功能卡片区 */
.nav-grid-container {
  padding: 0 8px;
}

.nav-card {
  height: 220px;
  background: #ffffff;
  border-radius: 14px;
  border: 1px solid #e5e7eb;
  padding: 28px 22px;
  text-align: center;
  cursor: pointer;
  position: relative;
  transition: all 0.25s ease;
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
}

.nav-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 18px 30px rgba(15, 23, 42, 0.12);
}

.nav-icon-wrapper {
  width: 68px;
  height: 68px;
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 32px;
  margin: 0 auto 18px;
}

.nav-title {
  font-size: 17px;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 10px;
}

.nav-desc {
  font-size: 13px;
  color: #64748b;
  line-height: 1.6;
  margin: 0;
}

.nav-arrow {
  position: absolute;
  bottom: 14px;
  right: 18px;
  color: #cbd5e1;
  font-size: 20px;
  transition: color 0.2s;
}

.nav-card:hover .nav-arrow {
  color: #3b82f6;
}

/* 系统状态栏 */
.system-footer {
  margin-top: auto;
  padding: 18px 0;
  border-top: 1px solid #e2e8f0;
  display: flex;
  justify-content: center;
  gap: 32px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #94a3b8;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #94a3b8;
}

.dot.pulse {
  background: #22c55e;
  box-shadow: 0 0 0 rgba(34, 197, 94, 0.5);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.6); }
  70% { box-shadow: 0 0 0 10px rgba(34, 197, 94, 0); }
  100% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }
}
</style>
