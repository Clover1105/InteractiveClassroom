import { createApp } from 'vue'
import './style.css'
import App from './App.vue'

// 创建对象
const app = createApp(App)

// 注册路由
import router from './router'
app.use(router)

// axios 全局配置
import axios from 'axios'   // 导入 axios 包
axios.defaults.baseURL = 'http://localhost:8000/'   // 服务器请求路径公共部分
axios.defaults.headers.post['Content-Type'] = 'application/json'    // post 请求发送json数据给服务器
axios.defaults.headers.put['Content-Type'] = 'application/json'     // put 请求发送json数据给服务器
app.config.globalProperties.$axios = axios      // 将 axios 对象挂载到 vue 对象上，使用 $axios 替代原生的 axios


// axios 请求拦截器：登录后所有请求自动携带JWT令牌
axios.interceptors.request.use(config => {
    const token = sessionStorage.getItem('token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

// axios 响应拦截器：
//   401 = token无效/已过期/已登出，清除登录态并跳回登录页
//   403 = 角色无权访问该接口
import { ElMessage } from 'element-plus'
axios.interceptors.response.use(res => res, err => {
    if (err.response) {
        if (err.response.status === 401) {
            sessionStorage.clear()
            ElMessage.error('登录已过期或已退出，请重新登录')
            router.push('/login')
        } else if (err.response.status === 403) {
            ElMessage.error('当前身份无权访问该功能')
        }
    }
    return Promise.reject(err)
})


// 导航守卫
// 固定写法 -- 每次路由要跳转时都会触发这个回调函数
// to: 要去的目标页面
// from: 从哪个页面离开
// next(): 放行函数，必须调用它才能继续跳转
router.beforeEach((to, from, next) => {
    // 判断目标页面的 meta 里 login 字段是否为 true
    if (to.meta.login){
        // 需要登录的页面：去 sessionStorage 里查有没有存 token
        let token = sessionStorage.getItem('token')
        // 如果查到了 token，说明已登录，调用 next() 放行；
        // 如果没查到，说明未登录，调用 next('/') 强制把用户重定向到首页
        if (!token){
            console.log('未登录，跳转到主页面')
            next('/')
            return
        }
        // 需要登录的页面还校验身份匹配：学生token进不了教师页，反之亦然
        if (to.meta.identity && to.meta.identity !== sessionStorage.getItem('identity')) {
            console.log('身份不符，跳转到首页')
            next('/')
            return
        }
        console.log('已登录，放行')
        next()
    // 如果目标页面不需要登录，就直接放行
    } else {
        console.log('非登录保护页面，直接访问')
        next()
    }
})

// 美化页面全局配置 -- 全局注册 Element-Plus
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
app.use(ElementPlus)

// 挂载到页面
app.mount('#app')