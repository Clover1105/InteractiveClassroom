<template>
  <div class="login-page">
    <!-- 背景装饰 -->
    <div class="bg-shapes">
      <span class="shape shape-1"></span>
      <span class="shape shape-2"></span>
      <span class="shape shape-3"></span>
    </div>

    <div class="login-card">
      <!-- 标题区 -->
      <div class="card-head">
        <div class="identity-tag" :class="identity === 'teacher' ? 'tag-teacher' : 'tag-student'">
          {{ identity === 'teacher' ? '🎓 教师端登录' : '📚 学生端登录' }}
        </div>
        <h1 class="card-title">欢迎回来</h1>
        <p class="card-sub">AI互动智课生成与实时问答系统</p>
      </div>

      <!-- 表单区 -->
      <form class="form-area" @submit.prevent="goChat">
        <div class="form-item">
          <label class="form-label">{{ isShow ? '工号' : '学号' }}</label>
          <input type="text" v-model="id" class="form-input"
                 :placeholder="'请输入' + (isShow ? '工号' : '学号')">
        </div>

        <div class="form-item">
          <label class="form-label">密码</label>
          <input type="password" v-model="password" class="form-input" placeholder="请输入密码">
        </div>

        <!-- 主按钮：type=submit，在输入框按回车也能登录 -->
        <button class="btn-primary" type="submit">登 录</button>
      </form>



      <!-- 底部链接 -->
      <div class="card-footer">
        <span class="footer-link" @click="goSignUp">没有账号？去注册</span>
        <span class="footer-divider">|</span>
        <span class="footer-link footer-plain" @click="goHome">返回首页</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import {ref, getCurrentInstance, onMounted} from "vue";
import {useRouter} from "vue-router"
import {ElMessage} from "element-plus";

// 加载页面后自动执行功能
let identity = ref("")
let isShow = ref('')
onMounted(() => {
  identity.value = sessionStorage.getItem("identity");
  if (identity.value === 'teacher'){
    isShow.value = true;
  } else {
    isShow.value = false;
  }
})

// 创建路由跳转对象
let router = useRouter();
function goSignUp(){
  router.push('/signup');
}
function goHome(){
  router.push('/');
}

// 创建当前实例对象 -- 通过这个对象才可以访问到 main.js 中定义的 $axios 变量
let proxy = getCurrentInstance().proxy

// 基本信息
let id = ref('')
let name = ref('')
let email = ref('')
let password = ref('')

// 登录
function goChat(){
  console.log("【测试】开始登录账号......")

  let accountInformation = {
    identity: identity.value,
    id: id.value,
    name: name.value,
    email: email.value,
    password: password.value
  }

  proxy.$axios({
    url:'account/login',
    method:'post',
    data:accountInformation
  }).then(res => {
    console.log("【测试】验证的返回结果：", res.data)
    let code = res.data.code
    let message = res.data.message
    let data = res.data.data
    if(code === 200){
      sessionStorage.setItem("name", data);
      // 存储JWT令牌：此后请求由 main.js 的axios拦截器自动携带
      sessionStorage.setItem("token", res.data.token);
      ElMessage.success(message)
      if(identity.value === "student"){
        setTimeout(() =>{
          router.push('/student')
        },2000)
      } else {
        setTimeout(() =>{
          router.push('/teacher')
        },2000)
      }

    } else {
      ElMessage.error(message)
    }
  })
}

</script>

<style scoped>
/* ===== 页面容器：与首页统一的柔和渐变 ===== */
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 16px;
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
  width: 480px;
  height: 480px;
  background: radial-gradient(circle, rgba(91,124,250,0.18) 0%, transparent 70%);
  top: -150px;
  left: -120px;
}
.shape-2 {
  width: 380px;
  height: 380px;
  background: radial-gradient(circle, rgba(123,92,250,0.14) 0%, transparent 70%);
  bottom: -130px;
  right: -90px;
}
.shape-3 {
  width: 220px;
  height: 220px;
  background: radial-gradient(circle, rgba(91,124,250,0.10) 0%, transparent 70%);
  top: 55%;
  left: 15%;
}

/* ===== 登录卡片 ===== */
.login-card {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 400px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,0.6);
  border-radius: 22px;
  box-shadow: 0 18px 50px rgba(30, 40, 90, 0.12);
  padding: 38px 36px 28px;
}

/* ===== 标题区 ===== */
.card-head {
  text-align: center;
  margin-bottom: 28px;
}
.identity-tag {
  display: inline-block;
  padding: 5px 16px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 16px;
}
.tag-teacher {
  background: linear-gradient(135deg, #f59e6b, #f0763c);
  box-shadow: 0 4px 12px rgba(240, 118, 60, 0.3);
}
.tag-student {
  background: linear-gradient(135deg, #5b7cfa, #7b5cfa);
  box-shadow: 0 4px 12px rgba(91, 124, 250, 0.3);
}
.card-title {
  margin: 0;
  font-size: 26px;
  font-weight: 800;
  color: #2c3350;
}
.card-sub {
  margin: 10px 0 0;
  color: #8a94b3;
  font-size: 13px;
  letter-spacing: 1px;
}

/* ===== 表单区 ===== */
.form-area {
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.form-label {
  font-size: 14px;
  color: #4a5070;
  font-weight: 600;
}
.form-input {
  width: 100%;
  padding: 12px 14px;
  font-size: 14px;
  color: #2c3350;
  border: 1.5px solid #dde3f3;
  border-radius: 12px;
  background: #f8faff;
  outline: none;
  box-sizing: border-box;
  transition: all 0.2s ease;
  font-family: inherit;
}
.form-input::placeholder {
  color: #b3bcd6;
}
.form-input:hover {
  border-color: #b9c6f2;
}
.form-input:focus {
  border-color: #5b7cfa;
  background: #ffffff;
  box-shadow: 0 0 0 4px rgba(91, 124, 250, 0.12);
}

/* ===== 主按钮 ===== */
.btn-primary {
  width: 100%;
  margin-top: 26px;
  padding: 13px 0;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 8px;
  text-indent: 8px;
  color: #fff;
  font-family: inherit;
  cursor: pointer;
  background: linear-gradient(135deg, #5b7cfa, #7b5cfa);
  box-shadow: 0 8px 18px rgba(91, 124, 250, 0.35);
  transition: all 0.2s ease;
}
.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 24px rgba(91, 124, 250, 0.45);
}
.btn-primary:active {
  transform: translateY(0);
}

/* ===== 底部链接 ===== */
.card-footer {
  margin-top: 22px;
  padding-top: 18px;
  border-top: 1px dashed #e3e8f5;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 14px;
}
.footer-link {
  font-size: 13px;
  color: #5b7cfa;
  cursor: pointer;
  transition: opacity 0.2s ease;
}
.footer-link:hover {
  opacity: 0.75;
  text-decoration: underline;
}
.footer-plain {
  color: #8a94b3;
}
.footer-divider {
  color: #d5dcea;
  font-size: 12px;
}
</style>
