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
  // 嘗試初始化任務，就算已經初始化過，後端也會忽略
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
   GET /api/flows/my-tasks/
════════════════════════════════════════ */
async function renderDashboardProgress() {
  const dashCompletion = document.getElementById('dashCompletionRate');
  const dashRecentTasks = document.getElementById('dashRecentTasks');
  const dashOverdueCount = document.getElementById('dashOverdueCount');

  // 如果三個都不存在，代表不在 dashboard 頁面
  if (!dashCompletion && !dashRecentTasks && !dashOverdueCount) return;

  /* ---------- 更新完成率 ---------- */
  try {
    const { ok, data } = await apiFetch('/api/flows/progress/');

    if (ok && data && data.data && dashCompletion) {
      const stages = data.data.stages || [];

      const total = stages.reduce((sum, stage) => sum + (stage.total || 0), 0);
      const completed = stages.reduce((sum, stage) => sum + (stage.completed || 0), 0);
      const percent = data.data.overall_percent || 0;

      const completedText = dashCompletion.getAttribute('data-completed-text') || '已完成';
      const itemsText = dashCompletion.getAttribute('data-items-text') || '項';

      dashCompletion.innerHTML = `
        ${percent}%<br>
        <span style="font-size:16px;font-weight:600;color:var(--muted);">
          ${completedText} ${completed} / ${total} ${itemsText}
        </span>
      `;
    }
  } catch (err) {
    console.error('Failed to render dashboard progress:', err);

    if (dashCompletion) {
      dashCompletion.textContent = '0%';
    }
  }

  /* ---------- 更新即將到期任務 + 近期待辦任務 ---------- */
  try {
    const tasksRes = await apiFetch('/api/flows/my-tasks/');

    if (!tasksRes.ok || !tasksRes.data || !tasksRes.data.data) {
      if (dashOverdueCount) dashOverdueCount.textContent = '0';
      return;
    }

    const allStages = tasksRes.data.data.stages || [];

    // 先更新「即將到期任務」數字
    // 重點：這段不要包在 dashRecentTasks 裡，不然 dashRecentTasks 沒載到時 dashOverdueCount 也會失敗
    if (dashOverdueCount) {
      const today = new Date();
      today.setHours(0, 0, 0, 0);

      const threeDaysLater = new Date(today);
      threeDaysLater.setDate(today.getDate() + 3);

      let overdueCount = 0;

      allStages.forEach(stage => {
        const tasks = stage.tasks || [];

        tasks.forEach(task => {
          if (task.due_date && task.status !== 'completed') {
            const due = new Date(task.due_date);
            due.setHours(0, 0, 0, 0);

            // 今天以前或三天內到期都算「即將到期」
            if (due <= threeDaysLater) {
              overdueCount++;
            }
          }
        });
      });

      dashOverdueCount.textContent = overdueCount;
    }

    // 再更新「近期待辦任務」
    if (dashRecentTasks) {
      dashRecentTasks.innerHTML = '';

      const pendingTasks = [];

      allStages.forEach(stage => {
        const tasks = stage.tasks || [];

        tasks.forEach(task => {
          if (task.status !== 'completed') {
            pendingTasks.push({
              ...task,
              stage_name: stage.stage_name
            });
          }
        });
      });

      if (pendingTasks.length === 0) {
        const noTasksText = dashRecentTasks.getAttribute('data-no-tasks') || '🎉 太棒了！您目前沒有待辦任務。';

        dashRecentTasks.innerHTML = `
          <div style="text-align:center;padding:16px 0;color:var(--muted);">
            ${noTasksText}
          </div>
        `;
        return;
      }

      pendingTasks.slice(0, 3).forEach(task => {
        dashRecentTasks.innerHTML += `
          <div style="padding:12px 16px;background:white;border-radius:8px;border:1px solid var(--border);display:flex;align-items:center;gap:12px;">
            <div style="width:12px;height:12px;border-radius:50%;background:var(--warning);"></div>
            <div style="flex:1;">
              <div style="font-weight:700;font-size:14px;">${task.task_detail ? task.task_detail.title : '未命名任務'}</div>
              <div style="font-size:12px;color:var(--muted);">${task.stage_name || '流程階段'}</div>
            </div>
          </div>
        `;
      });
    }
  } catch (err) {
    console.error('Failed to render dashboard tasks:', err);

    if (dashOverdueCount) {
      dashOverdueCount.textContent = '0';
    }

    if (dashRecentTasks) {
      dashRecentTasks.innerHTML = `
        <div style="text-align:center;padding:16px 0;color:var(--muted);">
          任務載入失敗，請重新整理頁面。
        </div>
      `;
    }
  }
}

/* ════════════════════════════════════════
   3. 渲染獨立的 my_flows.html
   GET /api/flows/my-tasks/
════════════════════════════════════════ */
let currentActiveTabIndex = 0;

window.switchFlowTab = function(activeIndex) {
  currentActiveTabIndex = activeIndex;
  
  const buttons = document.querySelectorAll('.flow-tab-btn:not(.skeleton)');
  buttons.forEach((btn, idx) => {
    if (idx === activeIndex) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  const sections = document.querySelectorAll('.stage-section:not(.skeleton)');
  sections.forEach((sec, idx) => {
    if (idx === activeIndex) {
      sec.classList.add('active');
    } else {
      sec.classList.remove('active');
    }
  });
};

async function renderMyTasks() {
  const container = document.getElementById('flowsContainer');
  if (!container) return;

  const { ok, data } = await apiFetch('/api/flows/my-tasks/');

  if (!ok) {
    container.innerHTML = `<div style="text-align:center;color:red;">載入失敗，請確認已登入並填寫學生資料。</div>`;
    return;
  }

  const stages = data.data.stages || [];
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

  if (currentActiveTabIndex >= stages.length) {
    currentActiveTabIndex = 0;
  }

  let tabsHtml = `<div class="flows-tabs">`;
  let contentHtml = ``;

  stages.forEach((stage, index) => {
    const isActive = index === currentActiveTabIndex ? 'active' : '';
    tabsHtml += `<button class="flow-tab-btn ${isActive}" onclick="switchFlowTab(${index})">${stage.stage_name}</button>`;
    
    const tasks = stage.tasks || [];
    const total = tasks.length;
    const completed = tasks.filter(t => t.status === 'completed').length;
    const progressText = `${completed} / ${total} 完成`;

    contentHtml += `
      <div class="stage-section ${isActive}">
        <div class="stage-header" style="justify-content: flex-end; border-bottom: none; padding-bottom: 0; margin-bottom: 16px;">
          <div class="stage-progress">${progressText}</div>
        </div>
        <div class="task-list">
    `;

    tasks.forEach(task => {
      const isDone = task.status === 'completed';
      contentHtml += `
        <div class="task-item ${isDone ? 'completed' : ''}" onclick="toggleTaskStatus(${task.id}, this)">
          <div class="task-checkbox"></div>
          <div class="task-content">
            <div class="task-title">${task.task_detail ? task.task_detail.title : '未命名任務'}</div>
            <div class="task-desc">${task.task_detail && task.task_detail.description ? task.task_detail.description : '無詳細說明'}</div>
          </div>
        </div>
      `;
    });

    contentHtml += `</div></div>`;
  });

  tabsHtml += `</div>`;
  container.innerHTML = tabsHtml + contentHtml;
}

/* ════════════════════════════════════════
   4. 切換任務狀態
   PATCH /api/flows/my-tasks/<id>/update/
════════════════════════════════════════ */
async function toggleTaskStatus(studentTaskId, element) {
  const isCurrentlyDone = element.classList.contains('completed');
  const newStatus = isCurrentlyDone ? 'not_started' : 'completed';

  // 先讓畫面即時變化
  element.classList.toggle('completed');

  const { ok } = await apiFetch(`/api/flows/my-tasks/${studentTaskId}/update/`, 'PATCH', {
    status: newStatus
  });

  if (!ok) {
    // 失敗就還原
    showToast('更新失敗', 'error');
    element.classList.toggle('completed');
    return;
  }

  showToast(newStatus === 'completed' ? '任務已完成！' : '任務已取消完成', 'success');

  // 重新渲染任務頁
  renderMyTasks();

  // 如果 dashboard 也有相關數字，順便重新更新
  renderDashboardProgress();
}

/* ════════════════════════════════════════
   5. 讀取並渲染通知
   GET /api/flows/reminders/
════════════════════════════════════════ */
window.toggleReminderDropdown = function () {
  const dropdown = document.getElementById('reminderDropdown');
  if (!dropdown) return;

  if (dropdown.style.display === 'none') {
    dropdown.style.display = 'block';
  } else {
    dropdown.style.display = 'none';
  }
};

async function renderReminders() {
  const { ok, data } = await apiFetch('/api/flows/reminders/?unread_only=true');
  if (!ok) return;

  const count = data.data.unread_count || 0;
  const reminders = data.data.reminders || [];

  const badge = document.getElementById('reminderBadge');
  const dashCount = document.getElementById('dashUnreadCount');
  const list = document.getElementById('reminderList');
  const dropdown = document.getElementById('reminderDropdown');

  const noRemindersText = dropdown ? dropdown.getAttribute('data-no-reminders') : '沒有未讀通知 🎉';
  const markReadText = dropdown ? dropdown.getAttribute('data-mark-read') : '標記為已讀';

  if (dashCount) {
    dashCount.textContent = count;
  }

  if (badge) {
    if (count > 0) {
      badge.style.display = 'inline-block';
      badge.textContent = count;
    } else {
      badge.style.display = 'none';
    }
  }

  // 如果目前頁面沒有通知清單，只更新 dashboard 數字即可
  if (!list) return;

  if (reminders.length === 0) {
    list.innerHTML = `
      <div style="padding:16px; text-align:center; color:var(--muted);">
        ${noRemindersText}
      </div>
    `;
    return;
  }

  list.innerHTML = '';

  reminders.forEach(r => {
    list.innerHTML += `
      <div id="reminder-${r.id}" style="padding:12px 16px; border-bottom:1px solid var(--border, #eee); display:flex; flex-direction:column; gap:4px; font-size:14px;">
        <div style="color:var(--text); line-height:1.4;">${r.message}</div>
        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:4px;">
          <span style="font-size:12px; color:var(--muted);">${new Date(r.created_at).toLocaleDateString()}</span>
          <button onclick="markReminderRead(${r.id})" style="background:none; border:none; color:var(--primary, #007bff); cursor:pointer; font-size:12px; padding:0;">${markReadText}</button>
        </div>
      </div>
    `;
  });
}

window.markReminderRead = async function (id) {
  const { ok } = await apiFetch(`/api/flows/reminders/${id}/read/`, 'PATCH');

  if (ok) {
    const item = document.getElementById(`reminder-${id}`);
    if (item) {
      item.style.opacity = '0.5';
    }

    setTimeout(() => {
      renderReminders();
    }, 500);
  }
};

/* ════════════════════════════════════════
   初始化
════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', async () => {
  // 當在 Dashboard 或 Flows 頁面時，確保有任務
  if (document.getElementById('profileDash') || document.getElementById('flowsContainer')) {
    await initUserTasks();
  }

  if (document.getElementById('profileDash')) {
    await renderDashboardProgress();
  }

  if (document.getElementById('flowsContainer')) {
    await renderMyTasks();
  }

  if (document.getElementById('reminderBtn') || document.getElementById('profileDash')) {
    await renderReminders();
  }
});