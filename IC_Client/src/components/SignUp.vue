<template>
  <div class="signup-page">
    <!-- 背景装饰 -->
    <div class="bg-shapes">
      <span class="shape shape-1"></span>
      <span class="shape shape-2"></span>
      <span class="shape shape-3"></span>
    </div>

    <div class="signup-card">
      <!-- 标题区 -->
      <div class="card-head">
        <div class="identity-tag" :class="identity === 'teacher' ? 'tag-teacher' : 'tag-student'">
          {{ identity === 'teacher' ? '🎓 教师端注册' : '📚 学生端注册' }}
        </div>
        <h1 class="card-title">创建账号</h1>
        <p class="card-sub">AI互动智课生成与实时问答系统</p>
      </div>

      <!-- 表单区 -->
      <form class="form-area" @submit.prevent>
        <div class="form-item">
          <label class="form-label">{{ isShow ? '工号' : '学号' }}</label>
          <input type="text" v-model="id" class="form-input"
                 :placeholder="'请输入' + (isShow ? '工号' : '学号')">
        </div>
        <div class="form-item">
          <label class="form-label">姓名</label>
          <input type="text" v-model="name" class="form-input" placeholder="请输入真实姓名">
        </div>
        <div class="form-item">
          <label class="form-label">邮箱号</label>
          <input type="text" v-model="email" class="form-input" placeholder="请输入常用邮箱（用于接收验证码）">
        </div>
        <div class="form-row">
          <div class="form-item form-row-half">
            <label class="form-label">密码</label>
            <input type="password" v-model="password" class="form-input" placeholder="请设置密码">
          </div>
          <div class="form-item form-row-half">
            <label class="form-label">确认密码</label>
            <input type="password" v-model="confirmPassword" class="form-input" placeholder="请再次输入密码">
          </div>
        </div>
        <div class="form-item">
          <label class="form-label">验证码</label>
          <input type="text" v-model="captcha" class="form-input" placeholder="请输入邮箱收到的验证码">
        </div>
      </form>

      <!-- 操作按钮（发送验证码 / 注册 二选一显示） -->
      <button v-show="iscaptcha" @click="sendCaptcha" class="btn-primary" type="button">发送验证码</button>
      <button v-show="!iscaptcha" @click="signUp" class="btn-primary" type="button">注 册</button>

      <!-- 底部链接 -->
      <div class="card-footer">
        <span class="footer-link" @click="goLogin">已有账号？返回登录</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import {ref, getCurrentInstance, onMounted} from "vue";
import {useRouter} from "vue-router";
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
function goLogin(){
  router.push('/login');
}

// 创建当前实例对象
let proxy = getCurrentInstance().proxy;

let id = ref('')
let name = ref('')
let email = ref('')
let password = ref('')
let confirmPassword = ref('')

let captcha = ref("")
let iscaptcha = ref(true)



// 发送验证码 -- 向服务器发送请求，验证用户信息
function sendCaptcha(){
  console.log("【测试】开始验证账号信息......")

  let accountInformation = {
    identity: identity.value,
    id: id.value,
    name: name.value,
    email: email.value,
    password: password.value
  }

  // 验证两次密码是否一致
  if(password.value !== confirmPassword.value){
    ElMessage.error('两次密码不一致');
    return {
      "code": 500,
      "msg": "两次密码不一致"
    }
  }

  // 接收验证码
  proxy.$axios({
    url:'account/email',
    method:'post',
    data:accountInformation
  }).then(res=>{
    console.log("【测试】邮件的发送结果：", res.data)
    let code = res.data.code
    let message = res.data.msg
    if(code === 200){
      iscaptcha.value = !iscaptcha.value
      ElMessage.success(message)
    } else {
      ElMessage.error(message)
    }
  })
}

// 注册账号
function signUp(){
  console.log("【测试】开始注册账号......")

  let accountInformation = {
    identity: identity.value,
    id: id.value,
    name: name.value,
    email: email.value,
    password: password.value,
    captcha: captcha.value
  }

  proxy.$axios({
    url: 'account/signup',
    method: 'post',
    data: accountInformation
  }).then(res => {
    console.log(res.data);
    let code = res.data.code;
    if(code === 200){
      ElMessage.success('注册成功');
      router.push('/login');
    }else{
      ElMessage.error('注册失败');
    }
  })
}

</script>

<style scoped>
/* ===== 页面容器：与登录页统一的柔和渐变 ===== */
.signup-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 36px 16px;
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
  width: 460px;
  height: 460px;
  background: radial-gradient(circle, rgba(91,124,250,0.18) 0%, transparent 70%);
  top: -140px;
  right: -120px;
}
.shape-2 {
  width: 360px;
  height: 360px;
  background: radial-gradient(circle, rgba(123,92,250,0.14) 0%, transparent 70%);
  bottom: -120px;
  left: -90px;
}
.shape-3 {
  width: 200px;
  height: 200px;
  background: radial-gradient(circle, rgba(91,124,250,0.10) 0%, transparent 70%);
  top: 50%;
  right: 18%;
}

/* ===== 注册卡片 ===== */
.signup-card {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 440px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,0.6);
  border-radius: 22px;
  box-shadow: 0 18px 50px rgba(30, 40, 90, 0.12);
  padding: 34px 36px 26px;
}

/* ===== 标题区 ===== */
.card-head {
  text-align: center;
  margin-bottom: 24px;
}
.identity-tag {
  display: inline-block;
  padding: 5px 16px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 14px;
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
  font-size: 24px;
  font-weight: 800;
  color: #2c3350;
}
.card-sub {
  margin: 8px 0 0;
  color: #8a94b3;
  font-size: 13px;
  letter-spacing: 1px;
}

/* ===== 表单区 ===== */
.form-area {
  display: flex;
  flex-direction: column;
  gap: 15px;
}
.form-item {
  display: flex;
  flex-direction: column;
  gap: 7px;
}
.form-row {
  display: flex;
  gap: 14px;
}
.form-row-half {
  flex: 1;
}
.form-label {
  font-size: 14px;
  color: #4a5070;
  font-weight: 600;
}
.form-input {
  width: 100%;
  padding: 11px 14px;
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

/* ===== 主按钮（发送验证码 / 注册 二选一显示） ===== */
.btn-primary {
  width: 100%;
  margin-top: 22px;
  padding: 12px 0;
  border: none;
  border-radius: 12px;
  font-size: 15px;
  font-weight: 700;
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
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px dashed #e3e8f5;
  display: flex;
  justify-content: center;
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

/* ===== 小屏适配：密码一行放不下时堆叠 ===== */
@media (max-width: 480px) {
  .signup-card {
    padding: 28px 22px 22px;
  }
  .form-row {
    flex-direction: column;
    gap: 15px;
  }
}
</style>
