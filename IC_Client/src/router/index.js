// 引入路由配置文件
import {createRouter, createWebHistory} from 'vue-router';


// 定义路由配置对象 -- 数组
const routes = [
    {
        path: '',
        meta: {
            title: '首页',
            login: false,   //配合全局路由守卫（导航守卫）使用，表示访问这个页面不需要登录。
            identity: null,
        },
        component: () => import('../components/Home.vue')
    },
    {
        path: '/login',
        meta: {
            title: '账号的登录与注册',
            login: false,
            identity: null,
        },
        component: () => import('../components/Login.vue')
    },
    {
        path: '/signup',
        meta: {
            title: '注册',
            login: false,
            identity: null,
        },
        component: () => import('../components/SignUp.vue')
    },
    {
        path: '/teacher',
        meta: {
            title: '教师上传课件页面',
            login: true,
            identity: 'teacher',
        },
        component: () => import('../components/Teacher.vue')
    },
    {
        path: '/student',
        meta: {
            title: '学生学习页面',
            login: true,
            identity: 'student',
        },
        component: () => import('../components/Student.vue')
    },
]

// 设置路由模式为 history 模式 -- 默认 hash 模式，访问路径中间有一个 # 号
const router = createRouter({
    history: createWebHistory(),
    routes
})

// 导出路由实例
export default router