/**
 * users/static/users/js/users.js
 * 使用者管理模塊前端邏輯
 * 所有 fetch() 呼叫對應 users/api_urls.py 中的 API 路由
 */

'use strict';

/* ════════════════════════════════════════
   0. 工具函式
════════════════════════════════════════ */

/** 取得 Django CSRF Token（由 Cookie 讀取） */
function getCookie(name) {
  for (const cookie of document.cookie.split(';')) {
    const c = cookie.trim();
    if (c.startsWith(name + '=')) return decodeURIComponent(c.slice(name.length + 1));
  }
  return null;
}

const REGION_COUNTRY_MAP = {
  'East Asia': [
    { value: 'Japan', label: '🇯🇵 日本' },
    { value: 'Korea', label: '🇰🇷 韓國' },
    { value: 'Macau', label: '🇲🇴 澳門' },
    { value: 'Hong Kong', label: '🇭🇰 香港' },
  ],
  'Southeast Asia': [
    { value: 'Indonesia', label: '🇮🇩 印尼' },
    { value: 'Malaysia', label: '🇲🇾 馬來西亞' },
    { value: 'Vietnam', label: '🇻🇳 越南' },
    { value: 'Thailand', label: '🇹🇭 泰國' },
    { value: 'Philippines', label: '🇵🇭 菲律賓' },
    { value: 'Cambodia', label: '🇰🇭 柬埔寨' },
    { value: 'Myanmar', label: '🇲🇲 緬甸' },
    { value: 'Singapore', label: '🇸🇬 新加坡' },
  ],
  'South Asia': [
    { value: 'India', label: '🇮🇳 印度' },
    { value: 'Pakistan', label: '🇵🇰 巴基斯坦' },
    { value: 'Bangladesh', label: '🇧🇩 孟加拉' },
  ],
  'Middle East': [
    { value: 'Saudi Arabia', label: '🇸🇦 沙烏地阿拉伯' },
    { value: 'UAE', label: '🇦🇪 阿拉伯聯合大公國' },
    { value: 'Turkey', label: '🇹🇷 土耳其' },
  ],
  'Europe': [
    { value: 'UK', label: '🇬🇧 英國' },
    { value: 'France', label: '🇫🇷 法國' },
    { value: 'Germany', label: '🇩🇪 德國' },
    { value: 'Italy', label: '🇮🇹 義大利' },
    { value: 'Spain', label: '🇪🇸 西班牙' },
  ],
  'North America': [
    { value: 'USA', label: '🇺🇸 美國' },
    { value: 'Canada', label: '🇨🇦 加拿大' },
  ],
  'Latin America': [
    { value: 'Brazil', label: '🇧🇷 巴西' },
    { value: 'Mexico', label: '🇲🇽 墨西哥' },
    { value: 'Argentina', label: '🇦🇷 阿根廷' },
  ],
  'Africa': [
    { value: 'South Africa', label: '🇿🇦 南非' },
    { value: 'Egypt', label: '🇪🇬 埃及' },
    { value: 'Nigeria', label: '🇳🇬 奈及利亞' },
  ],
  'Oceania': [
    { value: 'Australia', label: '🇦🇺 澳洲' },
    { value: 'New Zealand', label: '🇳🇿 紐西蘭' },
  ],
};

window.handleRegionChange = function(regionId = 'setupRegion', nationalityId = 'setupNationality') {
  console.log("handleRegionChange 有執行");
  const regionSelect = document.getElementById(regionId);
  const natSelect = document.getElementById(nationalityId);
  if (!regionSelect || !natSelect) return;

  const region = regionSelect.value;
  const currentVal = natSelect.getAttribute('data-selected') || natSelect.value;
  
  natSelect.innerHTML = '<option value="">請選擇國籍</option>';
  
  if (region && REGION_COUNTRY_MAP[region]) {
    REGION_COUNTRY_MAP[region].forEach(c => {
      const opt = document.createElement('option');
      opt.value = c.value;
      opt.textContent = c.label;
      if (c.value === currentVal) opt.selected = true;
      natSelect.appendChild(opt);
    });
    
    const otherOpt = document.createElement('option');
    otherOpt.value = 'Other';
    otherOpt.textContent = '🌍 其他';
    if ('Other' === currentVal) otherOpt.selected = true;
    natSelect.appendChild(otherOpt);
  }
};

document.addEventListener('DOMContentLoaded', () => {
  const editRegion = document.getElementById('editRegion');
  if (editRegion) {
    handleRegionChange('editRegion', 'editNationality');
  }
});

/** 統一 fetch 封裝（自動帶 CSRF Token 與 JSON headers）*/
async function apiFetch(url, method = 'GET', body = null) {
  const opts = {
    method,
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken'),
    },
    credentials: 'same-origin',
  };
  // Token Auth（前後端分離模式）
  const token = localStorage.getItem('authToken');
  if (token) opts.headers['Authorization'] = `Token ${token}`;
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(url, opts);
  const data = await res.json();
  return { ok: res.ok, status: res.status, data };
}

/** 顯示 Toast 通知 */
function showToast(msg, type = 'info', duration = 3500) {
  const icons = { success: '✅', error: '❌', info: 'ℹ️' };
  const container = document.getElementById('toastContainer');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${icons[type]}</span><span>${msg}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.transition = 'opacity .3s';
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

/** 顯示欄位錯誤訊息 */
function showError(id, msg) {
  const el = document.getElementById(id);
  if (el) { el.textContent = msg; el.classList.remove('hidden'); }
}

/** 清除欄位錯誤訊息 */
function clearErrors(ids) {
  ids.forEach(id => {
    const el = document.getElementById(id);
    if (el) { el.textContent = ''; el.classList.add('hidden'); }
  });
}

/** 設定按鈕 Loading 狀態 */
const _btnOrigText = {};
function setLoading(btnId, loading) {
  const btn = document.getElementById(btnId);
  if (!btn) return;
  if (loading) {
    _btnOrigText[btnId] = btn.innerHTML;
    btn.innerHTML = `<span class="spinner"></span>處理中…`;
    btn.disabled = true;
  } else {
    btn.innerHTML = _btnOrigText[btnId] || btn.innerHTML;
    btn.disabled = false;
  }
}

/** 顯示 / 隱藏密碼 */
function togglePw(inputId, btn) {
  const input = document.getElementById(inputId);
  if (!input) return;
  if (input.type === 'password') { input.type = 'text'; btn.textContent = '🙈'; }
  else { input.type = 'password'; btn.textContent = '👁'; }
}

/* ════════════════════════════════════════
   1. 頁面切換
════════════════════════════════════════ */
const ALL_PAGES = ['loginPage', 'profileSetupPage', 'profileDash', 'editProfilePage', 'forgotPage'];

function showPage(id) {
  ALL_PAGES.forEach(p => {
    const el = document.getElementById(p);
    if (el) el.classList.add('hidden');
  });
  const target = document.getElementById(id);
  if (target) target.classList.remove('hidden');
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

/** Auth Tab 切換（登入 ↔ 註冊）*/
function switchAuth(type) {
  const signInPanel = document.getElementById('signInPanel');
  const registerPanel = document.getElementById('registerPanel');
  if (!signInPanel) return;

  const isSignin = type === 'signin';
  signInPanel.classList.toggle('hidden', !isSignin);
  registerPanel.classList.toggle('hidden', isSignin);

  // 兩套 tab 都同步更新 active 狀態
  ['tabSignIn', 'tabSignIn2'].forEach(id => {
    document.getElementById(id)?.classList.toggle('active', isSignin);
  });
  ['tabRegister', 'tabReg2'].forEach(id => {
    document.getElementById(id)?.classList.toggle('active', !isSignin);
  });
}

/* ════════════════════════════════════════
   2. Confirm Modal
════════════════════════════════════════ */
function confirmAction(_type, title, msg, cbName) {
  document.getElementById('modalTitle').textContent = title;
  document.getElementById('modalMsg').textContent = msg;
  document.getElementById('confirmModal').classList.remove('hidden');
  document.getElementById('modalConfirmBtn').onclick = () => {
    closeModal();
    if (typeof window[cbName] === 'function') window[cbName]();
  };
}
function closeModal() {
  const modal = document.getElementById('confirmModal');
  if (modal) modal.classList.add('hidden');
}

/* ════════════════════════════════════════
   3. 密碼強度檢查
════════════════════════════════════════ */
function checkPwStrength(pw, fillId = 'pwFill', hintId = 'pwHint') {
  let score = 0;
  if (pw.length >= 8) score++;
  if (/[A-Z]/.test(pw)) score++;
  if (/[a-z]/.test(pw)) score++;
  if (/\d/.test(pw)) score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;
  const configs = [
    { w: '0%', c: '#e0e0e0', t: '請輸入密碼' },
    { w: '20%', c: '#db6b47', t: '非常弱' },
    { w: '40%', c: '#e7be67', t: '弱' },
    { w: '60%', c: '#a3c940', t: '中等' },
    { w: '80%', c: '#2ea85e', t: '強' },
    { w: '100%', c: '#1b7a42', t: '非常強 ✓' },
  ];
  const cfg = configs[Math.min(score, 5)];
  const fill = document.getElementById(fillId);
  const hint = document.getElementById(hintId);
  if (fill) { fill.style.width = cfg.w; fill.style.background = cfg.c; }
  if (hint) { hint.textContent = cfg.t; hint.style.color = cfg.c; }
}

/* ════════════════════════════════════════
   4. 登入
   POST /api/users/login/
   Activity Diagram: 進入系統 → 是否已有帳號 → 登入
════════════════════════════════════════ */
async function handleLogin(e) {
  e.preventDefault();
  clearErrors(['loginEmailErr', 'loginPwErr', 'loginGlobalErr']);

  const email = document.getElementById('loginEmail').value.trim();
  const pw = document.getElementById('loginPw').value;

  if (!email) { showError('loginEmailErr', '請輸入電子郵件'); return; }
  if (!pw) { showError('loginPwErr', '請輸入密碼'); return; }

  setLoading('loginSubmitBtn', true);

  const { ok, data } = await apiFetch('/api/users/login/', 'POST', { email, password: pw });

  setLoading('loginSubmitBtn', false);

  if (!ok) {
    const msg = data?.errors
      ? Object.values(data.errors).flat().join('、')
      : (data?.message || '登入失敗，請確認帳號與密碼');
    showError('loginGlobalErr', msg);
    return;
  }

  localStorage.setItem('authToken', data.data.token);
  // 快取 user 資料，讓下一頁 initApp() 跳過重複的 /api/users/me/ 請求
  sessionStorage.setItem('_userCache', JSON.stringify({ d: data.data, ts: Date.now() }));

  showToast(`歡迎回來，${data.data.user.name}！`, 'success');

  window.location.href = data.data.has_profile ? '/dashboard/' : '/profile/setup/';
}

/* ════════════════════════════════════════
   5. 註冊
   POST /api/users/register/
   Activity Diagram: 否有帳號 → 註冊帳號 → 填寫基本資料
════════════════════════════════════════ */
async function handleRegister(e) {
  e.preventDefault();
  clearErrors(['regNameErr', 'regEmailErr', 'regPwErr', 'regPw2Err', 'regGlobalErr']);

  const name = document.getElementById('regName').value.trim();
  const email = document.getElementById('regEmail').value.trim();
  const pw = document.getElementById('regPw').value;
  const pw2 = document.getElementById('regPw2').value;
  let ok = true;

  if (!name) { showError('regNameErr', '請輸入姓名'); ok = false; }
  if (!email) { showError('regEmailErr', '請輸入電子郵件'); ok = false; }
  if (pw.length < 8) { showError('regPwErr', '密碼至少 8 字元'); ok = false; }
  if (pw !== pw2) { showError('regPw2Err', '兩次密碼輸入不一致'); ok = false; }
  if (!document.getElementById('agreeTerms')?.checked) {
    showError('regGlobalErr', '請同意服務條款與隱私政策'); ok = false;
  }
  if (!ok) return;

  setLoading('regSubmitBtn', true);

  const { ok: apiOk, data } = await apiFetch('/api/users/register/', 'POST',
    { name, email, password: pw, password2: pw2 });

  setLoading('regSubmitBtn', false);

  if (!apiOk) {
    const msg = data?.errors
      ? Object.values(data.errors).flat().join('、')
      : (data?.message || '註冊失敗，請稍後再試');
    showError('regGlobalErr', msg);
    return;
  }

  localStorage.setItem('authToken', data.token);
  localStorage.setItem('pendingVerifyEmail', email);
  showToast('帳號建立成功！驗證信已寄出，請至信箱完成驗證', 'success');
  showVerifyEmailPanel(email);
}

/** 顯示 Email 驗證等待面板 */
function showVerifyEmailPanel(email) {
  document.getElementById('signInPanel')?.classList.add('hidden');
  document.getElementById('registerPanel')?.classList.add('hidden');
  const emailEl = document.getElementById('verifyEmailDisplay');
  if (emailEl) emailEl.textContent = email;
  document.getElementById('verifyEmailPanel')?.classList.remove('hidden');
}

/** 返回登入（從驗證等待面板） */
function backToLogin() {
  localStorage.removeItem('pendingVerifyEmail');
  localStorage.removeItem('authToken');
  document.getElementById('verifyEmailPanel')?.classList.add('hidden');
  switchAuth('signin');
}

/* ── 問答系統狀態 ── */
let _quizFormData = null;          // 暫存原表單資料
let _quizAnswers  = {};            // 問答結果
let _quizStep     = 0;             // 當前題目 index
let _quizSequence = [];            // 實際要顯示的題目 ID 序列
let _quizTransitioning = false;

/**
 * Step 1: 驗證原有表單，進入問答模式
 */
function startProfileQuiz(e) {
  console.log("startProfileQuiz 有執行");
  e.preventDefault();
  clearErrors(['nationalityErr', 'universityErr', 'identityErr', 'statusErr', 'arrivalErr']);

  const region = document.getElementById('setupRegion').value;
  const nationality = document.getElementById('setupNationality').value;
  const university  = document.getElementById('setupUniversity').value.trim();
  const identity    = document.getElementById('setupIdentity').value;
  const status      = document.getElementById('admissionStatusVal').value;
  const arrival     = document.getElementById('setupArrival')?.value || '';

  let ok = true;
  if (!region) { showError('regionErr', '請選擇地區'); ok = false; }
  if (!nationality) { showError('nationalityErr', '請選擇國籍'); ok = false; }
  if (!university)  { showError('universityErr', '請選擇就讀學校'); ok = false; }
  if (!identity)    { showError('identityErr', '請選擇身份別'); ok = false; }
  if (!status)      { showError('statusErr', '請選擇入學狀態'); ok = false; }
  if (!arrival)     { showError('arrivalErr', '請填寫預計抵台日期'); ok = false; }
  if (!ok) {
    const firstErr = document.querySelector('.field-error:not(.hidden)');
    if (firstErr) firstErr.scrollIntoView({ behavior: 'smooth', block: 'center' });
    return;
  }

  // 暫存表單資料
  _quizFormData = {
    region,
    nationality,
    university,
    identity_type: identity,
    admission_status: status,
    department: document.getElementById('setupDept')?.value || '',
    expected_arrival: arrival,
  };

  _quizSequence = ['quizQ1', 'quizQ2'];

  _quizStep = 0;
  _quizAnswers = {};

  // 設定進度指示器
  _buildQuizProgress(_quizSequence.length);

  // 啟動 overlay
  const overlay = document.getElementById('quizOverlay');
  overlay.classList.add('active');
  document.body.style.overflow = 'hidden';

  // Fade in 第一題
  setTimeout(() => {
    const firstCard = document.getElementById(_quizSequence[0]);
    firstCard.classList.add('visible');
    _updateQuizDots(0);
  }, 200);
}

/**
 * 動態建構進度 dots（2 或 3 題）
 */
function _buildQuizProgress(total) {
  const container = document.getElementById('quizProgress');
  container.innerHTML = '';
  for (let i = 0; i < total; i++) {
    const dot = document.createElement('div');
    dot.className = 'quiz-dot' + (i === 0 ? ' active' : '');
    dot.dataset.dot = i;
    container.appendChild(dot);
    if (i < total - 1) {
      const line = document.createElement('div');
      line.className = 'quiz-line';
      line.dataset.line = i;
      container.appendChild(line);
    }
  }
}

/**
 * 更新進度 dots
 */
function _updateQuizDots(activeIndex) {
  const dots  = document.querySelectorAll('#quizProgress .quiz-dot');
  const lines = document.querySelectorAll('#quizProgress .quiz-line');
  dots.forEach((dot, i) => {
    dot.classList.remove('active', 'done');
    if (i < activeIndex) dot.classList.add('done');
    else if (i === activeIndex) dot.classList.add('active');
  });
  lines.forEach((line, i) => {
    line.classList.toggle('done', i < activeIndex);
  });
}

/**
 * Step 2: 記錄答案並前進到下一題
 */
function answerQuiz(field, value) {
  if (_quizTransitioning) return;
  _quizTransitioning = true;

  _quizAnswers[field] = value;

  const currentCard = document.getElementById(_quizSequence[_quizStep]);
  const nextStep    = _quizStep + 1;

  // Fade out 當前卡片
  currentCard.classList.remove('visible');
  currentCard.classList.add('exit');

  setTimeout(() => {
    currentCard.classList.remove('exit');

    if (nextStep >= _quizSequence.length) {
      // 已回答完所有題目 → 提交資料
      _updateQuizDots(nextStep);
      submitProfileWithQuiz();
      return;
    }

    // Fade in 下一題
    _quizStep = nextStep;
    _updateQuizDots(nextStep);
    const nextCard = document.getElementById(_quizSequence[nextStep]);
    setTimeout(() => {
      nextCard.classList.add('visible');
      _quizTransitioning = false;
    }, 80);
  }, 380);
}

/**
 * Step 3: 合併表單 + 問答資料，提交至 API
 */
async function submitProfileWithQuiz() {
  console.log("submitProfileWithQuiz 有執行");
  const body = {
    ..._quizFormData,
    has_taiwan_id: _quizAnswers.has_taiwan_id ?? null,
    is_deferred:   _quizAnswers.is_deferred ?? null,
  };

  const closeOverlay = () => {
    const overlay = document.getElementById('quizOverlay');
    if (overlay) overlay.classList.remove('active');
    document.body.style.overflow = '';
    _quizTransitioning = false;
  };

  let apiOk, data;
  try {
    ({ ok: apiOk, data } = await apiFetch('/api/users/profile/', 'POST', body));
  } catch (err) {
    closeOverlay();
    showToast('網路錯誤，請確認連線後再試', 'error');
    return;
  }

  if (!apiOk) {
    closeOverlay();
    const msg = (data?.errors && Object.keys(data.errors).length > 0)
      ? Object.values(data.errors).flat().join('、')
      : (data?.message || '儲存失敗，請稍後再試');
    showToast(msg, 'error');
    return;
  }

  showToast('資料已儲存！個人化流程已生成 🎉', 'success');
  setTimeout(() => { window.location.href = '/dashboard/'; }, 800);
}


/* ════════════════════════════════════════
   7. 更新基本資料
   PATCH /api/users/profile/update/
════════════════════════════════════════ */
async function handleEditBasic(e) {
  e.preventDefault();
  setLoading('editBasicBtn', true);

  const body = {
    name: document.getElementById('editName').value.trim(),
    region: document.getElementById('editRegion').value,
    nationality: document.getElementById('editNationality').value,
    department: document.getElementById('editDept').value.trim(),
    identity_type: document.getElementById('editIdentity').value,
    admission_status: document.getElementById('editAdmissionStatus').value,
    expected_arrival: document.getElementById('editArrival').value || null,
  };

  const { ok, data } = await apiFetch('/api/users/profile/update/', 'PATCH', body);

  setLoading('editBasicBtn', false);

  if (!ok) {
    showToast(data?.message || '更新失敗', 'error');
    return;
  }

  showToast('個人資料已更新', 'success');
  setTimeout(() => { window.location.href = '/dashboard/'; }, 800);
}

/* ════════════════════════════════════════
   8. 修改密碼
   POST /api/users/change-password/
════════════════════════════════════════ */
async function handleChangePw(e) {
  e.preventDefault();
  clearErrors(['oldPwErr', 'newPw1Err', 'newPw2Err']);

  const old = document.getElementById('oldPw').value;
  const n1 = document.getElementById('newPw1').value;
  const n2 = document.getElementById('newPw2').value;

  if (!old) { showError('oldPwErr', '請輸入目前密碼'); return; }
  if (n1.length < 8) { showError('newPw1Err', '新密碼至少 8 字元'); return; }
  if (n1 !== n2) { showError('newPw2Err', '兩次新密碼不一致'); return; }

  setLoading('changePwBtn', true);

  const { ok, data } = await apiFetch('/api/users/change-password/', 'POST',
    { old_password: old, new_password1: n1, new_password2: n2 });

  setLoading('changePwBtn', false);

  if (!ok) {
    const hasErrors = data?.errors && Object.keys(data.errors).length > 0;
    const msg = hasErrors ? Object.values(data.errors).flat().join('、') : data?.message;
    showToast(msg || '修改失敗', 'error');
    return;
  }

  // 更新 Token
  if (data.data?.token) localStorage.setItem('authToken', data.data.token);
  showToast('密碼已更新，請重新登入', 'success');
  document.getElementById('changePwForm')?.reset();
  setTimeout(handleLogout, 2000);
}

/* ════════════════════════════════════════
   9. 忘記密碼
   POST /api/users/password-reset/
════════════════════════════════════════ */
async function handleForgot(e) {
  e.preventDefault();
  clearErrors(['forgotEmailErr']);

  const email = document.getElementById('forgotEmail').value.trim();
  if (!email) { showError('forgotEmailErr', '請輸入電子郵件'); return; }

  setLoading('forgotBtn', true);

  await apiFetch('/api/users/password-reset/', 'POST', { email });

  setLoading('forgotBtn', false);

  // 無論帳號是否存在，都顯示成功（防止帳號枚舉攻擊）
  document.getElementById('forgotEmailSent').textContent = email;
  document.getElementById('forgotStep1').classList.add('hidden');
  document.getElementById('forgotStep2').classList.remove('hidden');
}

/* ════════════════════════════════════════
   10. 登出
   POST /api/users/logout/
════════════════════════════════════════ */
async function handleLogout() {
  localStorage.removeItem('authToken');
  window.location.href = '/logout/';
}

/* ════════════════════════════════════════
   11. 刪除帳號
   DELETE /api/users/delete/
════════════════════════════════════════ */
async function deleteAccount() {
  const { ok, data } = await apiFetch('/api/users/delete/', 'DELETE');
  if (ok) {
    localStorage.removeItem('authToken');
    showToast('帳號已停用，感謝您使用 StudyGo Taiwan', 'info', 2000);
    setTimeout(() => { window.location.href = '/login/?deleted=1'; }, 2000);
  } else {
    showToast(data?.message || '刪除失敗', 'error');
  }
}

/* ════════════════════════════════════════
   12. 重新寄送驗證信
   POST /api/users/resend-verification/
════════════════════════════════════════ */
async function resendVerification() {
  const { ok, data } = await apiFetch('/api/users/resend-verification/', 'POST');
  showToast(data?.message || (ok ? '驗證信已寄出' : '寄送失敗'), ok ? 'success' : 'error');
}

/* ════════════════════════════════════════
   13. 填充儀表板資料（從 API 回應）
════════════════════════════════════════ */
const IDENTITY_LABELS = {
  overseas_chinese: '僑生', foreign_student: '外籍生',
  exchange: '交換生', preparatory: '先修生',
};
const STATUS_LABELS = {
  applied: '已申請', admitted: '已錄取',
  pre_arrival: '入境前準備', arrived: '已抵臺就學',
};

function populateDashboard(user, profile) {
  if (!user) return;
  const initials = (user.name || '?').charAt(0).toUpperCase();

  const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };

  set('dashGreeting', `你好，${user.name} 👋`);
  set('dashSubtitle', `${IDENTITY_LABELS[profile?.identity_type] || '境外生'}，歡迎使用 StudyGo Taiwan。`);
  set('dashAvatar', initials);
  set('dashName', user.name);
  set('dashEmail', user.email);
  set('dashNatTag', `🌏 ${profile?.nationality || '—'}`);
  set('dashIdentTag', IDENTITY_LABELS[profile?.identity_type] || '—');
  set('dashUnivTag', profile?.university || '—');
  set('dashDept', profile?.department || '—');
  set('dashArrival', profile?.expected_arrival || '—');
  set('dashCreated', (profile?.created_at || user.date_joined || '').slice(0, 10));
  set('dashStatus', STATUS_LABELS[profile?.admission_status] || '—');
  set('dashStatusSub', profile?.admission_status === 'arrived' ? '已抵臺就讀中' : '準備中');

  // 預填編輯表單
  const editFields = {
    editName: user.name,
    editEmailDisp: user.email,
    editNationality: profile?.nationality,
    editIdentity: profile?.identity_type,
    editUniversity: profile?.university,
    editDept: profile?.department,
    editStatus: profile?.admission_status,
    editArrival: profile?.expected_arrival || '',
  };
  for (const [id, val] of Object.entries(editFields)) {
    const el = document.getElementById(id);
    if (el && val !== undefined) el.value = val;
  }

  const lastLoginEl = document.getElementById('lastLogin');
  if (lastLoginEl) lastLoginEl.textContent = new Date().toLocaleString('zh-TW');

}

/* ════════════════════════════════════════
   14. 更新 NavBar 登入狀態
════════════════════════════════════════ */
function updateNavAuth(user) {
  const navAuth = document.getElementById('navAuth');
  const navGuest = document.getElementById('navGuest');
  const navGreeting = document.getElementById('navGreeting');
  if (navAuth) navAuth.classList.remove('hidden');
  if (navGuest) navGuest.style.display = 'none';
  if (navGreeting && user) navGreeting.textContent = `${user.name} 同學`;
}

/* ════════════════════════════════════════
   15. 入學狀態卡片選取
════════════════════════════════════════ */
function selectStatus(card) {
  document.querySelectorAll('.status-card').forEach(c => c.classList.remove('active'));
  card.classList.add('active');
  const hidden = document.getElementById('admissionStatusVal');
  if (hidden) hidden.value = card.dataset.val;
  updatePreview();
}

/* ════════════════════════════════════════
   16. 資料預覽即時更新（Profile Setup）
════════════════════════════════════════ */
function updatePreview() {
  const g = id => document.getElementById(id);
  const set = (id, val) => { const el = g(id); if (el) el.textContent = val; };

  const user = window._tempUser;
  if (user?.name) {
    set('prevAvatar', user.name.charAt(0).toUpperCase());
    set('prevName', user.name);
    set('prevEmail', user.email);
  }
  set('prevNationality', g('setupNationality')?.value || '國籍未選');
  set('prevIdentity', IDENTITY_LABELS[g('setupIdentity')?.value] || '身份別未選');
  set('prevStatus', STATUS_LABELS[g('admissionStatusVal')?.value] || '狀態未選');
  const univSel = g('setupUniversity');
  const univLabel = univSel?.options[univSel.selectedIndex]?.text || univSel?.value || '—';
  set('prevUniv', univLabel !== '請選擇就讀學校' ? univLabel : '—');
  set('prevDept', g('setupDept')?.value || '—');
  set('prevArrival', g('setupArrival')?.value || '—');
}

function _prefillSetupPreview(user) {
  window._tempUser = user;
  const set = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
  set('prevAvatar', (user.name || '?').charAt(0).toUpperCase());
  set('prevName', user.name || '—');
  set('prevEmail', user.email || '—');
}

/* ════════════════════════════════════════
   17. Edit Tab 切換
════════════════════════════════════════ */
function switchEditTab(tab, btn) {
  ['editBasic', 'editPassword', 'editAccount'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.classList.add('hidden');
  });
  const target = document.getElementById('edit' + tab.charAt(0).toUpperCase() + tab.slice(1));
  if (target) target.classList.remove('hidden');
  document.querySelectorAll('.edit-tab').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
}

/* ════════════════════════════════════════
   18. Task Toggle（儀表板任務）
   PATCH /api/tasks/<id>/status/（模塊二接口）
════════════════════════════════════════ */
function toggleTask(btn) {
  const task = btn.closest('.check-task');
  const isDone = !task.classList.contains('done');
  task.classList.toggle('done', isDone);
  btn.textContent = isDone ? '✓' : '';
  const status = task.querySelector('.task-status');
  if (status) status.textContent = isDone ? '已完成' : '待完成';

  /*
  const taskId = task.dataset.taskId;
  if (taskId) {
    apiFetch(`/api/tasks/${taskId}/status/`, 'PATCH',
      { status: isDone ? 'completed' : 'pending' });
  }
  */
}

/* ════════════════════════════════════════
   19. Login Slide 輪播（滑動效果）
════════════════════════════════════════ */
let currentLoginSlide = 0;
let loginSlideTimer = null;
let _loginTransitioning = false;

function showLoginSlide(index) {
  const slides = document.querySelectorAll('.login-slide');
  const dots = document.querySelectorAll('.slide-dot');
  const total = slides.length;
  if (index === currentLoginSlide || _loginTransitioning) return;
  _loginTransitioning = true;

  const forward = ((index - currentLoginSlide + total) % total) < total / 2;
  const entering = slides[index];
  const leaving = slides[currentLoginSlide];

  // 1. 瞬間把「進入張」定位到畫面邊緣（不觸發 transition）
  entering.style.transition = 'none';
  entering.style.transform = `translateX(${forward ? '100%' : '-100%'})`;
  void entering.offsetWidth; // 強制 reflow，確認位置已套用

  // 2. 恢復 transition，同步動畫兩張投影片
  entering.style.transition = '';
  entering.style.transform = 'translateX(0)';
  entering.classList.add('active');          // CSS opacity 0 → 1

  leaving.style.transform = `translateX(${forward ? '-100%' : '100%'})`;
  leaving.style.opacity = '0';

  dots.forEach((dot, i) => dot.classList.toggle('active', i === index));
  currentLoginSlide = index;

  // 3. transition 結束後清理 inline styles
  setTimeout(() => {
    leaving.classList.remove('active');
    leaving.style.transform = '';
    leaving.style.opacity = '';
    entering.style.transform = '';
    entering.style.transition = '';
    _loginTransitioning = false;
  }, 520);
}

function startLoginSlider() {
  if (loginSlideTimer) clearInterval(loginSlideTimer);
  loginSlideTimer = setInterval(() => {
    const loginPage = document.getElementById('loginPage');
    if (loginPage && !loginPage.classList.contains('hidden')) {
      const totalSlides = document.querySelectorAll('.login-slide').length;
      if (totalSlides > 0) {
        showLoginSlide((currentLoginSlide + 1) % totalSlides);
      }
    }
  }, 3200);
}

/* ════════════════════════════════════════
   20. 頁面初始化：檢查是否已登入
════════════════════════════════════════ */
async function initApp() {
  // ── 公開首頁：不需登入 ──
  if (document.getElementById('homePage')) return;

  // ── Login 頁面 ──
  if (document.getElementById('loginPage')) {
    const params = new URLSearchParams(window.location.search);
    const verified = params.get('verified');
    const pendingEmail = localStorage.getItem('pendingVerifyEmail');

    // 啟動輪播與 Google 登入
    if (document.querySelectorAll('.login-slide').length > 0) {
      showLoginSlide(0);
      startLoginSlider();
    }
    initGoogleSignIn();

    // 處理驗證結果通知
    if (verified === '1') {
      localStorage.removeItem('pendingVerifyEmail');
      localStorage.removeItem('authToken');
      showToast('Email 驗證成功！請登入您的帳號', 'success');
    } else if (verified === 'fail') {
      showToast('驗證連結無效或已使用', 'error');
    } else if (verified === 'expired') {
      showToast('驗證連結已過期，請重新申請', 'error');
    }
    if (params.get('deleted') === '1') showToast('帳號已停用，感謝您使用 StudyGo Taiwan', 'info', 5000);
    if (params.get('need_verify') === '1') showToast('請先驗證電子信箱才能繼續', 'error');

    // 若有待驗證狀態（且非剛完成驗證），顯示驗證等待面板
    if (pendingEmail && verified !== '1') {
      showVerifyEmailPanel(pendingEmail);
      return;
    }

    // 一般登入頁：清除舊 token
    localStorage.removeItem('authToken');
    return;
  }

  // ── 公開頁面（忘記密碼、重設密碼）：不需要登入，直接結束 ──
  const publicPaths = ['/forgot-password/', '/reset-password/'];
  if (publicPaths.some(p => window.location.pathname.startsWith(p))) {
    return;
  }

  // ── 受保護頁面：優先使用登入時快取的 user 資料（30 秒內有效）──
  let userData;
  const _cache = sessionStorage.getItem('_userCache');
  if (_cache) {
    try {
      const parsed = JSON.parse(_cache);
      if (Date.now() - parsed.ts < 30000) {
        userData = parsed.d;
      }
    } catch (_) {}
    sessionStorage.removeItem('_userCache');
  }

  if (!userData) {
    const { ok, data } = await apiFetch('/api/users/me/');
    if (!ok) {
      localStorage.removeItem('authToken');
      window.location.href = '/login/';
      return;
    }
    userData = data.data;
  }
  localStorage.removeItem('pendingVerifyEmail');

  const user = userData;
  const profile = user.student_profile;

  updateNavAuth(user);

  // ── 依當前頁面 ID 決定要做什麼，不做跨頁跳轉 ──
  if (document.getElementById('profileDash')) {
    // Dashboard 頁
    populateDashboard(user, profile);
    showPage('profileDash');
  } else if (document.getElementById('profileSetupPage')) {
    // 個人資料設定頁
    _prefillSetupPreview(user);
    showPage('profileSetupPage');
  }
  // editProfilePage、forgotPage 等：Django 已渲染好，只需更新 navbar
}

/* ════════════════════════════════════════
   21. Google OAuth 登入
════════════════════════════════════════ */

/** Google Identity Services 初始化：輪詢直到 google 物件就緒 */
function initGoogleSignIn() {
  if (!window.GOOGLE_CLIENT_ID) return;
  if (typeof google === 'undefined' || !google.accounts) {
    setTimeout(initGoogleSignIn, 100);
    return;
  }
  google.accounts.id.initialize({
    client_id: window.GOOGLE_CLIENT_ID,
    callback: handleGoogleLogin,
    auto_select: false,
    cancel_on_tap_outside: true,
  });
  const container = document.getElementById('googleBtnContainer');
  if (container) {
    google.accounts.id.renderButton(container, {
      theme: 'outline',
      size: 'large',
      width: 300,
      text: 'signin_with',
      logo_alignment: 'center',
    });
  }
}

/** 收到 Google ID Token 後送往後端換取系統 Token */
async function handleGoogleLogin(response) {
  const credential = response.credential;
  if (!credential) {
    showToast('Google 登入失敗，未取得憑證', 'error');
    return;
  }

  const { ok, data } = await apiFetch('/api/users/google-login/', 'POST', { credential });

  if (!ok) {
    showToast(data?.message || 'Google 登入失敗', 'error');
    return;
  }

  localStorage.setItem('authToken', data.data.token);
  sessionStorage.setItem('_userCache', JSON.stringify({ d: data.data, ts: Date.now() }));
  const isNew = data.data.is_new_user;
  showToast(isNew ? `帳號已建立，歡迎 ${data.data.user.name}！` : `歡迎回來，${data.data.user.name}！`, 'success');

  window.location.href = data.data.has_profile ? '/dashboard/' : '/profile/setup/';
}

// 啟動
//document.addEventListener('DOMContentLoaded', initApp);
document.addEventListener('DOMContentLoaded', () => {
  initApp();

  const profileSetupForm = document.getElementById('profileSetupForm');

  if (profileSetupForm) {
    profileSetupForm.addEventListener('submit', function (e) {
      e.preventDefault();
      startProfileQuiz(e);
    });
  }

  const setupRegion = document.getElementById('setupRegion');

  if (setupRegion) {
    handleRegionChange('setupRegion', 'setupNationality');

    setupRegion.addEventListener('change', () => {
      handleRegionChange('setupRegion', 'setupNationality');
      updatePreview();
    });
  }
});