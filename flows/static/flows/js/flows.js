/**
 * flows/static/flows/js/flows.js
 * Flows 模塊前端邏輯
 */

'use strict';

/* ════════════════════════════════════════
   1. 任務初始化
   POST /api/flows/my-tasks/init/
════════════════════════════════════════ */
async function initUserTasks() {
  // 嘗試初始化任務 (就算已經初始化過，後端也會優雅忽略)
  // 如果尚未登入，API 會回傳 403，由 apiFetch 自行處理
  try {
    await apiFetch('/api/flows/my-tasks/init/', 'POST');
  } catch (err) {
    console.error('Failed to init tasks:', err);
  }
}

/* ════════════════════════════════════════
   2. 讀取 Dashboard 狀態
   GET /api/flows/progress/
════════════════════════════════════════ */
async function renderDashboardProgress() {
  const dashCompletion = document.getElementById('dashCompletionRate');
  const dashRecentTasks = document.getElementById('dashRecentTasks');
  
  if (!dashCompletion && !dashRecentTasks) return; // 不在 dashboard
  
  const { ok, data } = await apiFetch('/api/flows/progress/');
  if (!ok) return;

  // 更新完成率
  if (dashCompletion) {
    dashCompletion.textContent = `${data.data.completion_rate}%`;
  }

  // 取得近期未完成的任務 (可以從 progress 裡面挖，或是直接呼叫 my-tasks API)
  // 這裡我們再打一次 my-tasks API 來抓前 3 筆未完成任務
  const tasksRes = await apiFetch('/api/flows/my-tasks/');
  if (dashRecentTasks && tasksRes.ok) {
    dashRecentTasks.innerHTML = '';
    const allStages = tasksRes.data.data.stages;
    const pendingTasks = [];
    
    // 攤平找出未完成的任務
    allStages.forEach(stage => {
      stage.tasks.forEach(task => {
        if (task.status !== 'completed') {
          pendingTasks.push(task);
        }
      });
    });

    if (pendingTasks.length === 0) {
      dashRecentTasks.innerHTML = `
        <div style="text-align:center;padding:16px 0;color:var(--muted);">
          🎉 太棒了！您目前沒有待辦任務。
        </div>
      `;
      return;
    }

    // 渲染前 3 筆
    pendingTasks.slice(0, 3).forEach(task => {
      dashRecentTasks.innerHTML += `
        <div style="padding:12px 16px;background:white;border-radius:8px;border:1px solid var(--border);display:flex;align-items:center;gap:12px;">
          <div style="width:12px;height:12px;border-radius:50%;background:var(--warning);"></div>
          <div style="flex:1;">
            <div style="font-weight:700;font-size:14px;">${task.task_detail.title}</div>
            <div style="font-size:12px;color:var(--muted);">${stage.stage_name || '流程階段'}</div>
          </div>
        </div>
      `;
    });
  }
}

/* ════════════════════════════════════════
   3. 渲染獨立的 my_flows.html
   GET /api/flows/my-tasks/
════════════════════════════════════════ */
async function renderMyTasks() {
  const container = document.getElementById('flowsContainer');
  if (!container) return;

  const { ok, data } = await apiFetch('/api/flows/my-tasks/');
  if (!ok) {
    container.innerHTML = `<div style="text-align:center;color:red;">載入失敗，請確認已登入並填寫學生資料。</div>`;
    return;
  }

  const stages = data.data.stages;
  container.innerHTML = '';

  if (!stages || stages.length === 0) {
    container.innerHTML = `
      <div style="text-align:center;padding:48px;background:white;border-radius:16px;">
        <h3 style="margin-bottom:12px;">尚未產生任務</h3>
        <p style="color:var(--muted);">請確保您已在「我的帳戶」中設定完學籍身分，並重新整理頁面。</p>
      </div>
    `;
    return;
  }

  stages.forEach(stage => {
    const total = stage.tasks.length;
    const completed = stage.tasks.filter(t => t.status === 'completed').length;
    const progressText = `${completed} / ${total} 完成`;

    let html = `
      <div class="stage-section">
        <div class="stage-header">
          <div class="stage-title">${stage.stage_name}</div>
          <div class="stage-progress">${progressText}</div>
        </div>
        <div class="task-list">
    `;

    stage.tasks.forEach(task => {
      const isDone = task.status === 'completed';
      html += `
        <div class="task-item ${isDone ? 'completed' : ''}" onclick="toggleTaskStatus(${task.id}, this)">
          <div class="task-checkbox"></div>
          <div class="task-content">
            <div class="task-title">${task.task_detail.title}</div>
            <div class="task-desc">${task.task_detail.description || '無詳細說明'}</div>
          </div>
        </div>
      `;
    });

    html += `</div></div>`;
    container.innerHTML += html;
  });
}

/* ════════════════════════════════════════
   4. 切換任務狀態
   PATCH /api/flows/my-tasks/<id>/update/
════════════════════════════════════════ */
async function toggleTaskStatus(studentTaskId, element) {
  const isCurrentlyDone = element.classList.contains('completed');
  const newStatus = isCurrentlyDone ? 'pending' : 'completed';

  // Optimistic UI update
  element.classList.toggle('completed');

  const { ok } = await apiFetch(`/api/flows/my-tasks/${studentTaskId}/update/`, 'PATCH', { status: newStatus });
  
  if (!ok) {
    // Revert on failure
    showToast('更新失敗', 'error');
    element.classList.toggle('completed');
    return;
  }

  showToast(newStatus === 'completed' ? '任務已完成！' : '任務已取消完成', 'success');
  
  // 重新計算進度標籤 (Optional: 或是直接重 call renderMyTasks)
  renderMyTasks(); 
}


/* ════════════════════════════════════════
   初始化
════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', async () => {
  // 當在 Dashboard 或是 Flows 頁面時，確保有任務
  if (document.getElementById('profileDash') || document.getElementById('flowsContainer')) {
    await initUserTasks();
  }

  // 渲染 Dashboard 資料
  if (document.getElementById('profileDash')) {
    renderDashboardProgress();
  }

  // 渲染我的任務頁面
  if (document.getElementById('flowsContainer')) {
    renderMyTasks();
  }
});
