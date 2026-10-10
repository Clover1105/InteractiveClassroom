<template>
  <div class="home-page">
    <!-- 背景装饰 -->
    <div class="bg-shapes">
      <span class="shape shape-1"></span>
      <span class="shape shape-2"></span>
      <span class="shape shape-3"></span>
      <span class="shape shape-4"></span>
    </div>

    <div class="home-wrapper">
      <!-- 左侧：品牌与特性 -->
      <div class="brand-side">
        <div class="brand-label">AI Interactive Classroom</div>
        <h1 class="brand-title">
          AI互动智课
          <span>生成与实时问答系统</span>
        </h1>
        <p class="brand-desc">
          基于大模型与知识图谱，为师生提供智能课件解析、授课脚本生成、实时互动问答与学情测试评价的一站式教学辅助平台。
        </p>

        <div class="feature-list">
          <div class="feature-item">
            <span class="feature-icon">✦</span>
            <span>智能课件解析与四源检索</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon">✦</span>
            <span>流式实时对话与四层记忆</span>
          </div>
          <div class="feature-item">
            <span class="feature-icon">✦</span>
            <span>章节测试与个性化点评报告</span>
          </div>
        </div>
      </div>

      <!-- 右侧：角色选择卡片 -->
      <div class="role-side">
        <div class="role-card">
          <h3 class="role-card-title">请选择角色进入系统</h3>
          <div class="role-list">
            <div class="role-item role-teacher" @click="goTeacherLogin">
              <div class="role-icon-box">
                <span class="role-emoji">🎓</span>
              </div>
              <div class="role-info">
                <div class="role-name">教师端</div>
                <div class="role-desc">上传课件 · 生成脚本 · 管理课程</div>
              </div>
              <div class="role-arrow">→</div>
            </div>

            <div class="role-item role-student" @click="goStudentLogin">
              <div class="role-icon-box">
                <span class="role-emoji">📚</span>
              </div>
              <div class="role-info">
                <div class="role-name">学生端</div>
                <div class="role-desc">课程问答 · 在线测试 · 查看点评</div>
              </div>
              <div class="role-arrow">→</div>
            </div>
          </div>
          <div class="role-card-footer">选择角色后将进入对应登录页面</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import {useRouter} from "vue-router";

// 创建路由跳转对象
let router = useRouter();

function goTeacherLogin() {
  router.push('/login');
  sessionStorage.setItem("identity", "teacher");
}

function goStudentLogin() {
  router.push('/login');
  sessionStorage.setItem("identity", "student");
}
</script>

<style scoped>
/* ===== 页面容器：柔和蓝紫渐变 ===== */
.home-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 5%;
  box-sizing: border-box;
  background: linear-gradient(120deg, #f0f5ff 0%, #e8eeff 40%, #f4f1ff 100%);
  position: relative;
  overflow: hidden;
  font-family: "Segoe UI", "Microsoft YaHei", Arial, sans-serif;
}

/* ===== 背景装饰几何 ===== */
.bg-shapes {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}
.shape {
  position: absolute;
  border-radius: 50%;
  opacity: 0.55;
}
.shape-1 {
  width: 520px;
  height: 520px;
  background: radial-gradient(circle, rgba(91,124,250,0.18) 0%, transparent 70%);
  top: -160px;
  right: -100px;
}
.shape-2 {
  width: 360px;
  height: 360px;
  background: radial-gradient(circle, rgba(123,92,250,0.14) 0%, transparent 70%);
  bottom: -120px;
  left: -80px;
}
.shape-3 {
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, rgba(91,124,250,0.12) 0%, transparent 70%);
  top: 15%;
  left: 8%;
}
.shape-4 {
  width: 260px;
  height: 260px;
  background: radial-gradient(circle, rgba(123,92,250,0.10) 0%, transparent 70%);
  bottom: 18%;
  right: 12%;
}

/* ===== 主内容区：左右分栏 ===== */
.home-wrapper {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 1100px;
  display: flex;
  align-items: center;
  gap: 60px;
}

/* ===== 左侧品牌区 ===== */
.brand-side {
  flex: 1.1;
  color: #2c3350;
}
.brand-label {
  display: inline-block;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 2px;
  color: #5b7cfa;
  background: rgba(91,124,250,0.10);
  padding: 5px 12px;
  border-radius: 999px;
  margin-bottom: 20px;
}
.brand-title {
  margin: 0;
  font-size: 42px;
  font-weight: 800;
  line-height: 1.25;
  letter-spacing: 1px;
}
.brand-title span {
  display: block;
  margin-top: 6px;
  font-size: 30px;
  font-weight: 600;
  color: #5b7cfa;
}
.brand-desc {
  margin: 24px 0 0;
  font-size: 15px;
  line-height: 1.8;
  color: #6b7394;
  max-width: 520px;
}
.feature-list {
  margin-top: 34px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.feature-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 15px;
  color: #4a5070;
  font-weight: 500;
}
.feature-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: linear-gradient(135deg, #5b7cfa, #7b5cfa);
  color: #fff;
  font-size: 11px;
  flex-shrink: 0;
}

/* ===== 右侧角色卡 ===== */
.role-side {
  flex: 0.9;
  display: flex;
  justify-content: center;
}
.role-card {
  width: 100%;
  max-width: 420px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,0.6);
  border-radius: 22px;
  box-shadow: 0 18px 50px rgba(30, 40, 90, 0.12);
  padding: 34px 30px 26px;
}
.role-card-title {
  margin: 0 0 24px;
  text-align: center;
  font-size: 17px;
  font-weight: 700;
  color: #3b4272;
}
.role-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.role-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 18px 18px;
  border-radius: 16px;
  border: 1.5px solid #e8ecf9;
  background: #fbfcff;
  cursor: pointer;
  transition: all 0.25s ease;
}
.role-item:hover {
  transform: translateY(-3px);
  border-color: transparent;
  box-shadow: 0 12px 28px rgba(91, 124, 250, 0.16);
}
.role-teacher:hover {
  background: linear-gradient(135deg, #f2f6ff, #ffffff);
}
.role-student:hover {
  background: linear-gradient(135deg, #f5f2ff, #ffffff);
}
.role-icon-box {
  width: 52px;
  height: 52px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #5b7cfa, #7b5cfa);
  font-size: 24px;
  flex-shrink: 0;
}
.role-info {
  flex: 1;
}
.role-name {
  font-size: 17px;
  font-weight: 700;
  color: #2c3350;
  margin-bottom: 4px;
}
.role-desc {
  font-size: 13px;
  color: #8a94b3;
}
.role-arrow {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #5b7cfa;
  background: #eef2ff;
  font-size: 16px;
  transition: all 0.2s ease;
}
.role-item:hover .role-arrow {
  background: #5b7cfa;
  color: #fff;
}
.role-card-footer {
  margin-top: 20px;
  text-align: center;
  font-size: 12px;
  color: #a0aac8;
}

/* ===== 响应式 ===== */
@media (max-width: 860px) {
  .home-wrapper {
    flex-direction: column;
    gap: 36px;
  }
  .brand-side {
    text-align: center;
    align-items: center;
    display: flex;
    flex-direction: column;
  }
  .brand-desc {
    max-width: 100%;
  }
  .role-side {
    width: 100%;
  }
  .role-card {
    max-width: 460px;
  }
}
@media (max-width: 520px) {
  .home-page {
    padding: 24px 16px;
  }
  .brand-title {
    font-size: 32px;
  }
  .brand-title span {
    font-size: 22px;
  }
}
</style>
