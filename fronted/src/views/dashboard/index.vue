<template>
  <div class="home-dashboard">

    <div class="user-bar">
      <el-tag class="version-tag" effect="plain">Beta · v1.2</el-tag>
      <el-dropdown trigger="click" @command="handleCommand">
        <div class="user-profile">
          <el-avatar :size="30" icon="UserFilled"/>
          <span class="user-name">Researcher</span>
          <el-icon><ArrowDown/></el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">
              <el-icon><User/></el-icon>
              Profile
            </el-dropdown-item>
            <el-dropdown-item command="logout" divided>
              <el-icon><SwitchButton/></el-icon>
              Logout
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>

    <section class="hero">
      <h1 class="hero-title">Titanium Alloy AI Research Platform</h1>
      <p class="hero-subtitle">
        AI-driven platform for titanium alloy design, property prediction and inverse alloy discovery.
      </p>
      <div class="hero-tags">
        <el-tag effect="dark" round>AI Powered</el-tag>
        <el-tag effect="dark" round type="primary">Data Driven</el-tag>
      </div>
    </section>

    <section class="module-nav">
      <div v-for="(item,index) in navs" :key="index" class="nav-link" @click="go(item.path)">
        {{item.title}}
      </div>
    </section>

    <div class="start-explore" @click="go('/cases')">
      <div class="explore-arrow">↓</div>
      <div class="explore-text">Start Exploring</div>
    </div>

  </div>
</template>

<script setup>
import {useRouter} from 'vue-router'
import {ElMessageBox,ElMessage} from 'element-plus'
import {ArrowDown,User,SwitchButton} from '@element-plus/icons-vue'
const router=useRouter()
const go=(path)=>{router.push(path)}
const handleCommand=(command)=>{
  if(command==="logout"){
    ElMessageBox.confirm("Are you sure to logout?","Confirm",{type:"warning"}).then(()=>{
      router.push("/login")
      ElMessage.success("Logged out")
    })
  }}
const navs=[
  {title:"Dataset Management",path:"/datasets"},
  {title:"Feature Engineering",path:"/feature"},
  {title:"Model Registry",path:"/management"},
  {title:"Model Evaluation",path:"/evaluation"},
  {title:"Property Prediction",path:"/forward"},
  {title:"Inverse Design",path:"/inverse"},
  {title:"Comparison Analysis",path:"/comparison"},
  {title:"Experiment History",path:"/history"}
]
</script>

<style scoped>
.home-dashboard{
  position: relative;
  height: 83vh;
  display:flex;
  flex-direction:column;
  justify-content:center;
  padding:80px;
  color:white;
  position:relative;
  background:linear-gradient(rgba(15,23,42,0.75),rgba(15,23,42,0.85)),url("@/assets/hero-bg.jpg") center/cover no-repeat;
}
.user-bar{
  position:absolute;
  top:40px;
  right:80px;
  display:flex;
  align-items:center;
  gap:16px;
}
.version-tag{
  font-size:12px;
}
.user-profile{
  display:flex;
  align-items:center;
  gap:8px;
  cursor:pointer;
}
.user-name{
  font-size:14px;
}
.hero{
  max-width:760px;
  margin-bottom:60px;
}
.hero-title{
  font-size:46px;
  font-weight:600;
  letter-spacing:1px;
}
.hero-subtitle{
  margin-top:18px;
  font-size:18px;
  opacity:0.85;
  line-height:1.7;
}
.hero-tags{
  margin-top:24px;
  display:flex;
  gap:14px;
}
.module-nav{
  display:flex;
  flex-wrap:wrap;
  gap:36px;
  max-width:900px;
}
.nav-link{
  font-size:16px;
  cursor:pointer;
  opacity:0.85;
  transition:0.25s;
  border-bottom:1px solid rgba(255,255,255,0.3);
  padding-bottom:4px;
}
.nav-link:hover{
  opacity:1;
  transform:translateY(-2px);
  border-color:white;
}
.start-explore{
  position:absolute;
  bottom:40px;
  right:80px;
  text-align:center;
  cursor:pointer;
  opacity:0.85;
  transition:0.25s;
}
.start-explore:hover{
  opacity:1;
  transform:translateY(-3px);
}
.explore-arrow{
  font-size:28px;
  animation:float 2s infinite;
}
.explore-text{
  font-size:14px;
  margin-top:4px;
}
@keyframes float{
  0%{transform:translateY(0);}
  50%{transform:translateY(6px);}
  100%{transform:translateY(0);}
}
</style>