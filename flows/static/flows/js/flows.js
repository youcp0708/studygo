/**
 * flows/static/flows/js/flows.js
 * Flows 模塊前端邏輯
 */

'use strict';

/** 取得 i18n 字串（UI_STRINGS 由模板注入；不在任務頁時退回中文） */
function flowsT(key, fallback) {
  return (window.UI_STRINGS && window.UI_STRINGS[key]) || fallback;
}

/** 依網站目前語言（<html lang>）取得對應的 BCP-47 locale，供 toLocaleDateString 等使用 */
function getSiteLocale() {
  const lang = (document.documentElement.lang || 'zh-hant').toLowerCase();
  return lang === 'zh-hant' ? 'zh-TW' : lang;
}

/** HTML 跳脫：插入 innerHTML 的動態內容（使用者備註、通知訊息）一律先跳脫 */
function escapeFlowsHtml(text) {
  return String(text ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

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
      const percent = Math.round(Number(data.data.overall_percent || 0)); 

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
          // 截止日由後端依 deadline 設定計算（deadline_info.calculated_due_date，格式 YYYY/MM/DD）
          const dueStr = task.deadline_info && task.deadline_info.calculated_due_date;
          if (dueStr && task.status !== 'completed') {
            const due = new Date(dueStr);
            due.setHours(0, 0, 0, 0);

            // 今天以前或三天內到期都算「即將到期」
            if (!isNaN(due) && due <= threeDaysLater) {
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
              <div style="font-weight:700;font-size:14px;">${escapeFlowsHtml(task.localized ? task.localized.title : (task.task_detail ? task.task_detail.title : flowsT('unnamedTask', '未命名任務')))}</div>
              <div style="font-size:12px;color:var(--muted);">${escapeFlowsHtml(task.stage_name || flowsT('flowStage', '流程階段'))}</div>
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
      const loadErrorText = dashRecentTasks.getAttribute('data-load-error') || '任務載入失敗，請重新整理頁面。';
      dashRecentTasks.innerHTML = `
        <div style="text-align:center;padding:16px 0;color:var(--muted);">
          ${loadErrorText}
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
// 最近一次 renderMyTasks() 抓到的 stages 資料，供「帶領」逐步引導查詢任務歸屬與完成狀態，不用重打 API
let lastStagesData = null;
// 目前正在被「帶領」引導的 StudentTask id；null 代表沒有引導中
let taskGuideId = null;

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
      const progressText = sec.getAttribute('data-progress');
      const topProgress = document.getElementById('topProgressText');
      if (topProgress && progressText) {
        topProgress.textContent = progressText;
      }
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
    showToast(
      newStatus === 'completed'
        ? flowsT('taskCompletedToast', '任務已完成')
        : flowsT('taskUncompletedToast', '已取消完成'),
      'success'
    );
    renderMyTasks();
    renderDashboardProgress();
    renderReminders();

    // 「帶領」逐步引導：剛好完成的是目前正在被引導的那個任務時，結束引導並附上相關指南連結
    if (taskGuideId && taskId === taskGuideId && newStatus === 'completed') {
      const finishedId = taskGuideId;
      taskGuideId = null;
      window.endGuideHand();
      apiFetch(`/chatbot/api/task-guide/${finishedId}/`).then(({ ok: guideOk, data: guideData }) => {
        const guide = guideOk && guideData.data;
        const msg = guide
          ? flowsT('guideDoneWithLink', '任務已完成！想更了解細節可以看看：')
            + ` <a href="${guide.url}" target="_top">${guide.title}</a>`
          : flowsT('guideDone', '任務已完成！');
        showToast(msg, 'success', 8000);
      });
    }
  } else {
    showToast(flowsT('statusUpdateFailedToast', '狀態更新失敗'), 'error');
    checkbox.checked = !checkbox.checked; // revert
  }
};

/** 在 lastStagesData 裡找到指定 id 的任務與所屬 stage index，回傳 { task, stageIndex } 或 null */
function findTaskAndStageIndex(taskId) {
  if (!lastStagesData) return null;
  for (let sIdx = 0; sIdx < lastStagesData.length; sIdx++) {
    const task = (lastStagesData[sIdx].tasks || []).find(t => t.id === taskId);
    if (task) return { task, stageIndex: sIdx };
  }
  return null;
}

/** 由 AI 主動訊息的「帶領」連結觸發：切到正確分頁、指向該任務卡片 */
function startTaskGuideFor(taskId) {
  const found = findTaskAndStageIndex(taskId);
  if (!found || found.task.status === 'completed') {
    if (found) showToast(flowsT('guideTaskDone', '這項任務已經完成囉！'), 'success');
    return;
  }

  const sections = document.querySelectorAll('.stage-section:not(.skeleton)');
  if (sections[found.stageIndex] && !sections[found.stageIndex].classList.contains('active')) {
    switchFlowTab(found.stageIndex);
  }

  taskGuideId = taskId;
  const loc = found.task.localized || found.task.task_detail || {};
  const title = loc.title || '';
  const text = flowsT('guideTaskText', '完成「{title}」吧！').replace('{title}', title);
  window.pointGuideHand('task-' + taskId, text);
}


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
  if (ok) showToast(flowsT('noteSavedToast', '備註已儲存'), 'success');
};

async function renderMyTasks() {
  const container = document.getElementById('flowsContainer');
  if (!container) return;

  await renderProgressChart();

  const { ok, data } = await apiFetch('/api/flows/my-tasks/');

  if (!ok) {
    container.innerHTML = `<div style="text-align:center;color:red;">${flowsT('loadFailedText', '載入失敗，請確認已登入並填寫學生資料。')}</div>`;
    return;
  }

  const stages = data.data.stages || [];
  lastStagesData = stages;
  container.innerHTML = '';

  if (!stages || stages.length === 0) {
    container.innerHTML = `
      <div style="text-align:center;padding:48px;background:white;border-radius:14px;border:1px solid #e5e8e6;">
        <h3 style="margin-bottom:12px;">${flowsT('noTasksTitle', '尚未產生任務')}</h3>
        <p style="color:var(--muted);">${flowsT('noTasksHint', '請確保您已在「我的帳戶」中設定完學籍身分，並重新整理頁面。')}</p>
      </div>
    `;
    return;
  }

  if (currentActiveTabIndex >= stages.length) {
    currentActiveTabIndex = 0;
  }

  let tabsHtml = `<div class="flows-top-row"><div class="flows-tabs">`;
  let contentHtml = ``;
  let activeProgressText = '';

  stages.forEach((stage, index) => {
    const isActive = index === currentActiveTabIndex ? 'active' : '';
    tabsHtml += `<button class="flow-tab-btn ${isActive}" onclick="switchFlowTab(${index})">${escapeFlowsHtml(stage.stage_name)}</button>`;

    const tasks = stage.tasks || [];
    const total = tasks.length;
    const completed = tasks.filter(t => t.status === 'completed').length;
    const progressText = `${completed} / ${total} ${window.UI_STRINGS.completedProgress}`;
    if (isActive) {
      activeProgressText = progressText;
    }

    contentHtml += `
      <div class="stage-section ${isActive}" data-progress="${progressText}">
      <div class="task-list">
    `;

    tasks.forEach(task => {
      const isDone = task.status === 'completed';
      // ── 使用後端已本地化的文字欄位 ──
      const loc = task.localized || task.task_detail || {};
      const deadlineInfo = task.deadline_info || {};

      // ── 依截止日判斷卡片邊框顏色：已過期紅框，3 天內（含今天）到期橘框 ──
      // 跟 renderDashboardProgress() 判斷「即將到期」用的邏輯與門檻（3 天）一致
      let dueStatusClass = '';
      if (!isDone && deadlineInfo.calculated_due_date) {
        const due = new Date(deadlineInfo.calculated_due_date);
        due.setHours(0, 0, 0, 0);
        if (!isNaN(due)) {
          const today = new Date();
          today.setHours(0, 0, 0, 0);
          const threeDaysLater = new Date(today);
          threeDaysLater.setDate(today.getDate() + 3);

          if (due < today) {
            dueStatusClass = 'overdue';
          } else if (due <= threeDaysLater) {
            dueStatusClass = 'due-soon';
          }
        }
      }

      const reqDocs = loc.required_documents ? escapeFlowsHtml(loc.required_documents) : null;
      const applyLoc = loc.apply_location ? escapeFlowsHtml(loc.apply_location.trim()) : null;
      const applyAddr = loc.apply_address ? escapeFlowsHtml(loc.apply_address.trim()) : null;
      const officialUrl = loc.official_url
        ? `<a href="${escapeFlowsHtml(loc.official_url)}" target="_blank" style="color:var(--primary);text-decoration:underline;">${window.UI_STRINGS.visitOfficialWebsite}</a>`
        : null;
      const noteVal = escapeFlowsHtml(task.note || '');
      const reqLabel = window.UI_STRINGS?.requiredLabel || '必做';
      const optLabel = window.UI_STRINGS?.optionalLabel || '建議';
      const requiredBadge = task.task_detail?.is_required
        ? `<span class="task-badge required">${reqLabel}</span>`
        : `<span class="task-badge optional">${optLabel}</span>`;

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
      const applyMapUrl = loc.apply_map_url ? escapeFlowsHtml(loc.apply_map_url) : null;

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
        <div id="task-${task.id}" class="task-item ${isDone ? 'completed' : ''} ${dueStatusClass}">
          <div class="task-item-row" onclick="toggleTaskDetails(${task.id})">
            <input type="checkbox" id="chk-${task.id}" onclick="toggleTaskCompletion(${task.id}, event)" ${isDone ? 'checked' : ''}>
            <div class="task-content">
              <div class="task-title">
                ${loc.title ? escapeFlowsHtml(loc.title) : window.UI_STRINGS.unnamedTask}
                ${requiredBadge}
                ${loc.has_fallback ? `<span class="task-badge" style="background:#fef3c7;color:#d97706;border:1px solid #fcd34d;">${flowsT('untranslatedBadge', '未翻譯')}</span>` : ''}
              </div>
              <div class="task-desc" style="white-space: pre-wrap;">${loc.description ? escapeFlowsHtml(loc.description) : ''}</div>
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

  tabsHtml += `</div><div class="stage-progress" id="topProgressText" style="white-space: nowrap; font-weight: 700;">${activeProgressText}</div></div>`;
  container.innerHTML = tabsHtml + contentHtml;

  applyTaskHashDeepLink();
}

/**
 * 讀取網址的 #task-<id>，切到對應分頁、捲過去並高亮。
 * 由 renderMyTasks() 頁面載入時呼叫；小鈴鐺提醒在同一頁點擊跳轉時也直接呼叫這個函式
 * （同頁改網址 hash 不會自動觸發這段邏輯，需要手動呼叫一次）。
 */
function applyTaskHashDeepLink() {
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

window.toggleTipCategory = function (id) {
  const panel = document.getElementById(`tip-panel-${id}`);
  const arrow = document.getElementById(`tip-arrow-${id}`);

  if (!panel) return;

  const isOpen = panel.style.display === 'block';

  panel.style.display = isOpen ? 'none' : 'block';

  if (arrow) {
    arrow.textContent = isOpen ? 'expand_more' : 'expand_less';
  }
};

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

    let html = '';

    tips.forEach((tip, tipIndex) => {
      html += `
        <div class="tip-item">
          <div class="tip-item-title">
            ${escapeFlowsHtml(tip.title)}
            ${tip.has_fallback ? `<span class="task-badge" style="background:#fef3c7;color:#d97706;border:1px solid #fcd34d;">${flowsT('untranslatedBadge', '未翻譯')}</span>` : ''}
          </div>
          ${tip.content ? `<div class="tip-item-content">${escapeFlowsHtml(tip.content)}</div>` : ''}
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

        html += `<div class="tip-accordion-list">`;

        Object.entries(categories).forEach(([cat, links], catIndex) => {
          const panelId = `${tipIndex}-${catIndex}`;
          const firstIcon = links[0].category_icon;

          const iconHtml = firstIcon
            ? `<span class="material-symbols-outlined tip-category-icon">${escapeFlowsHtml(firstIcon)}</span>`
            : '';

          html += `
            <div class="tip-accordion-item">
              <button type="button" class="tip-category-btn" onclick="toggleTipCategory('${panelId}')">
                <span class="tip-category-left">
                  ${iconHtml}
                  <span>${escapeFlowsHtml(cat)}</span>
                </span>
                <span id="tip-arrow-${panelId}" class="material-symbols-outlined tip-category-arrow">expand_more</span>
              </button>

              <div id="tip-panel-${panelId}" class="tip-category-panel" style="display:none;">
                <div class="tip-link-list">
          `;

          links.forEach(l => {
            const label = escapeFlowsHtml(l.label || l.url);
            html += `<a href="${escapeFlowsHtml(l.url)}" target="_blank" class="tip-app-link">${label}</a>`;
          });

          html += `
                </div>
              </div>
            </div>
          `;
        });

        if (uncategorized.length > 0) {
          html += `<div class="tip-link-list tip-uncategorized-links">`;

          uncategorized.forEach(l => {
            const label = escapeFlowsHtml(l.label || l.url);
            html += `
              <a href="${escapeFlowsHtml(l.url)}" target="_blank" class="tip-app-link">${label}</a>`;
          });

          html += `</div>`;
        }

        html += `</div>`;
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
    // 延遲一拍再掛監聽，避免這次開啟下拉選單的點擊事件被自己立刻關掉
    setTimeout(() => {
      document.addEventListener('click', _closeReminderDropdownOutside);
    }, 0);
  } else {
    closeReminderDropdown();
  }
};

function closeReminderDropdown() {
  const dropdown = document.getElementById('reminderDropdown');
  if (dropdown) dropdown.style.display = 'none';
  document.removeEventListener('click', _closeReminderDropdownOutside);
}

function _closeReminderDropdownOutside(e) {
  const wrap = document.getElementById('tourNavReminder');
  if (wrap && !wrap.contains(e.target)) {
    closeReminderDropdown();
  }
}

/**
 * 顯示 FAB 紅點 + 「嗶嗶嗶，你有新消息！」話框，記住要開啟哪個聊天 session。
 * 到期提醒、AI 首次歡迎訊息都共用這套通知機制（回應格式都是 { has_new, session_id }）。
 */
function showProactiveChatDot(sessionId) {
  sessionStorage.setItem('chatWidgetPendingSession', String(sessionId));
  const fabDot = document.getElementById('chatFabDot');
  const fabBubble = document.getElementById('chatFabBubble');
  if (fabDot) fabDot.hidden = false;
  if (fabBubble) fabBubble.hidden = false;
}

async function renderReminders() {
  const { ok, data } = await apiFetch('/api/flows/reminders/');
  if (!ok) return;

  const count = data.data.unread_count || 0;
  const reminders = data.data.reminders || [];

  const badge = document.getElementById('reminderBadge');
  const dashCount = document.getElementById('dashUnreadCount');
  const list = document.getElementById('reminderList');
  const dropdown = document.getElementById('reminderDropdown');

  // 主動 AI 引導訊息：後端已包裝成一則 helper 對話裡的 assistant 訊息，
  // 這裡只負責記住「哪個 session 有新訊息」並點亮 FAB 紅點，
  // 實際訊息內容交給聊天小工具開啟時自己載入該 session 顯示。
  const proactiveChat = data.data.proactive_chat;
  if (proactiveChat && proactiveChat.has_new) {
    showProactiveChatDot(proactiveChat.session_id);
  }

  const noRemindersText = dropdown ? dropdown.getAttribute('data-no-reminders') : '沒有通知 🎉';

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

  // 已讀/未讀用不同顏色：未讀是淡底色+一般文字色，已讀是透明底+灰色文字，但兩者都留在畫面上
  reminders.forEach(r => {
    const hasLink = r.link_task_id !== null && r.link_task_id !== undefined;
    const clickable = hasLink || !r.is_read;
    const clickAttr = clickable
      ? `onclick="onReminderClick(${r.id}, ${r.is_read}, ${hasLink ? r.link_task_id : 'null'})"`
      : '';
    const bg = r.is_read ? 'transparent' : 'var(--primary-soft, #eef6f3)';
    const textColor = r.is_read ? 'var(--muted)' : 'var(--text)';
    list.innerHTML += `
      <div id="reminder-${r.id}" ${clickAttr} style="padding:12px 16px; border-bottom:1px solid var(--border, #eee); display:flex; flex-direction:column; gap:4px; font-size:14px; background:${bg}; ${clickable ? 'cursor:pointer;' : ''}">
        <div class="reminder-message" style="color:${textColor}; line-height:1.4;">${escapeFlowsHtml(r.message)}</div>
        <span style="font-size:12px; color:var(--muted);">${new Date(r.created_at).toLocaleDateString(getSiteLocale())}</span>
      </div>
    `;
  });
}

/** 點小鈴鐺的提醒卡片：標記已讀（保留在畫面上，只是變灰）＋ 如果有對應任務就跳轉過去 */
window.onReminderClick = async function (id, wasRead, studentTaskId) {
  if (!wasRead) {
    const { ok } = await apiFetch(`/api/flows/reminders/${id}/read/`, 'PATCH');
    if (ok) {
      const item = document.getElementById(`reminder-${id}`);
      if (item) {
        item.style.background = 'transparent';
        const msg = item.querySelector('.reminder-message');
        if (msg) msg.style.color = 'var(--muted)';
      }
      updateUnreadCount(-1);
    }
  }

  if (studentTaskId !== null && studentTaskId !== undefined) {
    goToReminderTask(studentTaskId);
  }
};

function updateUnreadCount(delta) {
  const badge = document.getElementById('reminderBadge');
  const dashCount = document.getElementById('dashUnreadCount');
  if (badge) {
    const next = Math.max(0, parseInt(badge.textContent || '0', 10) + delta);
    if (next > 0) {
      badge.textContent = next;
    } else {
      badge.style.display = 'none';
    }
  }
  if (dashCount) {
    dashCount.textContent = Math.max(0, parseInt(dashCount.textContent || '0', 10) + delta);
  }
}

/** 點小鈴鐺的提醒卡片：跳到「我的任務」頁面並定位到對應任務 */
window.goToReminderTask = function (studentTaskId) {
  const hash = `#task-${studentTaskId}`;
  if (window.location.pathname === '/flows/my-tasks/') {
    window.location.hash = hash;
    applyTaskHashDeepLink();
    closeReminderDropdown();
  } else {
    window.location.href = `/flows/my-tasks/${hash}`;
  }
};

/* ════════════════════════════════════════
   初始化
════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', async () => {
  const hasDashboardWidgets =
    document.getElementById('dashCompletionRate') ||
    document.getElementById('dashOverdueCount') ||
    document.getElementById('dashRecentTasks');

  const hasFlowsPage = document.getElementById('flowsContainer');

  // 首頁、Dashboard、任務頁都先確保任務已初始化
  if (hasDashboardWidgets || hasFlowsPage) {
    await initUserTasks();
  }

  // 只要頁面有完成率 / 提醒 / 近期待辦，就更新 Dashboard 資料
  if (hasDashboardWidgets) {
    await renderDashboardProgress();

    // 首次進 dashboard：AI 主動打招呼 + 帶到第一個任務（後端用 has_received_welcome_chat 冪等保護，
    // 每次進 dashboard 呼叫都安全，只有第一次會真的產生新訊息）
    const { ok: welcomeOk, data: welcomeData } = await apiFetch('/chatbot/api/welcome-message/', 'POST');
    if (welcomeOk && welcomeData.data && welcomeData.data.has_new) {
      showProactiveChatDot(welcomeData.data.session_id);
    }
  }

  if (hasFlowsPage) {
    await renderMyTasks();
    await renderTips();

    // 由 AI 主動訊息的「帶領」連結接續：跨頁帶著要引導的任務 id 過來
    const guideTaskId = sessionStorage.getItem('taskGuideTarget');
    if (guideTaskId) {
      sessionStorage.removeItem('taskGuideTarget');
      startTaskGuideFor(Number(guideTaskId));
    }
  }

  if (document.getElementById('reminderBtn') || hasDashboardWidgets) {
    await renderReminders();
    // 輕量輪詢：讓學生開著頁面時，也能在一分鐘內看到新的到期提醒與主動 AI 訊息紅點。
    // proactive_notified_at 是後端的冪等旗標，多個分頁同時輪詢也不會重複產生訊息。
    setInterval(renderReminders, 60000);
  }
});