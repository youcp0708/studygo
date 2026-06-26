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
              <div style="font-weight:700;font-size:14px;">${task.localized ? task.localized.title : (task.task_detail ? task.task_detail.title : '未命名任務')}</div>
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

window.switchFlowTab = function (activeIndex) {
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

let progressChartInstance = null;

async function renderProgressChart() {
  const chartCard = document.getElementById('chartCard');
  const canvas = document.getElementById('progressChart');
  if (!chartCard || !canvas) return;

  try {
    const { ok, data } = await apiFetch('/api/flows/progress/');
    if (!ok || !data || !data.data) return;

    chartCard.style.display = 'block';

    const stages = data.data.stages || [];
    let totalCompleted = 0;
    let totalPending = 0;
    stages.forEach(s => {
      totalCompleted += s.completed;
      totalPending += (s.total - s.completed);
    });

    const total = totalCompleted + totalPending;
    const percent = total === 0 ? 0 : Math.round((totalCompleted / total) * 100);

    if (progressChartInstance) {
      progressChartInstance.destroy();
    }

    const completedLabel = window.UI_STRINGS?.completedTasks || '已完成任務';
    const pendingLabel = window.UI_STRINGS?.inProgressTasks || '未完成任務';

    // 移除之前加的 HTML div (如果有)
    const percentDiv = document.getElementById('chartPercentLabel');
    if (percentDiv) {
      percentDiv.remove();
    }

    // ── Chart.js 自訂外掛：繪製半圓內底色與文字 ──
    const semiCirclePlugin = {
      id: 'semiCirclePlugin',
      beforeDraw: (chart) => {
        const { ctx } = chart;
        const meta = chart.getDatasetMeta(0);
        if (!meta || !meta.data || meta.data.length === 0) return;

        const arc = meta.data[0];
        const x = arc.x;
        const y = arc.y;
        const innerRadius = arc.innerRadius;

        ctx.save();

        // 1. 繪製內圈半圓底色
        ctx.beginPath();
        // 畫半圓: 從 PI (左) 到 0 (右)
        ctx.arc(x, y, innerRadius, Math.PI, 0);
        ctx.fillStyle = '#f3f5f7'; // 截圖中的淺灰藍色
        ctx.fill();

        // 2. 繪製置中百分比文字
        const text = percent + '%';
        const fontSize = Math.max(16, innerRadius * 0.45); // 隨圖表大小縮放
        ctx.font = `800 ${fontSize}px "Inter", "Segoe UI", sans-serif`;
        ctx.fillStyle = '#1f2937';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        // 將文字放在半圓內的視覺中心 (大約是半徑的一半高度)
        ctx.fillText(text, x, y - (innerRadius * 0.4));

        ctx.restore();
      }
    };

    progressChartInstance = new Chart(canvas, {
      type: 'doughnut',
      data: {
        labels: [completedLabel, pendingLabel],
        datasets: [{
          data: [totalCompleted, totalPending],
          backgroundColor: ['#059669', '#e5e7eb'], // 原本的綠色與灰色
          borderWidth: 0,
          borderRadius: 5
        }]
      },
      options: {
        rotation: -90,
        circumference: 180,
        responsive: true,
        maintainAspectRatio: true,
        aspectRatio: 1.5, // 半圓形的比例
        cutout: '72%', // 調整空心比例，讓進度條稍微粗一點點
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              padding: 14,
              usePointStyle: true,
              pointStyleWidth: 10,
              font: { size: 13, weight: '600' },
              color: '#495057'
            }
          }
        }
      },
      plugins: [semiCirclePlugin]
    });
  } catch (err) {
    console.error('Chart error', err);
  }
}

window.toggleTaskCompletion = async function (taskId, event) {
  event.stopPropagation();
  const checkbox = event.target;
  const newStatus = checkbox.checked ? 'completed' : 'not_started';

  const { ok } = await apiFetch(`/api/flows/my-tasks/${taskId}/update/`, 'PATCH', { status: newStatus });
  if (ok) {
    showToast(newStatus === 'completed' ? '任務已完成' : '已取消完成', 'success');
    renderMyTasks();
    renderDashboardProgress();
    renderReminders();
  } else {
    showToast('狀態更新失敗', 'error');
    checkbox.checked = !checkbox.checked; // revert
  }
};

window.changeTaskStatus = async function (taskId, status, event) {
  event.stopPropagation();
  const { ok } = await apiFetch(`/api/flows/my-tasks/${taskId}/update/`, 'PATCH', { status });
  if (ok) {
    showToast('狀態更新成功', 'success');
    renderMyTasks();
    renderDashboardProgress();
    renderReminders();
  }
};

window.toggleTaskDetails = function (taskId) {
  const details = document.getElementById(`details-${taskId}`);
  if (details) {
    details.classList.toggle('active');
  }
};

window.saveTaskNote = async function (taskId, event) {
  event.stopPropagation();
  const noteInput = document.getElementById(`note-${taskId}`);
  const note = noteInput ? noteInput.value : '';
  const { ok } = await apiFetch(`/api/flows/my-tasks/${taskId}/update/`, 'PATCH', { note });
  if (ok) showToast('備註已儲存', 'success');
};

window.saveTaskDate = async function (taskId, event) {
  event.stopPropagation();
  const dateInput = document.getElementById(`date-${taskId}`);
  const due_date = dateInput ? dateInput.value : '';
  const { ok } = await apiFetch(`/api/flows/my-tasks/${taskId}/update/`, 'PATCH', { due_date });
  if (ok) showToast('日期已儲存', 'success');
};

async function renderMyTasks() {
  const container = document.getElementById('flowsContainer');
  if (!container) return;

  await renderProgressChart();

  const { ok, data } = await apiFetch('/api/flows/my-tasks/');

  if (!ok) {
    container.innerHTML = `<div style="text-align:center;color:red;">載入失敗，請確認已登入並填寫學生資料。</div>`;
    return;
  }

  const stages = data.data.stages || [];
  container.innerHTML = '';

  if (!stages || stages.length === 0) {
    container.innerHTML = `
      <div style="text-align:center;padding:48px;background:white;border-radius:14px;border:1px solid #e5e8e6;">
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
    const progressText = `${completed} / ${total} ${window.UI_STRINGS.completedProgress}`;

    contentHtml += `
      <div class="stage-section ${isActive}">
        <div class="stage-header">
          <div class="stage-progress">${progressText}</div>
        </div>
        <div class="task-list">
    `;

    tasks.forEach(task => {
      const isDone = task.status === 'completed';
      // ── 使用後端已本地化的文字欄位 ──
      const loc = task.localized || task.task_detail || {};
      const deadlineInfo = task.deadline_info || {};

      const reqDocs = loc.required_documents || null;
      const applyLoc = loc.apply_location ? loc.apply_location.trim() : null;
      const applyAddr = loc.apply_address ? loc.apply_address.trim() : null;
      const officialUrl = loc.official_url
        ? `<a href="${loc.official_url}" target="_blank" style="color:var(--primary);text-decoration:underline;">${window.UI_STRINGS.visitOfficialWebsite}</a>`
        : null;
      const noteVal = task.note || '';
      const requiredBadge = task.task_detail?.is_required
        ? '<span class="task-badge required">必做</span>'
        : '<span class="task-badge optional">建議</span>';

      // ── 期限資訊區塊（deadline_text 已在後端本地化）──
      let deadlineHtml = '';
      if (deadlineInfo.type === 'text_only' && deadlineInfo.text) {
        deadlineHtml = `
          <div class="deadline-block">
            <div class="detail-label">${window.UI_STRINGS.taskSchedule}</div>
            <div class="detail-value">${deadlineInfo.text}</div>
          </div>`;
      } else if (deadlineInfo.type === 'from_arrival') {
        if (deadlineInfo.arrival_missing) {
          deadlineHtml = `
            <div class="deadline-block warning">
              <div class="detail-label">${window.UI_STRINGS.deadlineWarning}</div>
              <div class="detail-value">${window.UI_STRINGS.fillArrivalDatePrompt}</div>
              ${deadlineInfo.text ? `<div style="margin-top:6px;color:#555;">${deadlineInfo.text}</div>` : ''}
            </div>`;
        } else {
          deadlineHtml = `
            <div class="deadline-block">
              <div class="detail-label">${window.UI_STRINGS.deadline}</div>
              <div class="detail-value" style="font-size:15px; font-weight:700; color:#059669;">${deadlineInfo.calculated_due_date}</div>
              ${deadlineInfo.text ? `<div style="margin-top:4px; font-size:13px; color:#555;">${deadlineInfo.text}</div>` : ''}
            </div>`;
        }
      } else if (deadlineInfo.type === 'absolute') {
        deadlineHtml = `
          <div class="deadline-block">
            <div class="detail-label">${window.UI_STRINGS.deadline}</div>
            <div class="detail-value" style="font-size:15px; font-weight:700; color:#059669;">${deadlineInfo.calculated_due_date || ''}</div>
            ${deadlineInfo.text ? `<div style="margin-top:4px; font-size:13px; color:#555;">${deadlineInfo.text}</div>` : ''}
          </div>`;
      }

      // ── 只顯示有資料的欄位 ──
      const applyMapUrl = loc.apply_map_url || null;

      const detailRows = [
        reqDocs ? `
          <div class="detail-row">
            <div class="detail-label">${window.UI_STRINGS.requiredDocs}</div>
            <div class="detail-value" style="white-space: pre-wrap;">${reqDocs}</div>
          </div>` : '',

        (applyLoc || applyAddr || applyMapUrl) ? `
          <div class="detail-row">
            <div class="detail-label">${window.UI_STRINGS.applyLocation}</div>
            <div class="detail-value">
              ${applyLoc ? `<div>${applyLoc}</div>` : ''}
              ${applyAddr ? `<div style="color:var(--muted);font-size:13px;">${applyAddr}</div>` : ''}
              ${applyMapUrl ? `<a href="${applyMapUrl}" target="_blank" style="display:inline-flex;align-items:center;gap:4px;margin-top:6px;color:var(--primary);font-weight:600;text-decoration:none;font-size:13px;">${window.UI_STRINGS.viewOnMap}</a>` : ''}
            </div>
          </div>` : '',

        officialUrl ? `
          <div class="detail-row">
            <div class="detail-label">${window.UI_STRINGS.officialWebsite}</div>
            <div class="detail-value">${officialUrl}</div>
          </div>` : '',
      ].join('');

      contentHtml += `
        <div id="task-${task.id}" class="task-item ${isDone ? 'completed' : ''}">
          <div class="task-item-row" onclick="toggleTaskDetails(${task.id})">
            <input type="checkbox" id="chk-${task.id}" onclick="toggleTaskCompletion(${task.id}, event)" ${isDone ? 'checked' : ''}>
            <div class="task-content">
              <div class="task-title">
                ${loc.title || window.UI_STRINGS.unnamedTask}
                ${requiredBadge}
                ${loc.has_fallback ? `<span class="task-badge" style="background:#fef3c7;color:#d97706;border:1px solid #fcd34d;">Untranslated</span>` : ''}
              </div>
              <div class="task-desc" style="white-space: pre-wrap;">${loc.description || ''}</div>
            </div>
            ${isDone ? `<span class="task-completed-badge">${window.UI_STRINGS.completedBadge}</span>` : ''}
          </div>
          <div id="details-${task.id}" class="task-details" onclick="event.stopPropagation()">
            ${detailRows || `<div style="color:var(--muted);font-size:13px;">${window.UI_STRINGS.noDetails}</div>`}
            ${deadlineHtml}
            <div class="detail-row" style="margin-top:10px;">
              <div class="detail-label">${window.UI_STRINGS.taskNotes}</div>
              <textarea id="note-${task.id}" class="task-note-input" rows="3" placeholder="${window.UI_STRINGS.enterNotesPlaceholder}">${noteVal}</textarea>
              <button class="btn-save-note" onclick="saveTaskNote(${task.id}, event)">${window.UI_STRINGS.saveNotesBtn}</button>
            </div>
          </div>
        </div>
      `;
    });


    contentHtml += `</div></div>`;
  });

  tabsHtml += `</div>`;
  container.innerHTML = tabsHtml + contentHtml;

  const hash = window.location.hash;
  if (hash && hash.startsWith('#task-')) {
    const target = document.querySelector(hash);
    if (target) {
      const section = target.closest('.stage-section');
      if (section) {
        const sections = document.querySelectorAll('.stage-section:not(.skeleton)');
        const tabIndex = Array.from(sections).indexOf(section);
        if (tabIndex !== -1) switchFlowTab(tabIndex);
      }
      setTimeout(() => {
        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
        target.classList.add('task-highlight');
      }, 150);
    }
  }
}


/* ════════════════════════════════════════
   4. 渲染小貼士
   GET /api/flows/tips/
════════════════════════════════════════ */
async function renderTips() {
  const tipsCard = document.getElementById('tipsCard');
  const tipsContainer = document.getElementById('tipsContainer');
  if (!tipsCard || !tipsContainer) return;

  try {
    const { ok, data } = await apiFetch('/api/flows/tips/');
    if (!ok || !data || !data.data) return;

    const tips = data.data.tips || [];
    if (tips.length === 0) return;

    tipsCard.style.display = 'block';
    const visitText = window.UI_STRINGS?.visitLink || '前往查看';

    let html = '';
    tips.forEach(tip => {
      html += `
        <div class="tip-item">
          <div class="tip-item-title">
            ${tip.title}
            ${tip.has_fallback ? `<span class="task-badge" style="background:#fef3c7;color:#d97706;border:1px solid #fcd34d;">Untranslated</span>` : ''}
          </div>
          ${tip.content ? `<div class="tip-item-content">${tip.content}</div>` : ''}
      `;

      if (Array.isArray(tip.links) && tip.links.length > 0) {
        const categories = {};
        const uncategorized = [];
        
        tip.links.forEach(l => {
          if (l.category && l.category.trim() !== '') {
            if (!categories[l.category]) categories[l.category] = [];
            categories[l.category].push(l);
          } else {
            uncategorized.push(l);
          }
        });

        // 渲染有分類的鏈結
        for (const [cat, links] of Object.entries(categories)) {
          const firstIcon = links[0].category_icon;
          const iconHtml = firstIcon ? `<span class="material-symbols-outlined" style="vertical-align: middle; font-size: 1.1rem; margin-right: 4px; margin-bottom: 2px;">${firstIcon}</span>` : '';
          html += `<div style="font-size: 0.85rem; color: var(--text-color); opacity: 0.7; margin: 10px 0 4px 0; font-weight: 600; display: flex; align-items: center;">${iconHtml}${cat}</div>`;
          // 所有有分類的連結都排在同一行，並用逗號分隔
          const catLinksHtml = links.map(l => {
            const label = l.label || l.url;
            return `<a href="${l.url}" target="_blank" class="tip-item-link" style="margin-left: 4px;">${label}</a>`;
          }).join('<span style="color: var(--text-color); margin: 0 4px;">,</span>');
          html += `<div style="margin-top: 4px; line-height: 1.8;">${catLinksHtml}</div>`;
        }

        // 渲染未分類的鏈結
        if (uncategorized.length > 0) {
          // 如果有其他分類，就給未分類加個標題，否則直接顯示
          if (Object.keys(categories).length > 0) {
            html += `<div style="font-size: 0.85rem; color: var(--text-color); opacity: 0.7; margin: 10px 0 4px 0; font-weight: 600;">🔗 其他 / Other</div>`;
          }
          html += `<div style="display: flex; flex-direction: column; gap: 6px; margin-top: 4px;">`;
          uncategorized.forEach(l => {
            const label = l.label || l.url;
            const margin = Object.keys(categories).length > 0 ? 'margin-left: 4px;' : '';
            html += `<a href="${l.url}" target="_blank" class="tip-item-link" style="${margin}">🔗 ${label}</a>`;
          });
          html += `</div>`;
        }
      }

      html += `</div>`;
    });

    tipsContainer.innerHTML = html;
  } catch (err) {
    console.error('Failed to render tips:', err);
  }
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
    await renderTips();
  }

  if (document.getElementById('reminderBtn') || document.getElementById('profileDash')) {
    await renderReminders();
  }
});