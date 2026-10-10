<template>
  <div class="teacher-page">
    <!-- 顶部 Header -->
    <div class="top-header">
      <div class="header-left">
        <div class="header-logo">🎓</div>
        <div class="header-title">
          <span class="header-name">教师工作台</span>
          <span class="header-sub">AI互动智课生成与实时问答系统</span>
        </div>
      </div>
      <div class="header-right">
        <span class="welcome">欢迎，{{ tea_name }}</span>
        <button @click="logout" class="btn-logout">退出登录</button>
      </div>
    </div>

    <!-- 主体：左上传 + 右列表 -->
    <div class="main-container">
      <!-- 上传表单卡片 -->
      <div class="panel-card upload-card">
        <h3 class="card-title"><span class="title-dot"></span>课件上传与处理</h3>

        <div class="form-item">
          <label class="form-label">课程名称</label>
          <input type="text" v-model="courseName" class="form-input" placeholder="例如：材料力学">
        </div>

        <div class="form-item">
          <label class="form-label">章节名称</label>
          <input type="text" v-model="chapterName" class="form-input" placeholder="例如：第一章 绪论">
        </div>

        <div class="form-item">
          <label class="form-label">上传课件</label>
          <!--
            在文件选择器中选好文件并点击"确定"后，change 事件被触发
            对于 <input type="file"> 元素，它有一个特殊的属性叫 files
            如果 input 没有 multiple 属性（只能选一个文件），files 里最多只有 1 个文件。
            如果 input 有 multiple 属性（可以多选），files 里会有多个文件。
          -->
          <input type="file" @change="choiceFile" accept=".ppt,.pptx,.pdf" class="file-input">
          <div class="file-tip">仅支持 PPT / PPTX / PDF，不超过 100MB</div>
        </div>

        <!-- 上传按钮只负责上传 -->
        <button @click="uploadFile" :disabled="uploading" class="btn-primary">
          {{ uploading ? '上传中...' : '上传课件' }}
        </button>

        <div class="upload-steps">
          <div class="step"><span class="step-num">1</span>填写课程与章节</div>
          <div class="step"><span class="step-num">2</span>选择课件文件</div>
          <div class="step"><span class="step-num">3</span>点击上传并处理</div>
        </div>
      </div>

      <!-- 已上传课件列表卡片 -->
      <div class="panel-card list-card">
        <div class="card-head-row">
          <h3 class="card-title"><span class="title-dot"></span>已上传课件</h3>
          <button @click="fetchCoursewareList" class="btn-small">刷新列表</button>
        </div>

        <table class="table">
          <thead>
            <tr>
              <th>文件名</th>
              <th>课程</th>
              <th>章节</th>
              <th>状态</th>
              <th>上传时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in coursewareList" :key="item.id">
              <td class="td-ellipsis">{{ item.original_filename }}</td>
              <td>{{ item.course_name }}</td>
              <td>{{ item.chapter_name }}</td>
              <td>
                <span class="status-badge"
                      :class="item.parse_status === 1 ? 'status-done' : item.parse_status === 0 ? 'status-processing' : item.parse_status === 2 ? 'status-pending' : 'status-fail'">
                  {{ getStatusText(item.parse_status) }}
                </span>
              </td>
              <td class="td-time">{{ item.upload_time }}</td>
              <td class="td-actions">
                <button @click="processCourseware(item)" :disabled="uploading" class="btn-small">处理</button>
                <button @click="viewScript(item)" class="btn-small btn-blue"
                        :disabled="item.parse_status !== 1 || generatingId === item.id">
                  {{ generatingId === item.id ? '生成中...' : '查看脚本' }}
                </button>
                <button @click="deleteCourseware(item)" :disabled="uploading" class="btn-small btn-danger">删除</button>
              </td>
            </tr>
            <tr v-if="coursewareList.length === 0">
              <td colspan="6" class="empty-cell">暂无上传记录，请先在左侧上传课件</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 脚本查看弹窗 -->
    <el-dialog v-model="scriptVisible" :title="scriptTitle" width="70%" top="5vh">
      <div class="script-view">
        {{ scriptContent }}
      </div>
      <template #footer>
        <span class="dialog-left">
          <button @click="regenerateScript" class="btn-small btn-blue"
                  :disabled="generatingId !== null">
            {{ generatingId !== null ? '生成中...' : '重新生成' }}
          </button>
        </span>
        <button @click="scriptVisible = false" class="btn-small">关 闭</button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import {ref, getCurrentInstance, onMounted, onUnmounted} from "vue";
import {useRouter} from "vue-router";
import {ElMessage} from "element-plus";

// 加载页面后自动执行功能 -- 获取已上传列表、获取当前角色名、用户名
let identity = ref("")
let tea_name = ref("")
onMounted(() => {
  identity.value = sessionStorage.getItem("identity");
  tea_name.value = sessionStorage.getItem("name");
  fetchCoursewareList();
  // 页面加载即检查轮询：若有处理中的课件，处理完成后自动刷新+提醒；没有则立即自动停止
  startPollingStatus(true);
});

// 获取当前实例和路由跳转对象
let proxy = getCurrentInstance().proxy;
let router = useRouter();
// 退出登录：调后端将token加入黑名单，清除本地登录态，回首页
function logout(){
  proxy.$axios({
    url: 'account/logout',
    method: 'post'
  }).finally(() => {
    sessionStorage.clear();
    router.push('/');
  });
}

// 表单数据
let courseName = ref(''); // 课程名称
let chapterName = ref('');  // 章节名称
let selectedFile = ref(null); // 选择文件
let uploading = ref(false); // 上传状态
let coursewareList = ref([]); // 已上传课件列表

// 文件选择变化 -- 点击选择文件按钮触发
// event 是浏览器产生的，vue自动把浏览器生成“事件对象（event）”，作为第一个参数传递给 choiceFile 函数
function choiceFile(event) {
  // 从触发事件的 input 元素中，取出用户选中的第一个文件
  // event.target：找到触发事件的元素，指向的是触发这次事件的那个 HTML 元素 -- input
  // .files：获取文件列表 -- 这是一个类数组对象，里面存放着用户选中的所有文件
  let file = event.target.files[0]; // 获取选中的第一个文件
  // 如果文件不存在，退出
  if (!file) return;
  // 拿到的 file 包含 -- name文件名、size文件大小（字节）、type文件类型
  // 从文件名里提取出文件后缀（扩展名），并统一转成小写
  // substring：截取；lastIndexOf('.')：找到最后一个.的位置；toLowerCase()：转为小写
  let ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();  // 获取后缀

  // 判断后缀
  if (ext !== '.ppt' && ext !== '.pptx' && ext !== '.pdf') {
    ElMessage.error('仅支持PPT/PPTX/PDF文件');
    // 文件格式不合格，重置文件选择框
    event.target.value = '';
    return;
  }

  // 判断文件大小
  if (file.size > 100 * 1024 * 1024) {
    ElMessage.error('文件不能超过100MB');
    // 文件过大，重置文件选择框
    event.target.value = '';
    return;
  }

  // 将选择的文件，赋值给表单变量selectedFile
  selectedFile.value = file;
  console.log("【测试】选择文件成功！")
}

// 提交上传
function uploadFile() {
  // 判断是否选择文件，相关信息是否已输入
  if (!courseName.value || !chapterName.value || !selectedFile.value) {
    ElMessage.warning('请填写课程名称、章节名称并选择文件');
    return;
  }

  // 上传状态
  uploading.value = true;

  // 创建一个空的表单数据对象
  // 普通的 JSON 对象不能直接传文件。如果要上传文件（比如图片、PPT），必须用 FormData 来打包，它会按照 multipart/form-data 的格式组织数据，这是后端接收文件的标准格式
  let formData = new FormData();

  // 向表单中添加普通字段
  formData.append('file', selectedFile.value);
  formData.append('course_name', courseName.value);
  formData.append('chapter_name', chapterName.value);

  // 将文件传递给后端服务器
  proxy.$axios({
    url: 'courseware/upload',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  }).then(res => {
    console.log("【测试】上传文件返回结果：",res.data)
    let code = res.data.code;
    let message = res.data.message;

    if (code === 200) {
      ElMessage.success(message);
      // 清空表单
      courseName.value = '';
      chapterName.value = '';
      selectedFile.value = null;
      // 刷新列表
      fetchCoursewareList();
    } else {
      ElMessage.error(message);
    }
  }).catch(err => {
    console.log("【测试】上传失败：", err);
    ElMessage.error('上传失败，请重试');
  }).finally(() => {
    // 更新上传状态
    uploading.value = false;
  });
}

// 处理函数，点击表格里的处理按钮时触发
function processCourseware(item) {
  uploading.value = true;
  console.log("【测试】处理课件中......");
  proxy.$axios({
    url: 'courseware/parse',
    method: 'post',
    data: {
      original_filename: item.original_filename,
      file_path: item.file_path,
      course_name: item.course_name,
      chapter_name: item.chapter_name,
      id: item.id
    }
  }).then(res => {
    if (res.data.code === 200) {
      ElMessage.info('课件已开始后台处理，处理完成后会自动提醒');
      fetchCoursewareList();
      startPollingStatus();
    } else {
      ElMessage.error(res.data.message);
    }
  }).catch(err => {
    console.log("【测试】处理失败：", err);
    ElMessage.error('处理失败，请重试');
  }).finally(() => {
    uploading.value = false;
  });
}

// 轮询状态，直到处理结束
// silent=true：静默模式（页面加载时的检查），发现没有处理中的课件时直接停止，不弹提示
let pollTimer = null; // 计时器
function startPollingStatus(silent = false) {
  clearInterval(pollTimer);
  pollTimer = setInterval(() => {
    // 先等列表刷新完成，再用最新数据判断是否停止轮询
    fetchCoursewareList().then(() => {
      // 没有状态为0（处理中）的课件时停止轮询
      if (!coursewareList.value.some(item => item.parse_status === 0)) {
        clearInterval(pollTimer);
        // 静默模式直接退出（处理中刷新/重进页面后，后台完成时由这里的轮询补上刷新，不重复打扰）
        if (silent) return;
        // 区分成功和失败：有状态为3（失败）的课件时，提示失败
        let failed = coursewareList.value.some(item => item.parse_status === 3);
        if (failed) {
          ElMessage.error('有课件处理失败，请重新处理');
        } else {
          ElMessage.success('课件处理完成');
        }
      }
    });
  }, 5000);
}

// 获取已上传课件列表
function fetchCoursewareList() {
  return proxy.$axios({
    url: 'courseware/list',
    method: 'get'
  }).then(res => {
    console.log("【测试】获取课件列表返回结果：",res.data)
    if (res.data.code === 200) {
      // 更新课件列表信息
      coursewareList.value = res.data.data;
    }
  }).catch(err => {
    console.log("获取列表失败：", err);
  });
}

function getStatusText(status) {
  if (status === 1) return '已完成';
  if (status === 0) return '处理中';
  if (status === 2) return '未处理';
  return '失败';
}

// 删除课件（级联删除该课件的所有数据）
function deleteCourseware(item){
  if (!confirm(`确定删除课件"${item.original_filename}"吗？\n将删除所有内容，且不可恢复！`)) {
    return;
  }
  proxy.$axios({
    url: 'courseware/delete',
    method: 'post',
    data: {
      original_filename: item.original_filename,
      file_path: item.file_path,
      course_name: item.course_name,
      chapter_name: item.chapter_name,
      id: item.id
    }
  }).then(res => {
    if (res.data.code === 200) {
      ElMessage.success('课件及所有相关数据已删除');
      fetchCoursewareList();  // 刷新列表
    } else {
      ElMessage.error(res.data.message);
    }
  }).catch(err => {
    console.log("【测试】删除课件失败：", err);
    ElMessage.error('删除失败，请重试');
  })

}


let scriptVisible = ref(false);
let scriptContent = ref('');
let scriptTitle = ref('授课脚本');
let generatingId = ref(null); // 正在查看/生成脚本的课件id
let currentScriptItem = ref(null); // 当前查看脚本的课件（供删除/重新生成使用）


// 查看脚本
function viewScript(item) {
  generatingId.value = item.id;
  currentScriptItem.value = item;  // 记住当前课件，供弹窗按钮使用
  // 首次查看会现场生成脚本，给出提示避免用户以为卡死
  ElMessage.info('正在获取脚本，若首次查看约需1-2分钟生成，请稍候');
  console.log("【测试】查看脚本中...");
  proxy.$axios({
    url: 'courseware/script',
    method: 'get',
    params: {
      courseware_id: item.id,
      course_name: item.course_name,
      chapter_name: item.chapter_name
    },
    timeout: 180000  // 脚本不存在时会现场调用LLM生成，放宽超时到3分钟
  }).then(res => {
    if (res.data.code === 200) {
      scriptTitle.value = `授课脚本 - ${item.course_name} / ${item.chapter_name}`;
      scriptContent.value = res.data.data.content;
      scriptVisible.value = true;
      // 现场生成的（非已有文件），提示生成完成
      if (res.data.data.generated) {
        ElMessage.success('授课脚本生成完成');
      }
    } else {
      ElMessage.warning(res.data.message);
    }
  }).catch(err => {
    console.log("【测试】获取脚本失败：", err);
    ElMessage.error('获取脚本失败，请重试');
  }).finally(() => {
    generatingId.value = null;
  });
}


// 重新生成脚本：先删旧文件，再走现有查看接口现场生成
function regenerateScript() {
  if (!currentScriptItem.value) return;
  if (!confirm('确定重新生成脚本吗？当前脚本将被覆盖。')) return;
  proxy.$axios({
    url: 'courseware/script/delete',
    method: 'post',
    data: {
      courseware_id: currentScriptItem.value.id,
      course_name: currentScriptItem.value.course_name,
      chapter_name: currentScriptItem.value.chapter_name
    }
  }).then(res => {
    if (res.data.code === 200) {
      // 旧文件已删，viewScript会现场生成并展示新脚本
      viewScript(currentScriptItem.value);
    }
  }).catch(err => {
    console.log("【测试】重新生成失败：", err);
    ElMessage.error('重新生成失败，请重试');
  });
}

// 组件卸载（离开页面）时清理轮询定时器
onUnmounted(() => {
  clearInterval(pollTimer);
});

</script>

<style scoped>
/* ===== 页面容器 ===== */
.teacher-page {
  min-height: 100vh;
  background: linear-gradient(120deg, #f0f5ff 0%, #e8eeff 40%, #f4f1ff 100%);
  font-family: "Segoe UI", "Microsoft YaHei", Arial, sans-serif;
  display: flex;
  flex-direction: column;
}

/* ===== 顶部 Header ===== */
.top-header {
  background: #ffffff;
  padding: 14px 28px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 12px rgba(30, 40, 90, 0.06);
  position: sticky;
  top: 0;
  z-index: 10;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.header-logo {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: linear-gradient(135deg, #f59e6b, #f0763c);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  box-shadow: 0 4px 12px rgba(240, 118, 60, 0.3);
}
.header-title {
  display: flex;
  flex-direction: column;
}
.header-name {
  font-size: 17px;
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

/* ===== 主体两栏 ===== */
.main-container {
  flex: 1;
  display: flex;
  gap: 20px;
  padding: 24px 28px 32px;
  align-items: flex-start;
}

/* ===== 通用卡片 ===== */
.panel-card {
  background: #ffffff;
  border-radius: 18px;
  box-shadow: 0 8px 30px rgba(30, 40, 90, 0.07);
  padding: 24px;
  box-sizing: border-box;
}
.card-title {
  margin: 0 0 18px;
  font-size: 16px;
  font-weight: 700;
  color: #2c3350;
  display: flex;
  align-items: center;
  gap: 8px;
}
.title-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: linear-gradient(135deg, #5b7cfa, #7b5cfa);
  flex-shrink: 0;
}
.card-head-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
}
.card-head-row .card-title {
  margin: 0;
}

/* ===== 上传卡片（左栏） ===== */
.upload-card {
  width: 340px;
  flex-shrink: 0;
  position: sticky;
  top: 88px;
}
.form-item {
  display: flex;
  flex-direction: column;
  gap: 7px;
  margin-bottom: 16px;
}
.form-label {
  font-size: 13px;
  color: #4a5070;
  font-weight: 600;
}
.form-input {
  width: 100%;
  padding: 10px 13px;
  font-size: 14px;
  color: #2c3350;
  border: 1.5px solid #dde3f3;
  border-radius: 10px;
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
.file-input {
  width: 100%;
  padding: 9px 12px;
  font-size: 13px;
  color: #4a5070;
  border: 1.5px dashed #c4cdf0;
  border-radius: 10px;
  background: #f8faff;
  cursor: pointer;
  box-sizing: border-box;
  transition: all 0.2s ease;
}
.file-input:hover {
  border-color: #5b7cfa;
  background: #f0f4ff;
}
.file-tip {
  color: #9aa3c0;
  font-size: 12px;
  margin-top: 6px;
}
.btn-primary {
  width: 100%;
  margin-top: 4px;
  padding: 11px 0;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 700;
  color: #fff;
  font-family: inherit;
  cursor: pointer;
  background: linear-gradient(135deg, #5b7cfa, #7b5cfa);
  box-shadow: 0 8px 18px rgba(91, 124, 250, 0.3);
  transition: all 0.2s ease;
}
.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 12px 24px rgba(91, 124, 250, 0.4);
}
.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.upload-steps {
  margin-top: 22px;
  padding-top: 18px;
  border-top: 1px dashed #e3e8f5;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.step {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: #6b7394;
}
.step-num {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #eef2ff;
  color: #5b7cfa;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

/* ===== 列表卡片（右栏） ===== */
.list-card {
  flex: 1;
  min-width: 0;
  overflow-x: auto;
}

/* ===== 表格 ===== */
.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.table th {
  background: #f4f6ff;
  color: #5b6790;
  padding: 11px 10px;
  text-align: left;
  font-weight: 600;
  white-space: nowrap;
}
.table th:first-child {
  border-radius: 8px 0 0 8px;
}
.table th:last-child {
  border-radius: 0 8px 8px 0;
}
.table td {
  padding: 12px 10px;
  border-bottom: 1px solid #eef1f9;
  color: #3b4272;
  vertical-align: middle;
}
.table tbody tr {
  transition: background 0.15s ease;
}
.table tbody tr:hover {
  background: #f7f9ff;
}
.td-ellipsis {
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 600;
  color: #2c3350;
}
.td-time {
  white-space: nowrap;
  color: #8a94b3;
  font-size: 12px;
}
.td-actions {
  white-space: nowrap;
}
.td-actions button {
  margin-right: 6px;
}
.empty-cell {
  text-align: center;
  color: #9aa3c0;
  padding: 42px 10px !important;
  font-size: 13px;
}

/* ===== 状态徽标 ===== */
.status-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 12px;
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

/* ===== 小按钮 ===== */
.btn-small {
  padding: 5px 12px;
  font-size: 12px;
  border-radius: 7px;
  border: 1.5px solid #e2e8f7;
  background: #ffffff;
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

/* ===== 弹窗 ===== */
.dialog-left {
  float: left;
}
.script-view {
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

/* ===== 滚动条美化 ===== */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-thumb {
  background: #c9d2ea;
  border-radius: 3px;
}
::-webkit-scrollbar-track {
  background: transparent;
}

/* ===== 响应式 ===== */
@media (max-width: 900px) {
  .main-container {
    flex-direction: column;
    padding: 18px 16px 28px;
  }
  .upload-card {
    width: 100%;
    position: static;
  }
}
</style>
