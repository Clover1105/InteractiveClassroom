<template>
  <div class="student-page">
    <!-- 顶部 Header -->
    <div class="header">
      <div class="header-left">
        <div class="header-logo">📚</div>
        <div class="header-title">
          <span class="header-name">学生学习中心</span>
          <span class="header-sub">AI互动智课生成与实时问答系统</span>
        </div>
      </div>
      <div class="header-right">
        <span class="welcome">欢迎，{{ stu_name }}<em class="role-tag">学生</em></span>
        <button @click="logout" class="btn-logout">退出登录</button>
      </div>
    </div>

    <div class="main-container">
      <!-- ===== 左侧面板 ===== -->
      <div class="left-panel">

        <!-- 课程选择（最多显示2个，超出滚动） -->
        <div class="section-label">选择课程</div>
        <div class="panel course-panel">
          <table class="table">
            <thead>
              <tr>
                <th>课程名称</th>
                <th>课件数</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(course, index) in courseList" :key="course.course_name" v-show="index < 2 || courseExpanded">
                <td class="td-course">{{ course.course_name }}</td>
                <td class="td-count">{{ course.count }}</td>
                <td>
                  <button @click="selectCourse(course.course_name)" class="btn-small btn-blue"
                          :disabled="selectedCourse === course.course_name">
                    {{ selectedCourse === course.course_name ? '已选' : '选择' }}
                  </button>
                </td>
              </tr>
              <tr v-if="courseList.length === 0">
                <td colspan="3" class="empty-cell">暂无课程</td>
              </tr>
            </tbody>
          </table>
          <button v-if="courseList.length > 2" @click="courseExpanded = !courseExpanded" class="btn-expand">
            {{ courseExpanded ? '收起' : '查看更多(' + courseList.length + ')' }}
          </button>
        </div>

        <!-- 历史记录（列表流样式） -->
        <div class="section-label">历史会话</div>
        <div class="panel history-panel-list">
          <div class="panel-header">
            <button @click="newSession" class="btn-new-chat">＋ 开启新对话</button>
          </div>
          <div class="history-list">
            <div v-if="sessionList.length === 0" class="empty-history">暂无历史会话</div>
            <div v-for="session in sessionList" :key="session.session_id"
                 class="history-item"
                 :class="{ 'history-item-active': currentSessionId == session.session_id }"
                 @click="loadSession(session.session_id)">
              <div class="history-item-title">{{ session.title }}</div>
              <div class="history-item-sub">
                <span class="sub-date">{{ session.time }}</span>
                <span class="sub-mode">
                  {{ session.modeText }}
                  <!-- .stop阻止事件冒泡，避免点删除时触发整个条目的loadSession -->
                  <button @click.stop="deleteSession(session.session_id)" class="btn-del" title="删除该会话"><el-icon color="red"><Delete /></el-icon></button>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ===== 右侧面板 ===== -->
      <div class="right-panel">
        <!-- 课件列表（紧凑） -->
        <div v-if="selectedCourse" class="panel courseware-panel">
          <h3 class="panel-title">课程：{{ selectedCourse }}</h3>
          <table class="table table-sm">
            <thead>
              <tr>
                <th>文件名</th>
                <th>章节</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in currentCoursewareList" :key="item.id">
                <td class="td-ellipsis">{{ item.original_filename }}</td>
                <td>{{ item.chapter_name }}</td>
                <td>
                  <span class="status-badge"
                        :class="item.parse_status === 1 ? 'status-done' : item.parse_status === 0 ? 'status-processing' : item.parse_status === 2 ? 'status-pending' : 'status-fail'">
                    {{ getStatusText(item.parse_status) }}
                  </span>
                </td>
                <td class="td-actions">
                  <button @click="viewCourseware(item)" :disabled="item.parse_status !== 1" class="btn-small">脚本</button>
                  <button @click="viewEvaluation(item)"
                          :disabled="evaluatingId === item.id" class="btn-small btn-blue">
                    {{ evaluatingId === item.id ? '...' : '评价' }}
                  </button>
                </td>
              </tr>
              <tr v-if="currentCoursewareList.length === 0">
                <td colspan="4" class="empty-cell">该课程暂无课件</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 大框：左脚本 + 右对话 + 底部输入 -->
        <div class="panel big-box" :class="{ 'has-courseware': selectedCourseware }">
          <!-- 脚本展示区（左） -->
          <div class="script-area" :class="{ 'hidden': !selectedCourseware || hideScript}">
            <h3 class="panel-title" v-if="selectedCourseware">授课脚本 - {{ selectedCourseware.chapter_name }}</h3>
            <div class="script-content">
              {{ scriptLoading ? '脚本加载中...' : (scriptContent || '请选择课件查看脚本') }}
            </div>
            <div class="script-actions">
<!--              <button @click="startQuestioning" :disabled="scriptLoading || !scriptContent">开始提问</button>-->
              <button @click="startTesting" :disabled="scriptLoading || !scriptContent || testing" class="btn-test">
                {{ testing ? '测试中...' : '开始测试' }}
              </button>
              <!-- 退出课程/课件按钮 -->
              <button @click="exitCourseMode" class="btn-small btn-danger">退出课件</button>
            </div>

          </div>

          <!-- 对话区（右） -->
          <div class="chat-area" :class="{ 'full': !selectedCourseware }">
            <h3 class="panel-title chat-title">
              智能对话
              <span class="mode-text">当前模式：{{ modeText }}</span>
              <!-- 退出测试按钮：仅测试模式显示 -->
              <button v-if="chatMode === 'test'" @click="exitTest" class="btn-small btn-danger btn-exit-test">
                退出测试
              </button>
            </h3>

            <!-- 等待课件提示（仅在选了课程但没选课件时显示） -->
            <div v-if="coursewareRequired" class="courseware-required-hint">
              <span class="hint-text">已选择课程，请选择上方具体课件以开始提问/测试，或退回普通对话模式。</span>
              <button @click="backToNormal" class="btn-small">退回普通对话</button>
            </div>

            <div class="chat-messages" ref="chatMessagesRef">
              <div v-for="(msg, index) in messages" :key="index" class="message" :class="msg.role === 'user' ? 'msg-row-user' : 'msg-row-ai'">
                <!-- 系统提示：居中小字样式，仅本地显示、不落库 -->
                <p v-if="msg.role === 'system'" class="msg-hint">{{ msg.content }}</p>
                <div v-else class="msg-bubble" :class="msg.role === 'user' ? 'bubble-user' : 'bubble-ai'">
                  {{ msg.content }}
                </div>
              </div>
              <div v-if="messages.length === 0" class="empty-chat">
                暂无消息，输入内容开始对话
              </div>
            </div>
            <div class="chat-input">
              <input v-model="inputText" type="text"
                     :placeholder="chatMode === 'test' ? '请输入本题答案...' : '输入你的问题...'"
                     :disabled="inputDisabled" @keyup.enter="sendMessage" />
              <button @click="sendMessage" :disabled="chatLoading" class="btn-send">
                {{ chatLoading ? '回答中...' : '发送' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 评价展示对话框 -->
    <el-dialog v-model="evaluationVisible" :title="evaluationTitle" width="70%" top="5vh">
      <div class="evaluation-view">
        {{ evaluationContent }}
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import {ref, computed, getCurrentInstance, onMounted, watch, nextTick} from "vue";
import {useRouter} from "vue-router";
import {ElMessage} from "element-plus";
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { Delete } from '@element-plus/icons-vue'

// 加载页面后自动执行功能 -- 获取课程列表、当前角色名、用户名
let identity = ref("")
let stu_name = ref("")
onMounted(() => {
  identity.value = sessionStorage.getItem("identity");
  stu_name.value = sessionStorage.getItem("name");
  fetchCourseList();
  fetchSessionList();
});

// 获取当前实例和路由跳转对象
let proxy = getCurrentInstance().proxy;
let router = useRouter();

// 退出登录 -- 调后端将token加入黑名单，清除本地登录态，回首页
function logout(){
  proxy.$axios({
    url: 'account/logout',
    method: 'post'
  }).finally(() => {
    sessionStorage.clear();
    router.push('/');
  });
}





// ==================== 课程与课件 ====================

// 基本变量
let courseList = ref([]);          // 课程列表（从课件数据按课程名分组）
let allCoursewareList = ref([]);   // 全部课件（courseware/list 的原始数据）
let selectedCourse = ref(null);   // 当前选中的课程名
let selectedCourseware = ref(null); // 当前选中的课件
let scriptContent = ref('');       // 当前课件的授课脚本
let scriptLoading = ref(false);    // 脚本加载状态
let courseExpanded = ref(false);   // 课程列表是否展开

// 当前课程下的课件列表变量
// computed 是 Vue 3 提供的响应式计算函数，返回值是一个计算属性对象
let currentCoursewareList = computed(() => {
  if (!selectedCourse.value) return [];
  // .filter() 遍历这个数组，筛选出 course_name 字段等于当前选中课程名的课件项
  return allCoursewareList.value.filter(item => item.course_name === selectedCourse.value);
});

// 获取课件列表并按课程分组
function fetchCourseList() {
  proxy.$axios({
    url: 'courseware/list',
    method: 'get'
  }).then(res => {
    console.log("【测试】获取课件列表返回结果：", res.data);
    if (res.data.code === 200) {
      // 将获取到的所有 课件 赋值给列表
      allCoursewareList.value = res.data.data;
      // 按课程名分组，统计每个课程的课件数
      let courseMap = {};
      // or...in 遍历的是索引/键，for...of 遍历的是值
      for (let cw of allCoursewareList.value) {
        if (!courseMap[cw.course_name]) {
          courseMap[cw.course_name] = 0;
        }
        courseMap[cw.course_name]++;
      }
      // 把映射表courseMap转为数组，赋值给 courseList
      // 遍历.key获得的纯字符串数组。它每拿到一个课程名（比如 "Python入门"），就去原来的 courseMap 里查一下这个课程对应的数量是多少，然后把它们打包成一个新的对象
      courseList.value = Object.keys(courseMap).map(name => ({
        course_name: name,
        count: courseMap[name]
      }));
    }
  }).catch(err => {
    console.log("【测试】获取课件列表失败：", err);
  });
}

function getStatusText(status) {
  if (status === 1) return '已完成';
  if (status === 0) return '处理中';
  if (status === 2) return '未处理';
  return '失败';
}

// 选择课程 -- 进入"等待选课件"的中间态，chatMode 保持 normal，输入框自动由 coursewareRequired 禁用
function selectCourse(courseName) {
  // 如果用户点击的课程就是当前已选中的那个，直接 return 退出函数，不做任何操作
  if (selectedCourse.value === courseName) return;

  // 退出提问/测试模式 -- 知识点和测试都绑定在具体课件上，切换课程即退出
  // 每轮对话后端已逐条落库 chat_history 表
  if (chatMode.value === 'qa' || chatMode.value === 'test') {
    testing.value = false;  // 控制是否处于测试进行中状态
    testIndex.value = 0;  // 当前测试进行到第几题
    testQuestions.value = []; // 存储本次测试的题目列表
    testAnswers.value = []; // 存储用户对每道题的回答
  }

  // 开启新会话（自动清空对话框并从后端刷新历史列表）
  newSession()

  // 只设置选中的课程；chatMode 保持 normal；
  // selectedCourseware 为 null → coursewareRequired=true → 输入框禁用 + 提示
  selectedCourse.value = courseName;
  selectedCourseware.value = null;
  scriptContent.value = '';
  console.log("【测试】已选择课程：", courseName);
}

// 点击课件：加载授课脚本（复用教师端已有接口）
function viewCourseware(item) {
  // 新对话框
  messages.value = [];
  currentSessionId.value = Date.now().toString();
  // 切换课件即开启新会话 -- 旧消息后端已逐轮落库，刷新历史列表即可拿到
  fetchSessionList();
  // 基础信息
  selectedCourseware.value = item;  // 选择的课件
  scriptLoading.value = true; // 开启脚本加载状态
  scriptContent.value = ''; // 初始化脚本内容
  console.log("【测试】查看课件脚本中...");
  proxy.$axios({
    url: 'courseware/script',
    method: 'get',
    params: {
      courseware_id: item.id,
      course_name: item.course_name,
      chapter_name: item.chapter_name
    },
    timeout: 180000  // 脚本不存在时后端会现场生成，放宽超时
  }).then(res => {
    if (res.data.code === 200) {
      scriptContent.value = res.data.data.content;
      chatMode.value = 'qa';
    } else {
      ElMessage.warning(res.data.message);
    }
  }).catch(err => {
    console.log("【测试】获取脚本失败：", err);
    ElMessage.error('获取脚本失败，请重试');
  }).finally(() => {
    scriptLoading.value = false;
  });
}




// ==================== 对话状态机 ====================
// chatMode 三种取值，对应三种情况：
//   normal : 普通对话（未选课件），不使用任何数据集
//   qa     : 知识点提问，检索 data_qa_chromadb + data_courseware_chromadb + neo4j
//   test   : 测试，由 student/test/* 接口处理
// 选了课程但没选课件时，chatMode 保持 normal，输入框由下面的 coursewareRequired 禁用，
// 此时不允许发消息，也不参与任何模式匹配，仅作为"等待用户选课件"的中间态。

let chatMode = ref('normal');

// 计算属性 modeText，用于根据当前聊天模式动态生成页面顶部的状态提示文字
let modeText = computed(() => {
  if (chatMode.value === 'test') {
    // testing=false 表示测试已结束（保持test模式直到退出/新对话）
    if (!testing.value) return '测试已结束';
    return `测试模式 (第 ${Math.min(testIndex.value + 1, testTotal)}/${testTotal} 题)`;
  }
  if (chatMode.value === 'qa') return '知识点提问';
  return '普通对话';
});

// 等待选课件状态：已选课程但未选课件（不区分普通聊天还是回看历史）
let coursewareRequired = computed(() => {
  return !!selectedCourse.value && !selectedCourseware.value;
});

// 输入禁用：测试已结束 或 回看测试历史
let inputDisabled = computed(() => {
  if (coursewareRequired.value) return true;
  if (chatMode.value === 'test' && !testing.value) return true;
  if (viewingTest.value) return true;
  return false;
});

// 初始化对话消息：[{role: 'user'|'assistant'|'system', content: '...'}]
let messages = ref([]);

// 自动滚动到对话底部
let chatMessagesRef = ref(null);
function scrollToBottom() {
  nextTick(() => {
    const el = chatMessagesRef.value;
    if (el) el.scrollTop = el.scrollHeight;
  });
}
watch(messages, scrollToBottom, { deep: true, flush: 'post' });

let inputText = ref('');  // 输入框内容
let chatLoading = ref(false);
let hideScript = ref(false);    // 测试进行中隐藏脚本（考察真实水平），结束/退出后恢复
let viewingTest = ref(false);   // 正在回看测试历史（禁止输入）









// ==================== 会话管理与历史记录 ====================
let currentSessionId = ref(0);      // 当前会话id
let sessionList = ref([]);             // 历史会话列表

// 开启新会话（清空当前对话，历史记录以数据库为准）
function newSession() {
  // 测试进行中点"开启新对话" = 退出测试：本次未完成、后端未存储，直接丢弃
  if (chatMode.value === 'test' && testing.value) {
    testing.value = false;
    testIndex.value = 0;
    testQuestions.value = [];
    testAnswers.value = [];
    hideScript.value = false;
  }

  // 清空所有上下文（无论是否处于 qa/test 或仅选了课程），关闭脚本展示，历史标记，课程选择并切换为普通对话
  selectedCourseware.value = null;
  scriptContent.value = '';
  selectedCourse.value = null;
  chatMode.value = 'normal';
  viewingTest.value = false;


  // Date.now() 返回当前时间戳
  currentSessionId.value = Date.now().toString();
  // 清空消息列表
  messages.value = [];
  // 测试进行中新会话会中断测试
  testing.value = false;  // 退出测试模式
  testIndex.value = 0;  // 当前测试题数重置为 0，下次进入测试时从第一题开始
  testQuestions.value = [];
  testAnswers.value = [];

  // 产生新对话后，及时从后端刷新历史记录列表
  fetchSessionList();
}

// 退回普通对话（保留当前会话）
// 退回普通对话：保留当前会话ID和消息，仅清空课程/课件上下文，输入框恢复可用
// 区别于 newSession -- 后者会开新会话、清空消息、重置 session_id
function backToNormal() {
  selectedCourseware.value = null;
  selectedCourse.value = null;
  scriptContent.value = '';
  chatMode.value = 'normal';
  viewingTest.value = false;
  // 不调用 fetchSessionList -- 不涉及历史记录刷新
}


// 查看历史会话：消息加载回对话框
function viewSession(session) {
  // 深拷贝 -- {...m} 是展开运算符，把对象 m 的所有属性"展开"到一个新对象里
  // 等价于：{ role: m.role, content: m.content, ... }
  // {...m} 会创建一个全新的对象，和原来的 m 不是同一个引用
  messages.value = session.messages.map(m => ({...m}));
  currentSessionId.value = session.session_id;

  // 恢复课程和课件上下文
  selectedCourseware.value = null;
  scriptContent.value = '';
  if (session.selectedCourse) {
    selectedCourse.value = session.selectedCourse;
    if (session.selectedChapter) {
      // 尝试在当前课件列表中查找对应的课件 -- matchedCw：匹配的课件
      let matchedCw = currentCoursewareList.value.find(
        item => item.chapter_name === session.selectedChapter
      );
      if (matchedCw) {
        selectedCourseware.value = matchedCw;
      }
    }
  } else {
    // 普通对话的历史记录：清空课程，隐藏课件列表
    selectedCourse.value = null;
  }

  // 测试会话只回看，显示脚本，禁止输入
  viewingTest.value = session.mode === 'test';
  hideScript.value = false;

  // 如果是知识点提问模式或测试模式的记录，加载脚本
  if (session.mode === 'qa' || session.mode === 'test') {
    // 如果已匹配到课件，加载脚本内容
    if (selectedCourseware.value) {
      scriptLoading.value = true;
      proxy.$axios({
        url: 'courseware/script',
        method: 'get',
        params: {
          courseware_id: selectedCourseware.value.id,
          course_name: selectedCourseware.value.course_name,
          chapter_name: selectedCourseware.value.chapter_name
        },
        timeout: 180000
      }).then(res => {
        if (res.data.code === 200) {
          scriptContent.value = res.data.data.content;
        }
      }).catch(err => {
        console.log("【测试】获取脚本失败：", err);
      }).finally(() => {
        scriptLoading.value = false;
      });
    }
    chatMode.value = session.mode;
  } else {
      // 非知识点提问模式：关闭脚本展示
      selectedCourseware.value = null;
      scriptContent.value = '';
      chatMode.value = session.mode;
      selectedCourse.value = null;
  }

  // 清除测试状态
  testing.value = false;
  testIndex.value = 0;
  testQuestions.value = [];
  testAnswers.value = [];

  console.log("【测试】查看历史会话：", session.session_id, "模式：", session.mode);
}

// 删除历史会话（调用后端，删除chat_history和摘要）
function deleteSession(sessionId) {
  if (!confirm('确定要删除这条历史记录吗？删除后不可恢复！')) {
    return;
  }
  proxy.$axios({
    url: 'student/session',
    method: 'delete',
    params: { session_id: sessionId }
  }).then(res => {
    if (res.data.code === 200) {
      ElMessage.success('历史记录已删除');
      // 从列表移除
      sessionList.value = sessionList.value.filter(s => s.session_id !== sessionId);
      // 若删除的是当前打开的会话，清空聊天区
      if (sessionId === currentSessionId.value.toString()) {
        messages.value = [];
        currentSessionId.value = 0;
      }
    } else {
      ElMessage.error(res.data.message || '删除失败');
    }
  }).catch(err => {
    console.log("【测试】删除会话失败：", err);
    ElMessage.error('删除失败，请重试');
  });
}


// 获取历史会话列表（从后端数据库拉取）
function fetchSessionList() {
  const userId = stu_name.value || 'default_user';
  proxy.$axios({
    url: 'student/session/list',
    method: 'get',
    params: { user_id: userId }
  }).then(res => {
    if (res.data.code === 200) {
      sessionList.value = res.data.data;
      console.log("【测试】获取到会话列表：", sessionList.value);
    } else {
      console.log("【测试】获取会话列表失败：", res.data.message);
    }
  }).catch(err => {
    console.log("【测试】获取会话列表异常：", err);
  });
}

// 加载历史会话详情（先列表，再按ID拉消息明细）
function loadSession(sessionId) {
  proxy.$axios({
    url: 'student/session/detail',
    method: 'get',
    params: { session_id: sessionId }
  }).then(res => {
    if (res.data.code === 200) {
      const detail = res.data.data;
      // 找到会话的元信息（模式、课程等）
      const sessionInfo = sessionList.value.find(s => s.session_id == sessionId);
      console.log("【测试】获取到会话详情：", detail);
      console.log("【测试】获取到会话元信息：", sessionInfo);
      viewSession({
        session_id: detail.session_id,
        messages: detail.messages,
        mode: sessionInfo ? sessionInfo.mode : 'normal',
        selectedCourse: sessionInfo ? sessionInfo.selectedCourse : null,
        selectedChapter: sessionInfo ? sessionInfo.selectedChapter : null
      });
    } else {
      console.log("【测试】获取会话详情失败：", res.data.message);
    }
  }).catch(err => {
    console.log("【测试】获取会话详情异常：", err);
  });
}





// ==================== 退出课程/课件模式 ====================
function exitCourseMode() {
  // 退出课件 = 开启新会话（自动清空课程/课件上下文、刷新历史列表、回到普通对话）
  newSession();

  console.log("【测试】已退出课程模式，回到普通对话。");
}






// ==================== 发送消息（对话核心） ====================
function sendMessage() {
  let text = inputText.value.trim();
  if (!text) return;
  inputText.value = '';

  // 情况四：测试模式下，输入即为本题答案
  if (chatMode.value === 'test') {
    // 调用测试答案处理函数，把用户输入当作本题答案提交 （会判断对错、更新答题进度等）
    handleTestAnswer(text);
    return;
  }

  // 如果当前没有会话ID，强制生成一个时间戳作为会话ID，防止后端 422
  if (!currentSessionId.value || currentSessionId.value === 0) {
    currentSessionId.value = Date.now().toString();
  }

  // 后端 POST student/chat -- 按 session_id 维护四层记忆，多轮
  //   mode=normal : 普通对话，不使用任何数据集
  //   mode=qa     : 知识点提问，检索 data_qa_chromadb + data_courseware_chromadb + neo4j
  // （mode=test 由 /student/test/* 单独处理，不走此接口）

  // 渲染用户输入消息
  messages.value.push({role: 'user', content: text});
  // 渲染初始占位消息(模拟思考中，后续会被流式文字覆盖)
  messages.value.push({role: 'assistant', content: '思考中，请耐心等待...'});

  // 设为 true 表示"AI正在思考"
  chatLoading.value = true;

  // 构造请求体
  const bodyParams = {
    session_id: currentSessionId.value.toString(),
    mode: chatMode.value,
    course_name: selectedCourse.value || '',
    chapter_name: selectedCourseware.value ? selectedCourseware.value.chapter_name : '',
    courseware_id: selectedCourseware.value ? selectedCourseware.value.id : 0,
    question: text,
    user_id: stu_name.value
  };

  console.log("【前端请求参数】", JSON.stringify(bodyParams));

  let ans = ''; // 用来拼接完整的后端回复

  // 建立 SSE 连接
  fetchEventSource('http://localhost:8000/student/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      // SSE不走axios拦截器，JWT令牌需手动携带
      'Authorization': 'Bearer ' + sessionStorage.getItem('token')
    },
    body: JSON.stringify(bodyParams),
    onmessage(event) {
      let data = event.data;
      if (data === 'end_end') {
        chatLoading.value = false;
        fetchSessionList();
        return;
      }
      // 解析JSON，提取实际的文本内容
      try {
        let parsed = JSON.parse(data);
        ans += parsed.content;
      } catch (e) {
        // 如果不是 JSON (比如意外收到的其他数据)，原样拼接
        ans += data;
      }
      messages.value[messages.value.length - 1].content = ans;
    },
    onerror(err) {
      console.log("【测试】SSE获取数据失败", err);
      chatLoading.value = false;
      messages.value[messages.value.length - 1].content = '网络异常，无法获取流式回复。';
      fetchSessionList();
      throw err; // 必须抛出错误，否则库会无限重试
    }
  }).catch(err => {
    // 捕获 onerror 抛出的异常，防止未处理的 Promise rejection
    console.log("【测试】SSE连接异常:", err);
  });
}








// ==================== 情况四：开始测试 ====================
let testing = ref(false);      // 测试是否进行中
let testIndex = ref(0);        // 当前题目下标（0~9）
let testTotal = 10;             // 题目总数
let testQuestions = ref([]);  // 题目列表
let testAnswers = ref([]);     // 学生答案列表

function startTesting() {
  if (!selectedCourseware.value) {
    ElMessage.warning('请先选择要测试的具体章节/课件');
    return;
  }

  // 进入测试即开启新会话（不用newSession -- 它会清课件，而测试依赖课件）
  messages.value = [];
  currentSessionId.value = Date.now().toString();
  viewingTest.value = false;
  // 旧消息后端已逐轮落库，刷新历史列表即可
  fetchSessionList();

  // 测试进行中隐藏脚本，考察真实水平
  hideScript.value = true;

  chatMode.value = 'test';
  testing.value = true;
  testIndex.value = 0;
  testAnswers.value = [];

  messages.value.push({ role: 'assistant', content: '正在出题，请耐心等待...' });
  chatLoading.value = true; // 展示AI正在思考

  // 基于该课程的数据集生成10道练习题，返回 {questions: ['...', ...]}
  proxy.$axios({
    url: 'student/test/start',
    method: 'post',
    data: {
      session_id: currentSessionId.value.toString(),
      courseware_id: selectedCourseware.value.id,
      course_name: selectedCourse.value,
      chapter_name: selectedCourseware.value.chapter_name,
      user_id: stu_name.value
    },
    timeout: 180000
  }).then(res => {
    if (res.data.code === 200) {
      testQuestions.value = res.data.data.questions;
      pushCurrentQuestion();
    } else {
      testing.value = false;
      hideScript.value = false;
      chatMode.value = 'qa';
      messages.value.push({role: 'system', content: res.data.message});
    }
  }).catch(err => {
    console.log("【测试】测试接口启动失败：", err);
    ElMessage.error('测试启动失败，请稍后重试');
    testing.value = false;
    hideScript.value = false;
    chatMode.value = 'qa';
  }).finally(() => {
    chatLoading.value = false;
  });
}

// 把当前题目推进对话框
function pushCurrentQuestion() {
  const content = `【练习题 ${testIndex.value + 1}/${testTotal}】${testQuestions.value[testIndex.value]}`;
  if (testIndex.value === 0 && messages.value.length > 0){
    messages.value[messages.value.length - 1].content = content;
  } else {
    messages.value.push({ role: 'assistant', content: content });
  }
}

// 退出测试：未完成则不存储（后端在收卷前不落库，直接退出即无痕）
function exitTest() {
  if (testing.value) {
    if (!confirm('测试尚未完成，退出后本次作答不会保存，确定退出吗？')) return;
  }
  currentSessionId.value = Date.now().toString();
  testing.value = false;
  hideScript.value = false;
  viewingTest.value = false;
  chatMode.value = 'qa';
  testIndex.value = 0;
  testQuestions.value = [];
  testAnswers.value = [];
  messages.value = [];   // 未存储的测试内容直接清空
  fetchSessionList();
}

// 处理测试答案：记录后进入下一题或收卷
function handleTestAnswer(answer) {
  testAnswers.value.push(answer);
  // 显示学生自己的回答
  messages.value.push({role: 'user', content: answer});
  // 系统提示（仅本地显示，不落库）
  messages.value.push({role: 'system', content: '已记录你的回答...'});

  if (testIndex.value < testTotal - 1) {
    testIndex.value++;
    pushCurrentQuestion();
  } else {
    finishTest();
  }
}

// 测试收卷：通知后端生成点评报告
function finishTest() {
  // 测试结束：testing=false → 输入框关闭、模式显示"测试已结束"
  // chatMode保持'test'直到用户点"退出测试"或"开启新对话"
  testing.value = false;
  messages.value.push({ role: 'system', content: '正在生成评价报告，请耐心等待...' });
  chatLoading.value = true;

  // 后端待实现接口契约：POST student/test/finish
  //   汇总5题作答，生成 .md 点评报告存储到 static/evaluation
  proxy.$axios({
    url: 'student/test/finish',
    method: 'post',
    data: {
      session_id: currentSessionId.value.toString(),
      courseware_id: selectedCourseware.value.id,
      course_name: selectedCourse.value,
      chapter_name: selectedCourseware.value.chapter_name,
      questions: testQuestions.value,
      answers: testAnswers.value,
      user_id: stu_name.value
    },
    timeout: 180000
  }).then(res => {
    let msg = res.data.code === 200
      ? '测试完成，点评报告已生成，可点击课件旁的"查看评价"按钮查看。'
      : res.data.message;
    const last = messages.value[messages.value.length - 1];
    if (last && last.role === 'system' && last.content === '正在生成评价报告，请耐心等待...') {
      last.content = msg;
    } else {
      messages.value.push({ role: 'system', content: msg });
    }
    // 恢复脚本显示；刷新历史记录（此时后端才落库测试问答）
    hideScript.value = false;
    fetchSessionList();
  }).catch(err => {
    console.log("【测试】收卷接口失败：", err);
    ElMessage.error('收卷失败，请稍后重试');
    chatLoading.value = false;
  }).finally(() => {
    chatLoading.value = false;
  });
}











// ==================== 查看评价 ====================
let evaluationVisible = ref(false); // 评价是否可见
let evaluationContent = ref('');  // 评价内容
let evaluationTitle = ref('测试点评');
let evaluatingId = ref(null);

// item -- 当前课程信息
function viewEvaluation(item) {
  evaluatingId.value = item.id;
  console.log("【测试】查看评价中...");
  // 后端待实现接口契约：GET student/evaluation/latest
  //   返回该课件最新一次测试生成的点评.md内容
  proxy.$axios({
    url: 'student/evaluation/latest',
    method: 'get',
    params: { courseware_id: item.id },
    timeout: 30000
  }).then(res => {
    if (res.data.code === 200) {
      evaluationTitle.value = `测试点评 - ${item.course_name} / ${item.chapter_name}`;
      evaluationContent.value = res.data.data.content;
      evaluationVisible.value = true;
    } else {
      ElMessage.warning(res.data.message);
    }
  }).catch(err => {
    console.log("【测试】获取评价失败：", err);
    ElMessage.error('暂无评价，请先完成测试');
  }).finally(() => {
    evaluatingId.value = null;
  });
}

</script>

<style scoped>
/* ===== 页面容器：不滚动 ===== */
.student-page {
  font-family: "Segoe UI", "Microsoft YaHei", Arial, sans-serif;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: linear-gradient(120deg, #f0f5ff 0%, #e8eeff 50%, #f4f1ff 100%);
}

/* 顶部 Header */
.header {
  background: #ffffff;
  padding: 12px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
  box-shadow: 0 2px 12px rgba(30, 40, 90, 0.06);
  position: relative;
  z-index: 10;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.header-logo {
  width: 38px;
  height: 38px;
  border-radius: 11px;
  background: linear-gradient(135deg, #5b7cfa, #7b5cfa);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 19px;
  box-shadow: 0 4px 12px rgba(91, 124, 250, 0.3);
}
.header-title {
  display: flex;
  flex-direction: column;
}
.header-name {
  font-size: 16px;
  font-weight: 800;
  color: #2c3350;
}
.header-sub {
  font-size: 11px;
  color: #9aa3c0;
  letter-spacing: 1px;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 14px;
}
.welcome {
  font-size: 14px;
  color: #4a5070;
  font-weight: 600;
}
.role-tag {
  display: inline-block;
  font-style: normal;
  font-size: 11px;
  color: #5b7cfa;
  background: rgba(91, 124, 250, 0.12);
  padding: 1px 8px;
  border-radius: 999px;
  margin-left: 8px;
  font-weight: 600;
}
.btn-logout {
  padding: 7px 16px;
  font-size: 13px;
  border-radius: 8px;
  border: 1.5px solid #e2e8f7;
  background: #ffffff;
  color: #5b6790;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s ease;
}
.btn-logout:hover {
  color: #f56c6c;
  border-color: #f56c6c;
}

/* 主容器：左右两栏，占满剩余高度 */
.main-container {
  display: flex;
  flex: 1;
  padding: 16px 20px 20px;
  gap: 16px;
  overflow: hidden;
}

/* ===== 左侧面板 ===== */
.left-panel {
  width: 275px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow: hidden;
}

/* 分区小标题 */
.section-label {
  font-size: 12px;
  font-weight: 700;
  color: #8a94b3;
  letter-spacing: 2px;
  padding-left: 4px;
  flex-shrink: 0;
}

/* 通用面板 */
.panel {
  border: none;
  border-radius: 14px;
  padding: 12px 14px;
  background: #ffffff;
  box-shadow: 0 6px 22px rgba(30, 40, 90, 0.06);
}
.panel-title {
  margin: 0 0 8px 0;
  font-size: 13px;
  font-weight: 700;
  color: #2c3350;
  border-bottom: 1px solid #eef1f9;
  padding-bottom: 7px;
  display: flex;
  align-items: center;
}

/* 课程选择面板（固定高度，最多显示2行数据） */
.course-panel {
  height: 118px;
  overflow-y: auto;
  flex-shrink: 0;
}
.btn-expand {
  margin-top: 8px;
  width: 100%;
  padding: 5px 0;
  font-size: 12px;
  border: none;
  border-radius: 8px;
  background: #f4f6ff;
  color: #5b7cfa;
  cursor: pointer;
  font-family: inherit;
  transition: background 0.2s ease;
}
.btn-expand:hover {
  background: #e9eeff;
}

/* ===== 历史记录面板（列表流样式） ===== */
.history-panel-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.history-panel-list .panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  flex-shrink: 0;
}
.btn-new-chat {
  width: 100%;
  padding: 9px 0;
  font-size: 13px;
  font-weight: 600;
  border: none;
  border-radius: 10px;
  background: linear-gradient(135deg, #5b7cfa, #7b5cfa);
  color: #fff;
  cursor: pointer;
  font-family: inherit;
  box-shadow: 0 5px 14px rgba(91, 124, 250, 0.28);
  transition: all 0.2s ease;
}
.btn-new-chat:hover {
  transform: translateY(-1px);
  box-shadow: 0 8px 18px rgba(91, 124, 250, 0.38);
}
.history-list {
  flex: 1;
  overflow-y: auto;
  padding-right: 4px;
}
.history-item-active {
  background: #eef2ff !important;
  border-left: 3px solid #5b7cfa;
  padding-left: 5px;
}
.history-item {
  padding: 10px 8px;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.2s;
  margin-bottom: 2px;
}
.history-item:hover {
  background: #f4f7ff;
}
.history-item-title {
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 4px;
  color: #3b4272;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.history-item-sub {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  color: #8a94b3;
  white-space: nowrap;      /* 防止换行成两行 */
}
.sub-mode {
  background: #f0f3fc;
  padding: 1px 6px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  flex-shrink: 0;           /* 模式标签不被压缩 */
}
.btn-del {
  border: none;
  background: transparent;
  color: #999;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  padding: 0;
  line-height: 1;
}
.btn-del:hover {
  color: #f56c6c;
}
.btn-del .el-icon {
  font-size: 11px;
  height: 11px;
}
.mode-text {
  color: #8a94b3;
  font-size: 11px;
  font-weight: normal;
  margin-left: 8px;         /* 从script-actions移到对话标题后，去掉原margin-left:auto */
}
.msg-hint {
  text-align: center;       /* 系统提示：居中小字 */
  color: #9aa3c0;
  font-size: 11px;
  margin: 10px 0;
}
.empty-history {
  text-align: center;
  color: #9aa3c0;
  margin-top: 30px;
  font-size: 13px;
}

/* ===== 右侧面板 ===== */
.right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  overflow: hidden;
  min-width: 0;
}

/* 课件面板（紧凑） */
.courseware-panel {
  flex-shrink: 0;
  max-height: 130px;
  overflow-y: auto;
}

/* 大框：左脚本 + 右对话 */
.big-box {
  flex: 1;
  display: flex;
  border-radius: 14px;
  padding: 14px;
  overflow: hidden;
  gap: 14px;
  min-height: 0;
}
.big-box .script-area {
  width: 40%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.big-box .script-area.hidden {
  display: none;
}
.big-box .chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.big-box .chat-area.full {
  width: 100%;
}

/* 脚本内容区 */
.script-content {
  border: 1px solid #e6ebf9;
  border-radius: 10px;
  padding: 12px;
  flex: 1;
  overflow-y: auto;
  white-space: pre-wrap;
  line-height: 1.7;
  background: #f8faff;
  font-size: 13px;
  color: #3b4272;
}
.script-actions {
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
  flex-wrap: wrap;
}
.btn-test {
  flex: 1;
  padding: 8px 0;
  font-size: 13px;
  font-weight: 700;
  border: none;
  border-radius: 9px;
  background: linear-gradient(135deg, #5b7cfa, #7b5cfa);
  color: #fff;
  cursor: pointer;
  font-family: inherit;
  box-shadow: 0 5px 12px rgba(91, 124, 250, 0.28);
  transition: all 0.2s ease;
}
.btn-test:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 8px 16px rgba(91, 124, 250, 0.38);
}
.btn-test:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 对话区 */
.chat-title {
  justify-content: flex-start;
}
.btn-exit-test {
  margin-left: auto;
  margin-right: 2px;
}
.chat-messages {
  border: 1px solid #e6ebf9;
  border-radius: 10px;
  padding: 12px;
  flex: 1;
  overflow-y: auto;
  background: #f8faff;
  min-height: 0;
}

/* 聊天气泡 */
.message {
  margin-bottom: 12px;
  display: flex;
}
.msg-row-user {
  justify-content: flex-end;
}
.msg-row-ai {
  justify-content: flex-start;
}
.msg-bubble {
  max-width: 78%;
  padding: 9px 13px;
  border-radius: 14px;
  font-size: 13px;
  line-height: 1.65;
  word-break: break-word;
  white-space: pre-wrap;
}
.bubble-user {
  background: linear-gradient(135deg, #5b7cfa, #7b5cfa);
  color: #ffffff;
  border-bottom-right-radius: 4px;
  box-shadow: 0 3px 10px rgba(91, 124, 250, 0.25);
}
.bubble-ai {
  background: #ffffff;
  color: #3b4272;
  border: 1px solid #e6ebf9;
  border-bottom-left-radius: 4px;
}
.empty-chat {
  color: #9aa3c0;
  text-align: center;
  margin-top: 100px;
  font-size: 13px;
}

/* 对话输入区（位于大框底部） */
.chat-input {
  margin-top: 10px;
  display: flex;
  gap: 10px;
  flex-shrink: 0;
}
.chat-input input {
  flex: 1;
  padding: 10px 14px;
  font-size: 13px;
  font-family: inherit;
  color: #2c3350;
  border: 1.5px solid #dde3f3;
  border-radius: 10px;
  background: #f8faff;
  outline: none;
  transition: all 0.2s ease;
}
.chat-input input::placeholder {
  color: #b3bcd6;
}
.chat-input input:focus {
  border-color: #5b7cfa;
  background: #ffffff;
  box-shadow: 0 0 0 4px rgba(91, 124, 250, 0.12);
}
.chat-input input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.btn-send {
  padding: 10px 26px;
  font-size: 13px;
  font-weight: 700;
  border: none;
  border-radius: 10px;
  background: linear-gradient(135deg, #5b7cfa, #7b5cfa);
  color: #fff;
  cursor: pointer;
  font-family: inherit;
  box-shadow: 0 5px 12px rgba(91, 124, 250, 0.28);
  transition: all 0.2s ease;
}
.btn-send:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 8px 16px rgba(91, 124, 250, 0.38);
}
.btn-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 表格样式 */
.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 12px;
}
.table th {
  background: #f4f6ff;
  color: #5b6790;
  padding: 7px 8px;
  text-align: left;
  font-weight: 600;
  white-space: nowrap;
}
.table td {
  padding: 6px 8px;
  border-bottom: 1px solid #eef1f9;
  vertical-align: middle;
  font-size: 12px;
  color: #3b4272;
}
.table tbody tr:hover {
  background: #f7f9ff;
}
.td-course {
  font-weight: 600;
  color: #2c3350;
}
.td-count {
  color: #8a94b3;
  text-align: center;
}
.td-ellipsis {
  max-width: 130px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.td-actions {
  white-space: nowrap;
}
.td-actions button {
  margin-right: 4px;
}
.table-sm th, .table-sm td {
  padding: 5px 7px;
}
.empty-cell {
  text-align: center;
  color: #9aa3c0;
  padding: 16px 8px !important;
}

/* ===== 状态徽标 ===== */
.status-badge {
  display: inline-block;
  padding: 2px 9px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
}
.status-done {
  color: #2fa96e;
  background: rgba(47, 169, 110, 0.12);
}
.status-processing {
  color: #e6922e;
  background: rgba(230, 146, 46, 0.13);
}
.status-pending {
  color: #8a94b3;
  background: #eef1f9;
}
.status-fail {
  color: #f56c6c;
  background: rgba(245, 108, 108, 0.12);
}

/* 按钮通用 */
.btn-small {
  padding: 3px 10px;
  font-size: 12px;
  border: 1.5px solid #e2e8f7;
  border-radius: 7px;
  background: #fff;
  color: #5b6790;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s ease;
}
.btn-small:hover:not(:disabled) {
  color: #5b7cfa;
  border-color: #5b7cfa;
  background: #f7f9ff;
}
.btn-small:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.btn-blue {
  color: #5b7cfa;
  border-color: #c9d5fb;
}
.btn-blue:hover:not(:disabled) {
  background: #f0f4ff;
}
.btn-danger {
  color: #f56c6c;
  border-color: #f8cdd3;
}
.btn-danger:hover:not(:disabled) {
  color: #f56c6c;
  border-color: #f56c6c;
  background: #fff5f5;
}

/* 评价弹窗 */
.evaluation-view {
  white-space: pre-wrap;
  line-height: 1.8;
  max-height: 70vh;
  overflow-y: auto;
  background: #f8faff;
  border: 1px solid #e6ebf9;
  border-radius: 12px;
  padding: 20px 24px;
  font-size: 14px;
  color: #3b4272;
}

/* 滚动条美化 */
::-webkit-scrollbar {
  width: 6px;
}
::-webkit-scrollbar-thumb {
  background: #c9d2ea;
  border-radius: 3px;
}
::-webkit-scrollbar-track {
  background: transparent;
}

/* ===== 等待课件提示条 ===== */
.courseware-required-hint {
  margin-bottom: 10px;
  padding: 10px 14px;
  background: #fff7e6;
  border: 1px solid #ffe7ba;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 12px;
  color: #8a6d3b;
  flex-shrink: 0;
}
.courseware-required-hint .hint-text {
  flex: 1;
  line-height: 1.5;
}

</style>
