/**
 * users/static/users/js/users.js
 * 使用者管理模塊前端邏輯
 * 所有 fetch() 呼叫對應 users/api_urls.py 中的 API 路由
 */

'use strict';

/* ════════════════════════════════════════
   0. 工具函式
════════════════════════════════════════ */

/** 依網站目前語言（<html lang>）取得對應的 BCP-47 locale，供 toLocaleString 等使用 */
function getSiteLocale() {
  const lang = (document.documentElement.lang || 'zh-hant').toLowerCase();
  return lang === 'zh-hant' ? 'zh-TW' : lang;
}

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
  
  natSelect.innerHTML = `<option value="">${window.I18N_PROFILE_SETUP?.selectNationality || '請選擇國籍'}</option>`;
  
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

// ── AI 小幫手懸浮按鈕：若上次是「最小化」離開（保留對話），點擊時回到原本畫面；
//    若上次是「關閉」或從未進入過，就導向全新的空白對話。
document.addEventListener('DOMContentLoaded', () => {
  const fab = document.querySelector('.chatbot-fab');
  if (!fab) return;

  fab.addEventListener('click', function (event) {
    const minimized = sessionStorage.getItem('chatbot_minimized') === '1';
    if (!minimized) return; // 保留原本的純網址，開新對話

    event.preventDefault();
    const mode = sessionStorage.getItem('chatbot_active_mode') || 'helper';
    const sessionId = sessionStorage.getItem(`chatbot_visit_session_${mode}`);
    const base = fab.getAttribute('href');
    const params = new URLSearchParams({ ai_mode: mode });
    if (sessionId) params.set('session', sessionId);
    window.location.href = `${base}?${params.toString()}`;
  });
});

/** 共用多語訊息（由 base.html 的 I18N_COMMON 注入；缺字典時退回中文） */
function tCommon(key, fallback) {
  return (window.I18N_COMMON && window.I18N_COMMON[key]) || fallback;
}

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

  localStorage.setItem('pendingVerifyEmail', email);
  showToast(tCommon('accountCreated', '帳號建立成功！驗證信已寄出，請至信箱完成驗證'), 'success');
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
  document.getElementById('verifyEmailPanel')?.classList.add('hidden');
  switchAuth('signin');
}

/* ── 問答系統狀態 ── */
let _quizFormData = null;          // 暫存原表單資料
let _quizAnswers  = {};            // 問答結果
let _quizStep     = 0;             // 當前題目 index
let _quizSequence = [];            // 實際要顯示的題目 ID 序列
let _quizTransitioning = false;
let _quizActive = false;           // 問答 overlay 是否正在開啟

const SETUP_DRAFT_KEY = 'profileSetupDraft';

/** 將目前的表單與問答進度存進 localStorage，避免重新整理或切換語言後資料消失 */
function saveSetupDraft() {
  const g = id => document.getElementById(id);
  if (!g('profileSetupForm')) {
    console.log('[draft] 找不到 profileSetupForm，跳過儲存');
    return;
  }
  const draft = {
    region: g('setupRegion')?.value || '',
    nationality: g('setupNationality')?.value || '',
    university: g('setupUniversity')?.value || '',
    department: g('setupDept')?.value || '',
    identity_type: g('setupIdentity')?.value || '',
    admission_status: g('admissionStatusVal')?.value || '',
    expected_arrival: g('setupArrival')?.value || '',
    quizActive: _quizActive,
    quizStep: _quizStep,
    quizAnswers: _quizAnswers,
  };
  localStorage.setItem(SETUP_DRAFT_KEY, JSON.stringify(draft));
  console.log('[draft] 已儲存', draft);
}

function clearSetupDraft() {
  localStorage.removeItem(SETUP_DRAFT_KEY);
}

/** 標示目前這題已選過的答案，並更新「下一題」按鈕的可用狀態 */
function _refreshQuizCardUI() {
  const cardId = _quizSequence[_quizStep];
  const card = document.getElementById(cardId);
  if (!card) return;

  const field = card.querySelector('.quiz-option')?.dataset.field;
  const answered = field !== undefined && _quizAnswers[field] !== undefined;

  card.querySelectorAll('.quiz-option').forEach(btn => {
    const matches = answered && String(_quizAnswers[field]) === btn.dataset.value;
    btn.classList.toggle('selected', matches);
  });

  const nextBtn = card.querySelector('.quiz-nav-btn[onclick="quizGoNext()"]');
  if (nextBtn) nextBtn.disabled = !answered;
}

/** 關閉問答 overlay，返回填寫個人資料畫面（已填的表單與已作答的題目都會保留） */
function returnToProfileForm() {
  const overlay = document.getElementById('quizOverlay');
  if (overlay) overlay.classList.remove('active');
  document.body.style.overflow = '';
  document.querySelectorAll('.quiz-card').forEach(c => c.classList.remove('visible', 'exit'));
  _quizActive = false;
  _quizTransitioning = false;
  saveSetupDraft();
}

/** 回到上一題（不會清除已作答的答案） */
function quizGoBack() {
  if (_quizTransitioning || _quizStep === 0) return;
  const currentCard = document.getElementById(_quizSequence[_quizStep]);
  currentCard.classList.remove('visible');
  _quizStep -= 1;
  _updateQuizDots(_quizStep);
  document.getElementById(_quizSequence[_quizStep]).classList.add('visible');
  _refreshQuizCardUI();
  saveSetupDraft();
}

/** 前進到下一題（僅在目前題目已作答時可用） */
function quizGoNext() {
  if (_quizTransitioning) return;
  const field = document.getElementById(_quizSequence[_quizStep])?.querySelector('.quiz-option')?.dataset.field;
  if (field === undefined || _quizAnswers[field] === undefined) return;
  if (_quizStep + 1 >= _quizSequence.length) return;

  const currentCard = document.getElementById(_quizSequence[_quizStep]);
  currentCard.classList.remove('visible');
  _quizStep += 1;
  _updateQuizDots(_quizStep);
  document.getElementById(_quizSequence[_quizStep]).classList.add('visible');
  _refreshQuizCardUI();
  saveSetupDraft();
}

/** 頁面載入時，若有暫存資料則還原表單欄位與問答進度 */
function restoreSetupDraft() {
  console.log('[draft] restoreSetupDraft 有執行');
  const raw = localStorage.getItem(SETUP_DRAFT_KEY);
  if (!raw) {
    console.log('[draft] localStorage 沒有暫存資料');
    return false;
  }
  let draft;
  try { draft = JSON.parse(raw); } catch (e) {
    console.log('[draft] 暫存資料解析失敗', e);
    return false;
  }
  console.log('[draft] 還原暫存資料', draft);

  const g = id => document.getElementById(id);
  if (draft.region && g('setupRegion')) g('setupRegion').value = draft.region;
  if (typeof updateSetupNationality === 'function') updateSetupNationality();
  if (draft.nationality && g('setupNationality')) g('setupNationality').value = draft.nationality;
  if (draft.university && g('setupUniversity')) g('setupUniversity').value = draft.university;
  if (draft.department && g('setupDept')) g('setupDept').value = draft.department;
  if (draft.identity_type && g('setupIdentity')) g('setupIdentity').value = draft.identity_type;
  if (draft.expected_arrival && g('setupArrival')) g('setupArrival').value = draft.expected_arrival;
  if (draft.admission_status) {
    const card = document.querySelector(`.status-card[data-val="${draft.admission_status}"]`);
    if (card) selectStatus(card);
  }
  updatePreview();

  if (draft.quizActive) {
    _quizFormData = {
      region: draft.region,
      nationality: draft.nationality,
      university: draft.university,
      identity_type: draft.identity_type,
      admission_status: draft.admission_status,
      department: draft.department,
      expected_arrival: draft.expected_arrival,
    };
    _quizAnswers = draft.quizAnswers || {};
    _quizSequence = _quizSequenceForIdentity(draft.identity_type);
    if (draft.identity_type === 'foreign_student' && _quizAnswers.has_taiwan_id === undefined) {
      _quizAnswers.has_taiwan_id = false;
    }
    _quizStep = Math.min(draft.quizStep || 0, _quizSequence.length - 1);
    _quizActive = true;

    _buildQuizProgress(_quizSequence.length);
    const overlay = g('quizOverlay');
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
    document.getElementById(_quizSequence[_quizStep]).classList.add('visible');
    _updateQuizDots(_quizStep);
    _refreshQuizCardUI();
  }

  // updatePreview() 在還原問答狀態前已先存了一次草稿，這裡用最終狀態覆寫回去
  saveSetupDraft();
  return true;
}

/** 依身份別決定問答題目：外籍生不問「是否有台灣身份證」 */
function _quizSequenceForIdentity(identity) {
  return identity === 'foreign_student' ? ['quizQ2'] : ['quizQ1', 'quizQ2'];
}

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
  if (!region) { showError('regionErr', window.I18N_PROFILE_SETUP?.selectRegion || '請選擇地區'); ok = false; }
  if (!nationality) { showError('nationalityErr', window.I18N_PROFILE_SETUP?.selectNationality || '請選擇國籍'); ok = false; }
  if (!university)  { showError('universityErr', window.I18N_PROFILE_SETUP?.selectUniversity || '請選擇就讀學校'); ok = false; }
  if (!identity)    { showError('identityErr', window.I18N_PROFILE_SETUP?.selectIdentity || '請選擇身份別'); ok = false; }
  if (!status)      { showError('statusErr', window.I18N_PROFILE_SETUP?.selectAdmissionStatus || '請選擇入學狀態'); ok = false; }
  if (!arrival)     { showError('arrivalErr', window.I18N_PROFILE_SETUP?.fillArrivalDate || '請填寫預計抵台日期'); ok = false; }
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

  // 外籍生依定義不會持有台灣身份證：跳過 Q1，答案自動設為「否」
  _quizSequence = _quizSequenceForIdentity(identity);
  _quizStep = 0;
  _quizAnswers = (identity === 'foreign_student') ? { has_taiwan_id: false } : {};
  _quizActive = true;
  saveSetupDraft();

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
    _refreshQuizCardUI();
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
  saveSetupDraft();

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
    saveSetupDraft();
    const nextCard = document.getElementById(_quizSequence[nextStep]);
    setTimeout(() => {
      nextCard.classList.add('visible');
      _refreshQuizCardUI();
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
    _quizActive = false;
    saveSetupDraft();
  };

  let apiOk, data;
  try {
    ({ ok: apiOk, data } = await apiFetch('/api/users/profile/', 'POST', body));
  } catch (err) {
    closeOverlay();
    showToast(tCommon('networkError', '網路錯誤，請確認連線後再試'), 'error');
    return;
  }

  if (!apiOk) {
    closeOverlay();
    const msg = (data?.errors && Object.keys(data.errors).length > 0)
      ? Object.values(data.errors).flat().join('、')
      : (data?.message || tCommon('saveFailed', '儲存失敗，請稍後再試'));
    showToast(msg, 'error');
    return;
  }

  clearSetupDraft();
  showToast(tCommon('profileSaved', '資料已儲存！個人化流程已生成 🎉'), 'success');
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

  showToast(tCommon('profileUpdated', '個人資料已更新'), 'success');
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

  showToast(tCommon('passwordUpdated', '密碼已更新，請重新登入'), 'success');
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
  window.location.href = '/logout/';
}

/* ════════════════════════════════════════
   11. 刪除帳號
   DELETE /api/users/delete/
════════════════════════════════════════ */
async function deleteAccount() {
  const { ok, data } = await apiFetch('/api/users/delete/', 'DELETE');
  if (ok) {
    showToast(tCommon('accountDeactivated', '帳號已停用，感謝您使用 ReadyTo Taiwan'), 'info', 2000);
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
  set('dashSubtitle', `${IDENTITY_LABELS[profile?.identity_type] || '境外生'}，歡迎使用 ReadyTo Taiwan。`);
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
  if (lastLoginEl) lastLoginEl.textContent = new Date().toLocaleString(getSiteLocale());

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
  const identityVal = g('setupIdentity')?.value;
  const statusVal = g('admissionStatusVal')?.value;
  set('prevNationality', g('setupNationality')?.value || window.I18N_PROFILE_SETUP?.nationalityNotSelected || '國籍未選');
  set('prevIdentity', window.I18N_PROFILE_SETUP?.identityLabels?.[identityVal] || IDENTITY_LABELS[identityVal] || window.I18N_PROFILE_SETUP?.identityNotSelected || '身份別未選');
  set('prevStatus', window.I18N_PROFILE_SETUP?.statusLabels?.[statusVal] || STATUS_LABELS[statusVal] || window.I18N_PROFILE_SETUP?.statusNotSelected || '狀態未選');
  const univSel = g('setupUniversity');
  const univLabel = univSel?.options[univSel.selectedIndex]?.text || univSel?.value || '—';
  set('prevUniv', univLabel !== '請選擇就讀學校' ? univLabel : '—');
  set('prevDept', g('setupDept')?.value || '—');
  set('prevArrival', g('setupArrival')?.value || '—');

  if (typeof saveSetupDraft === 'function') saveSetupDraft();
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
      showToast(tCommon('emailVerified', 'Email 驗證成功！請登入您的帳號'), 'success');
    } else if (verified === 'fail') {
      showToast(tCommon('verifyInvalid', '驗證連結無效或已使用'), 'error');
    } else if (verified === 'expired') {
      showToast(tCommon('verifyExpired', '驗證連結已過期，請重新申請'), 'error');
    }
    if (params.get('deleted') === '1') showToast(tCommon('accountDeactivated', '帳號已停用，感謝您使用 ReadyTo Taiwan'), 'info', 5000);
    if (params.get('need_verify') === '1') showToast(tCommon('needVerify', '請先驗證電子信箱才能繼續'), 'error');

    // 若有待驗證狀態（且非剛完成驗證），顯示驗證等待面板
    if (pendingEmail && verified !== '1') {
      showVerifyEmailPanel(pendingEmail);
      return;
    }

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

/** 收到 Google ID Token 後送往後端驗證並建立登入 session */
async function handleGoogleLogin(response) {
  const credential = response.credential;
  if (!credential) {
    showToast(tCommon('googleFailed', 'Google 登入失敗，未取得憑證'), 'error');
    return;
  }

  const { ok, data } = await apiFetch('/api/users/google-login/', 'POST', { credential });

  if (!ok) {
    showToast(data?.message || 'Google 登入失敗', 'error');
    return;
  }

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

/* ════════════════════════════════════════
   17. 導覽列搜尋（指南站內搜尋）
════════════════════════════════════════ */
function initGuidesSearch(LANG) {
      window.GUIDES_I18N = {
        'zh-hant': [
          { icon: '📋', title: '查看任務清單', desc: '我的個人化辦理任務清單', url: '/flows/my-tasks/' },
          { icon: '🤖', title: '詢問 AI 小幫手', desc: '有問題隨時問，簽證、居留、生活都能幫你解答', url: '/chatbot/' },
          { icon: '📚', title: '資訊中心', desc: '居留證辦理・住宿・交通等常用說明', url: '/guides/' },
          { icon: '✏️', title: '編輯資料', desc: '更新個人資料與身份別設定', url: '/profile/edit/' },
          { icon: '🌏', title: '各國專區', desc: '依地區查看海外聯招會申請說明，香港、馬來西亞、泰國等', url: '/guides/national-area/' },
          { icon: '📋', title: '入學申請指南', desc: '申請資格、時程、所需文件與注意事項整理', url: '/guides/admissions/' },
          { icon: '🪪', title: '外籍生 ARC 辦理', desc: '外國護照入學者的居留證申請流程與文件清單', url: '/guides/arc-foreign/' },
          { icon: '🪪', title: '僑生 ARC 辦理', desc: '持外國護照入台的僑生居留證申請說明', url: '/guides/arc-overseas/' },
          { icon: '🪪', title: '港澳生居留說明', desc: '入出境許可證、居留申請流程與健保工讀說明', url: '/guides/arc-exchange/' },
          { icon: '🏠', title: '中央大學住宿申請', desc: '宿舍分區、設備、申請流程與外僑優先保證說明', url: '/guides/housing-ncu/' },
          { icon: '🚌', title: '中央大學公車指南', desc: '主要路線、常見目的地與即時查詢連結', url: '/guides/bus-ncu/' },
          { icon: '⚖️', title: '來臺就學相關法規', desc: '入學・居留・健保・工讀・學籍等重要法規說明', url: '/guides/regulations/' },
          { icon: '💼', title: '工作許可證', desc: '申請流程、每週工時上限、違規罰則說明', url: '/guides/work-permit/' },
          { icon: '🌱', title: '心理支持', desc: '諮商中心預約、壓力、人際困擾、24H 熱線', url: '/guides/mental-health/' },
          { icon: '🏥', title: '醫療資訊', desc: '衛保組、校外診所、周邊醫院、急診與緊急電話', url: '/guides/medical/' },
          { icon: '🏆', title: '獎助學金', desc: '僑生獎學金、清寒補助、校內外各項申請指南', url: '/guides/scholarship/' },
          { icon: '🏥', title: '全民健保申請', desc: 'ARC 核發後即可加保，門診費用大幅降低', url: '/guides/nhi/' },
          { icon: '🏦', title: '在台開設銀行帳戶', desc: '統一證號說明、郵局・台灣銀行・玉山銀行開戶比較', url: '/guides/bank/' },
          { icon: '📱', title: '台灣門號申辦', desc: '預付卡 vs 月租方案，各大電信業者說明', url: '/guides/sim/' },
          { icon: '📄', title: '行政文件', desc: '在學證明、成績單、推薦信申請說明', url: '/guides/admin-docs/' },
          { icon: '🗂️', title: '學籍辦理', desc: '休學、復學、轉系、雙主修規定與流程', url: '/guides/enrollment/' },
          { icon: '📚', title: '課務資訊', desc: '選課、加退選、人工加退選、停修流程與日程', url: '/guides/course/' },
          { icon: '🎓', title: '成績與畢業門檻', desc: '等第制 GPA、畢業學分、英文門檻（TOEIC）依學院標準', url: '/guides/graduation/' },
          { icon: '🖥️', title: '校內系統', desc: 'Portal 帳號啟用、ee-class 課程平台、學生信箱設定', url: '/guides/systems/' },
          { icon: '🚨', title: '緊急聯絡', desc: '110・119・112・校安中心・國際事務處', url: '/guides/emergency/' },
          { icon: '📖', title: '圖書館', desc: '借書規則、K書中心、學術資料庫、列印費用', url: '/guides/library/' },
          { icon: '🗺️', title: '地圖導覽', desc: '學校・醫院・車站・機場位置，一鍵導航', url: '/guides/map/' },
        ],
        'en': [
          { icon: '📋', title: 'View Task List', desc: 'My personalized to-do list', url: '/flows/my-tasks/' },
          { icon: '🤖', title: 'Ask the AI Assistant', desc: 'Get help anytime — visa, ARC, living in Taiwan', url: '/chatbot/' },
          { icon: '📚', title: 'Info Center', desc: 'Guides on ARC, housing, transport and more', url: '/guides/' },
          { icon: '✏️', title: 'Edit Information', desc: 'Update your personal info and identity type', url: '/profile/edit/' },
          { icon: '🌏', title: 'National Area', desc: 'View application guides by region: Hong Kong, Malaysia, Thailand, and more', url: '/guides/national-area/' },
          { icon: '📋', title: 'Admissions Guide', desc: 'Eligibility, timeline, required documents and key notes', url: '/guides/admissions/' },
          { icon: '🪪', title: 'Foreign Student ARC Application', desc: 'ARC application process and document checklist for foreign passport holders', url: '/guides/arc-foreign/' },
          { icon: '🪪', title: 'Overseas Chinese Student ARC Application', desc: 'ARC application guide for overseas Chinese students entering Taiwan with a foreign passport', url: '/guides/arc-overseas/' },
          { icon: '🪪', title: 'HK & Macau Student Residency Guide', desc: 'Entry Permit, Residency Process, NHI & Work Rights Explained', url: '/guides/arc-exchange/' },
          { icon: '🏠', title: 'NCU Dormitory Application', desc: 'Dormitory zones, facilities, application process, and priority guarantee for foreign students', url: '/guides/housing-ncu/' },
          { icon: '🚌', title: 'NCU Bus Guide', desc: 'Main routes, common destinations, and real-time query links', url: '/guides/bus-ncu/' },
          { icon: '⚖️', title: 'Taiwan Study-Related Regulations', desc: 'Key regulations on admission, residency, health insurance, work, and academic status', url: '/guides/regulations/' },
          { icon: '💼', title: 'Work Permit', desc: 'Application process, weekly hour limits, and penalty rules', url: '/guides/work-permit/' },
          { icon: '🌱', title: 'Mental Health Support', desc: 'Counseling center, stress, interpersonal issues, 24H hotline', url: '/guides/mental-health/' },
          { icon: '🏥', title: 'Medical Information', desc: 'Health center, off-campus clinics, nearby hospitals, emergency contacts', url: '/guides/medical/' },
          { icon: '🏆', title: 'Scholarships', desc: 'Overseas Chinese scholarships, financial aid, on/off-campus application guides', url: '/guides/scholarship/' },
          { icon: '🏥', title: 'National Health Insurance', desc: 'Enroll after ARC approval and reduce clinic costs', url: '/guides/nhi/' },
          { icon: '🏦', title: 'Open a Bank Account in Taiwan', desc: 'Essential for scholarships — Post Office, Bank of Taiwan, E.Sun compared', url: '/guides/bank/' },
          { icon: '📱', title: 'Get a Taiwan SIM Card', desc: 'Prepaid vs monthly plans — major carriers explained', url: '/guides/sim/' },
          { icon: '📄', title: 'Administrative Documents', desc: 'Enrollment certificate, transcripts, recommendation letter requests', url: '/guides/admin-docs/' },
          { icon: '🗂️', title: 'Student Status', desc: 'Leave of absence, reinstatement, transfer, double major rules and process', url: '/guides/enrollment/' },
          { icon: '📚', title: 'Course Affairs', desc: 'Course selection, add/drop, manual add/drop, withdrawal process and schedule', url: '/guides/course/' },
          { icon: '🎓', title: 'Grades & Graduation Requirements', desc: 'Letter grade GPA, graduation credits, English proficiency (TOEIC) by college', url: '/guides/graduation/' },
          { icon: '🖥️', title: 'Campus Systems', desc: 'Portal account activation, ee-class platform, student email setup', url: '/guides/systems/' },
          { icon: '🚨', title: 'Emergency Contacts', desc: '110 · 119 · 112 · Campus Security · International Affairs Office', url: '/guides/emergency/' },
          { icon: '📖', title: 'Library', desc: 'Borrowing rules, study rooms, academic databases, printing fees', url: '/guides/library/' },
          { icon: '🗺️', title: 'Map & Navigation', desc: 'School, hospital, station, airport — one-tap navigation', url: '/guides/map/' },
        ],
        'id': [
          { icon: '📋', title: 'Lihat Daftar Tugas', desc: 'Daftar tugas pribadi saya', url: '/flows/my-tasks/' },
          { icon: '🤖', title: 'Tanya Asisten AI', desc: 'Bantuan kapan saja — visa, ARC, kehidupan di Taiwan', url: '/chatbot/' },
          { icon: '📚', title: 'Pusat Informasi', desc: 'Panduan ARC, asrama, transportasi, dan lainnya', url: '/guides/' },
          { icon: '✏️', title: 'Edit Data', desc: 'Perbarui informasi pribadi dan jenis identitas', url: '/profile/edit/' },
          { icon: '🌏', title: 'Area Nasional', desc: 'Lihat panduan pendaftaran per wilayah: Hong Kong, Malaysia, Thailand, dll.', url: '/guides/national-area/' },
          { icon: '📋', title: 'Panduan Penerimaan', desc: 'Syarat, jadwal, dokumen yang diperlukan, dan catatan penting', url: '/guides/admissions/' },
          { icon: '🪪', title: 'Pengajuan ARC Mahasiswa Asing', desc: 'Proses pengajuan ARC dan daftar dokumen untuk pemegang paspor asing', url: '/guides/arc-foreign/' },
          { icon: '🪪', title: 'Pengajuan ARC Mahasiswa Tionghoa Perantau', desc: 'Panduan pengajuan ARC bagi mahasiswa Tionghoa yang masuk Taiwan dengan paspor asing', url: '/guides/arc-overseas/' },
          { icon: '🪪', title: 'Panduan Tinggal Mahasiswa HK & Makau', desc: 'Izin Masuk/Keluar, Proses Izin Tinggal, JKN & Hak Kerja', url: '/guides/arc-exchange/' },
          { icon: '🏠', title: 'Permohonan Asrama NCU', desc: 'Zona asrama, fasilitas, proses pendaftaran, dan jaminan prioritas untuk mahasiswa asing', url: '/guides/housing-ncu/' },
          { icon: '🚌', title: 'Panduan Bus NCU', desc: 'Rute utama, tujuan umum, dan tautan kueri waktu nyata', url: '/guides/bus-ncu/' },
          { icon: '⚖️', title: 'Peraturan Terkait Studi di Taiwan', desc: 'Peraturan penting tentang penerimaan, tinggal, asuransi kesehatan, kerja, dan status akademik', url: '/guides/regulations/' },
          { icon: '💼', title: 'Izin Kerja', desc: 'Proses pengajuan, batas jam kerja mingguan, dan denda pelanggaran', url: '/guides/work-permit/' },
          { icon: '🌱', title: 'Dukungan Kesehatan Mental', desc: 'Pusat konseling, stres, masalah interpersonal, hotline 24 jam', url: '/guides/mental-health/' },
          { icon: '🏥', title: 'Informasi Medis', desc: 'Pusat kesehatan, klinik luar kampus, rumah sakit terdekat, kontak darurat', url: '/guides/medical/' },
          { icon: '🏆', title: 'Beasiswa', desc: 'Beasiswa mahasiswa Tionghoa perantau, bantuan keuangan, panduan pendaftaran', url: '/guides/scholarship/' },
          { icon: '🏥', title: 'Pendaftaran Asuransi Kesehatan Nasional', desc: 'Daftar setelah ARC diterbitkan, biaya klinik jauh berkurang', url: '/guides/nhi/' },
          { icon: '🏦', title: 'Buka Rekening Bank di Taiwan', desc: 'Wajib untuk beasiswa — Kantor Pos, Bank of Taiwan, E.Sun dibandingkan', url: '/guides/bank/' },
          { icon: '📱', title: 'Daftar Nomor Telepon Taiwan', desc: 'Kartu prabayar vs bulanan — penjelasan operator utama', url: '/guides/sim/' },
          { icon: '📄', title: 'Dokumen Administratif', desc: 'Surat keterangan mahasiswa, transkrip, permohonan surat rekomendasi', url: '/guides/admin-docs/' },
          { icon: '🗂️', title: 'Status Mahasiswa', desc: 'Cuti, kembali kuliah, pindah jurusan, aturan dan proses double major', url: '/guides/enrollment/' },
          { icon: '📚', title: 'Urusan Perkuliahan', desc: 'Pemilihan mata kuliah, tambah/hapus, penarikan, jadwal dan proses', url: '/guides/course/' },
          { icon: '🎓', title: 'Nilai & Syarat Kelulusan', desc: 'GPA huruf, kredit kelulusan, syarat bahasa Inggris (TOEIC) per fakultas', url: '/guides/graduation/' },
          { icon: '🖥️', title: 'Sistem Kampus', desc: 'Aktivasi akun Portal, platform ee-class, pengaturan email mahasiswa', url: '/guides/systems/' },
          { icon: '🚨', title: 'Kontak Darurat', desc: '110 · 119 · 112 · Keamanan Kampus · Kantor Urusan Internasional', url: '/guides/emergency/' },
          { icon: '📖', title: 'Perpustakaan', desc: 'Aturan peminjaman, ruang belajar, database akademik, biaya cetak', url: '/guides/library/' },
          { icon: '🗺️', title: 'Peta & Navigasi', desc: 'Sekolah, rumah sakit, stasiun, bandara — navigasi satu ketuk', url: '/guides/map/' },
        ],
        'ja': [
          { icon: '📋', title: 'タスクリストを見る', desc: '私のパーソナライズされたToDoリスト', url: '/flows/my-tasks/' },
          { icon: '🤖', title: 'AIアシスタントに質問', desc: 'いつでも質問できます — ビザ、ARC、台湾生活', url: '/chatbot/' },
          { icon: '📚', title: '情報センター', desc: 'ARC・寮・交通などのガイド', url: '/guides/' },
          { icon: '✏️', title: '情報を編集', desc: '個人情報と身分種別を更新', url: '/profile/edit/' },
          { icon: '🌏', title: '国別専用ページ', desc: '地域別申請説明（香港・マレーシア・タイなど）を確認できます', url: '/guides/national-area/' },
          { icon: '📋', title: '入学申請ガイド', desc: '申請資格・日程・必要書類と注意事項', url: '/guides/admissions/' },
          { icon: '🪪', title: '外国人留学生の居留証申請', desc: '外国パスポートで入学した学生の居留証申請手続きと書類リスト', url: '/guides/arc-foreign/' },
          { icon: '🪪', title: '僑生の居留証申請', desc: '外国パスポートで台湾入国した僑生の居留証申請説明', url: '/guides/arc-overseas/' },
          { icon: '🪪', title: '香港・マカオ学生の在留ガイド', desc: '入出境許可証・在留申請手順・健保とアルバイト説明', url: '/guides/arc-exchange/' },
          { icon: '🏠', title: '中央大学の寮申請', desc: '寮のゾーン・設備・申請手続きと外国人留学生優先保証の説明', url: '/guides/housing-ncu/' },
          { icon: '🚌', title: '中央大学バスガイド', desc: '主要路線・よく行く目的地とリアルタイム検索リンク', url: '/guides/bus-ncu/' },
          { icon: '⚖️', title: '台湾留学関連法規', desc: '入学・居留・健保・工讀・学籍等の重要法規説明', url: '/guides/regulations/' },
          { icon: '💼', title: '労働許可証', desc: '申請手続き・週間労働時間上限・違反罰則の説明', url: '/guides/work-permit/' },
          { icon: '🌱', title: 'メンタルヘルスサポート', desc: 'カウンセリングセンター・ストレス・人間関係・24H相談窓口', url: '/guides/mental-health/' },
          { icon: '🏥', title: '医療情報', desc: '保健センター・学外クリニック・周辺病院・救急連絡先', url: '/guides/medical/' },
          { icon: '🏆', title: '奨学金', desc: '僑生奨学金・経済支援・学内外の各種申請ガイド', url: '/guides/scholarship/' },
          { icon: '🏥', title: '全民健保加入手続き', desc: 'ARC取得後すぐ加入でき、外来費用が大幅に低下', url: '/guides/nhi/' },
          { icon: '🏦', title: '台湾の銀行口座開設', desc: '奨学金受取に必須 — 郵便局・台湾銀行・玉山銀行を比較', url: '/guides/bank/' },
          { icon: '📱', title: '台湾SIMカード申込み', desc: 'プリペイドvs月額プラン — 主要キャリアを解説', url: '/guides/sim/' },
          { icon: '📄', title: '行政書類', desc: '在学証明書・成績証明書・推薦状の申請方法', url: '/guides/admin-docs/' },
          { icon: '🗂️', title: '学籍手続き', desc: '休学・復学・転科・ダブルメジャーの規定と手続き', url: '/guides/enrollment/' },
          { icon: '📚', title: '履修情報', desc: '履修登録・追加/取消・手動追加取消・中途取消の流れと日程', url: '/guides/course/' },
          { icon: '🎓', title: '成績と卒業要件', desc: 'レターグレードGPA・卒業単位・英語要件（TOEIC）学部別基準', url: '/guides/graduation/' },
          { icon: '🖥️', title: '学内システム', desc: 'Portalアカウント有効化・ee-classプラットフォーム・学生メール設定', url: '/guides/systems/' },
          { icon: '🚨', title: '緊急連絡先', desc: '110・119・112・キャンパスセキュリティ・国際事務処', url: '/guides/emergency/' },
          { icon: '📖', title: '図書館', desc: '貸出ルール・自習室・学術データベース・印刷料金', url: '/guides/library/' },
          { icon: '🗺️', title: 'マップ＆ナビ', desc: '大学・病院・駅・空港の位置 — ワンタップでナビ', url: '/guides/map/' },
        ],
        'ms': [
          { icon: '📋', title: 'Lihat Senarai Tugasan', desc: 'Senarai tugasan peribadi saya', url: '/flows/my-tasks/' },
          { icon: '🤖', title: 'Tanya Pembantu AI', desc: 'Bantuan bila-bila masa — visa, ARC, kehidupan di Taiwan', url: '/chatbot/' },
          { icon: '📚', title: 'Pusat Maklumat', desc: 'Panduan ARC, asrama, pengangkutan dan lain-lain', url: '/guides/' },
          { icon: '✏️', title: 'Edit Maklumat', desc: 'Kemaskini maklumat peribadi dan jenis identiti', url: '/profile/edit/' },
          { icon: '🌏', title: 'Kawasan Negara', desc: 'Lihat panduan permohonan mengikut kawasan: Hong Kong, Malaysia, Thailand, dll.', url: '/guides/national-area/' },
          { icon: '📋', title: 'Panduan Kemasukan', desc: 'Kelayakan, jadual, dokumen diperlukan dan nota penting', url: '/guides/admissions/' },
          { icon: '🪪', title: 'Permohonan ARC Pelajar Asing', desc: 'Proses permohonan ARC dan senarai dokumen bagi pemegang pasport asing', url: '/guides/arc-foreign/' },
          { icon: '🪪', title: 'Permohonan ARC Pelajar Cina Perantau', desc: 'Panduan permohonan ARC bagi pelajar Cina perantau yang masuk Taiwan dengan pasport asing', url: '/guides/arc-overseas/' },
          { icon: '🪪', title: 'Panduan Pemastautin Pelajar HK & Macao', desc: 'Permit Masuk/Keluar, Proses Pemastautin, NHI & Hak Bekerja', url: '/guides/arc-exchange/' },
          { icon: '🏠', title: 'Permohonan Asrama NCU', desc: 'Zon asrama, kemudahan, proses permohonan, dan jaminan keutamaan untuk pelajar asing', url: '/guides/housing-ncu/' },
          { icon: '🚌', title: 'Panduan Bas NCU', desc: 'Laluan utama, destinasi lazim, dan pautan pertanyaan masa nyata', url: '/guides/bus-ncu/' },
          { icon: '⚖️', title: 'Peraturan Berkaitan Pengajian di Taiwan', desc: 'Peraturan penting tentang kemasukan, pemastautinan, insurans kesihatan, bekerja, dan status akademik', url: '/guides/regulations/' },
          { icon: '💼', title: 'Permit Kerja', desc: 'Proses permohonan, had jam kerja mingguan, dan denda pelanggaran', url: '/guides/work-permit/' },
          { icon: '🌱', title: 'Sokongan Kesihatan Mental', desc: 'Pusat kaunseling, tekanan, masalah interpersonal, talian bantuan 24 jam', url: '/guides/mental-health/' },
          { icon: '🏥', title: 'Maklumat Perubatan', desc: 'Pusat kesihatan, klinik luar kampus, hospital berdekatan, kenalan kecemasan', url: '/guides/medical/' },
          { icon: '🏆', title: 'Biasiswa', desc: 'Biasiswa pelajar Cina perantau, bantuan kewangan, panduan permohonan', url: '/guides/scholarship/' },
          { icon: '🏥', title: 'Permohonan Insurans Kesihatan Kebangsaan', desc: 'Daftar selepas ARC diluluskan, kos klinik berkurangan', url: '/guides/nhi/' },
          { icon: '🏦', title: 'Buka Akaun Bank di Taiwan', desc: 'Wajib untuk biasiswa — Pejabat Pos, Bank Taiwan, E.Sun dibandingkan', url: '/guides/bank/' },
          { icon: '📱', title: 'Dapatkan Nombor Telefon Taiwan', desc: 'Kad prabayar vs bulanan — penjelasan pengendali utama', url: '/guides/sim/' },
          { icon: '📄', title: 'Dokumen Pentadbiran', desc: 'Surat pengesahan pelajar, transkrip, permohonan surat sokongan', url: '/guides/admin-docs/' },
          { icon: '🗂️', title: 'Status Pelajar', desc: 'Cuti belajar, kembali belajar, tukar jurusan, peraturan double major', url: '/guides/enrollment/' },
          { icon: '📚', title: 'Urusan Kursus', desc: 'Pemilihan kursus, tambah/gugur, penarikan, jadual dan proses', url: '/guides/course/' },
          { icon: '🎓', title: 'Gred & Syarat Graduasi', desc: 'GPA huruf, kredit graduasi, syarat Bahasa Inggeris (TOEIC) mengikut fakulti', url: '/guides/graduation/' },
          { icon: '🖥️', title: 'Sistem Kampus', desc: 'Pengaktifan akaun Portal, platform ee-class, tetapan emel pelajar', url: '/guides/systems/' },
          { icon: '🚨', title: 'Kenalan Kecemasan', desc: '110 · 119 · 112 · Keselamatan Kampus · Pejabat Hal Ehwal Antarabangsa', url: '/guides/emergency/' },
          { icon: '📖', title: 'Perpustakaan', desc: 'Peraturan pinjaman, bilik belajar, pangkalan data akademik, kos cetakan', url: '/guides/library/' },
          { icon: '🗺️', title: 'Peta & Navigasi', desc: 'Lokasi sekolah, hospital, stesen, lapangan terbang — navigasi satu ketik', url: '/guides/map/' },
        ],
        'my': [
          { icon: '📋', title: 'တာဝန်စာရင်း ကြည့်ရန်', desc: 'ကျွန်ုပ်၏ ကိုယ်ပိုင်တာဝန်စာရင်း', url: '/flows/my-tasks/' },
          { icon: '🤖', title: 'AI အကူအညီကို မေးရန်', desc: 'အချိန်မရွေး မေးနိုင်သည် — ဗီဇာ၊ ARC၊ တိုင်ဝမ်ဘဝ', url: '/chatbot/' },
          { icon: '📚', title: 'သတင်းအချက်အလက်စင်တာ', desc: 'ARC၊ အဆောင်၊ သွားလာရေးနှင့် အခြားလမ်းညွှန်များ', url: '/guides/' },
          { icon: '✏️', title: 'အချက်အလက် ပြင်ရန်', desc: 'ကိုယ်ရေးကိုယ်တာ အချက်အလက်နှင့် အထောက်အထားအမျိုးအစား ပြင်ရန်', url: '/profile/edit/' },
          { icon: '🌏', title: 'နိုင်ငံဒေသများ', desc: 'ဒေသအလိုက် လျှောက်ထားမှုလမ်းညွှန်ကို ကြည့်ရှုပါ: ဟောင်ကောင်၊ မလေးရှား၊ ထိုင်း စသည်', url: '/guides/national-area/' },
          { icon: '📋', title: 'ဝင်ခွင့်လျှောက်ထားမှုလမ်းညွှန်', desc: 'လိုအပ်ချက်၊ အချိန်ဇယား၊ လိုအပ်သောစာရွက်စာတမ်းများနှင့် အရေးကြီးသောမှတ်ချက်များ', url: '/guides/admissions/' },
          { icon: '🪪', title: 'နိုင်ငံခြားကျောင်းသားများ ARC လျှောက်ထားခြင်း', desc: 'နိုင်ငံခြားနိုင်ငံကူးလက်မှတ်ဖြင့် ဝင်ရောက်သူများ ARC လျှောက်လွှာနှင့် စာရွက်စာတမ်းများ', url: '/guides/arc-foreign/' },
          { icon: '🪪', title: 'ဝပ်ကျောင်းသားများ ARC လျှောက်ထားခြင်း', desc: 'နိုင်ငံခြားနိုင်ငံကူးလက်မှတ်ဖြင့် တိုင်ဝမ်ဝင်ရောက်သော ဝပ်ကျောင်းသားများ ARC လမ်းညွှန်', url: '/guides/arc-overseas/' },
          { icon: '🪪', title: 'ဟောင်ကောင်နှင့်မကာအိုကျောင်းသား နေထိုင်ခွင့်လမ်းညွှန်', desc: 'ဝင်ထွက်ခွင့်ပါမစ်၊ နေထိုင်ခွင့်လုပ်ငန်းစဉ်၊ ကျန်းမာရေးအာမခံ', url: '/guides/arc-exchange/' },
          { icon: '🏠', title: 'NCU အိပ်ဆောင်လျှောက်ထားခြင်း', desc: 'ကျောင်းသူဆောင်ဇုန်များ၊ အသုံးအဆောင်များ၊ လျှောက်ထားရေးနှင့် နိုင်ငံခြားကျောင်းသားများ ဦးစားပေးသေချာပေါက်', url: '/guides/housing-ncu/' },
          { icon: '🚌', title: 'NCU ဘတ်စ်ကားလမ်းညွှန်', desc: 'အဓိကလမ်းကြောင်းများ၊ ပုံမှန်သွားသောနေရာများနှင့် အချိန်နှင့်တပြေးညီ သတင်းသုံးနည်း', url: '/guides/bus-ncu/' },
          { icon: '⚖️', title: 'တိုင်ဝမ်တွင် ပညာသင်ရေးဆိုင်ရာ ဥပဒေများ', desc: 'ဝင်ခွင့်၊ နေထိုင်ခွင့်၊ ကျန်းမာရေးအာမခံ၊ အလုပ်နှင့် ပညာရေးဆိုင်ရာ အရေးကြီးသောဥပဒေများ', url: '/guides/regulations/' },
          { icon: '💼', title: 'အလုပ်ခွင့်ပါမစ်', desc: 'လျှောက်ထားမှုလုပ်ငန်းစဉ်၊ တစ်ပတ်အလုပ်ချိန်အကန့်အသတ်၊ ဖောက်ဖျက်မှုဒဏ်ကြေးများ', url: '/guides/work-permit/' },
          { icon: '🌱', title: 'စိတ်ကျန်းမာရေးပံ့ပိုးမှု', desc: 'အကြံပေးဌာန ချိန်းဆိုခြင်း၊ စိတ်ဖိစီးမှု၊ လူမှုဆက်ဆံရေးပြဿနာ၊ ၂၄နာရီ ဖုန်းလိုင်း', url: '/guides/mental-health/' },
          { icon: '🏥', title: 'ဆေးပညာဆိုင်ရာ သတင်းအချက်အလက်', desc: 'ကျန်းမာရေးဗဟိုဌာန၊ ကျောင်းပြင်ပဆေးခန်း၊ နီးစပ်သောဆေးရုံ၊ အရေးပေါ်ဆက်သွယ်ရန်', url: '/guides/medical/' },
          { icon: '🏆', title: 'ပညာသင်ဆု', desc: 'ဝပ်ပညာသင်ဆု၊ ငွေကြေးအကူအညီ၊ ကျောင်းတွင်းကျောင်းပြင်ပ လျှောက်ထားနည်းလမ်းညွှန်', url: '/guides/scholarship/' },
          { icon: '🏥', title: 'အမျိုးသားကျန်းမာရေးအာမခံ လျှောက်ထားခြင်း', desc: 'ARC ရပြီးနောက် ကုသစရိတ် သိသိသာသာ လျော့ကျသည်', url: '/guides/nhi/' },
          { icon: '🏦', title: 'တိုင်ဝမ်ဘဏ်အကောင့် ဖွင့်ခြင်း', desc: 'ပညာသင်ဆု ရယူရန် မဖြစ်မနေလိုအပ်သည်', url: '/guides/bank/' },
          { icon: '📱', title: 'တိုင်ဝမ်ဖုန်းနံပါတ် လျှောက်ထားခြင်း', desc: 'ကြိုတင်ငွေဖြည့် နှင့် လစဉ်ကြေး - ပင်မ Operator များ ရှင်းလင်းချက်', url: '/guides/sim/' },
          { icon: '📄', title: 'စီမံခန့်ခွဲရေးစာရွက်စာတမ်းများ', desc: 'တက်ရောက်သောကျောင်းသားအထောက်အထား၊ ရမှတ်မှတ်တမ်း၊ ထောက်ခံစာ တောင်းဆိုခြင်း', url: '/guides/admin-docs/' },
          { icon: '🗂️', title: 'ကျောင်းသားအခြေအနေ', desc: 'နားထားခြင်း၊ ပြန်လာခြင်း၊ ဌာနပြောင်းရွှေ့ခြင်း၊ နှစ်ဘာသာမေဂျာ စည်းမျဉ်းနှင့် လုပ်ငန်းစဉ်', url: '/guides/enrollment/' },
          { icon: '📚', title: 'သင်တန်းဆိုင်ရာ သတင်းအချက်အလက်', desc: 'သင်တန်းရွေးချယ်ခြင်း၊ ထည့်/ဖြုတ်ခြင်း၊ ပြုပြင်ခြင်း လုပ်ငန်းစဉ်နှင့် အချိန်ဇယား', url: '/guides/course/' },
          { icon: '🎓', title: 'အမှတ်နှင့် ဘွဲ့လိုအပ်ချက်များ', desc: 'အမှတ်စနစ် GPA၊ ဘွဲ့ရနိုင်ရေးခရက်ဒစ်၊ အင်္ဂလိပ်ဘာသာ (TOEIC) တက္ကသိုလ်အလိုက်', url: '/guides/graduation/' },
          { icon: '🖥️', title: 'ကျောင်းဝင်းစနစ်များ', desc: 'Portal အကောင့်ဖွင့်ခြင်း၊ ee-class သင်တန်းပလက်ဖောင်း၊ ကျောင်းသားအီးမေးလ်', url: '/guides/systems/' },
          { icon: '🚨', title: 'အရေးပေါ်ဆက်သွယ်ရန်', desc: '110 · 119 · 112 · ကျောင်းဝင်းလုံခြုံရေး · နိုင်ငံတကာရေးရာဌာန', url: '/guides/emergency/' },
          { icon: '📖', title: 'စာကြည့်တိုက်', desc: 'ချေးငှားသောစည်းမျဉ်းများ၊ ကိုယ်တိုင်လေ့လာသောအခန်း၊ ပညာရေးဒေတာဘေ့စ်၊ မှတ်တမ်းနှင့် ငွေကြေး', url: '/guides/library/' },
          { icon: '🗺️', title: 'မြေပုံ နှင့် လမ်းညွှန်', desc: 'ကျောင်း ဆေးရုံ ဘူတာ လေဆိပ် - တစ်ချက်နှိပ်လမ်းညွှန်', url: '/guides/map/' },
        ],
        'th': [
          { icon: '📋', title: 'ดูรายการงาน', desc: 'รายการสิ่งที่ต้องทำส่วนตัวของฉัน', url: '/flows/my-tasks/' },
          { icon: '🤖', title: 'ถามผู้ช่วย AI', desc: 'ขอความช่วยเหลือได้ตลอดเวลา — วีซ่า ARC ชีวิตในไต้หวัน', url: '/chatbot/' },
          { icon: '📚', title: 'ศูนย์ข้อมูล', desc: 'คู่มือ ARC หอพัก การเดินทาง และอื่น ๆ', url: '/guides/' },
          { icon: '✏️', title: 'แก้ไขข้อมูล', desc: 'อัปเดตข้อมูลส่วนตัวและประเภทสถานะ', url: '/profile/edit/' },
          { icon: '🌏', title: 'พื้นที่แต่ละประเทศ', desc: 'ดูคำแนะนำการสมัครตามภูมิภาค: ฮ่องกง มาเลเซีย ไทย และอื่นๆ', url: '/guides/national-area/' },
          { icon: '📋', title: 'คู่มือการรับเข้าเรียน', desc: 'คุณสมบัติ กำหนดการ เอกสารที่ต้องใช้ และหมายเหตุสำคัญ', url: '/guides/admissions/' },
          { icon: '🪪', title: 'การยื่นขอ ARC สำหรับนักศึกษาต่างชาติ', desc: 'ขั้นตอนการยื่น ARC และรายการเอกสารสำหรับผู้ถือพาสปอร์ตต่างประเทศ', url: '/guides/arc-foreign/' },
          { icon: '🪪', title: 'การยื่นขอ ARC สำหรับนักศึกษาจีนโพ้นทะเล', desc: 'คู่มือการยื่น ARC สำหรับนักศึกษาจีนโพ้นทะเลที่เข้าไต้หวันด้วยพาสปอร์ตต่างประเทศ', url: '/guides/arc-overseas/' },
          { icon: '🪪', title: 'คู่มือการพำนักนักศึกษา HK และมาเก๊า', desc: 'ใบอนุญาตเข้า-ออก, ขั้นตอนพำนัก, ประกันสุขภาพ & สิทธิทำงาน', url: '/guides/arc-exchange/' },
          { icon: '🏠', title: 'การสมัครหอพัก NCU', desc: 'โซนหอพัก สิ่งอำนวยความสะดวก ขั้นตอนการสมัคร และการรับประกันสิทธิ์ก่อนสำหรับนักศึกษาต่างชาติ', url: '/guides/housing-ncu/' },
          { icon: '🚌', title: 'คู่มือรถบัส NCU', desc: 'เส้นทางหลัก จุดหมายปลายทางทั่วไป และลิงก์ค้นหาแบบเรียลไทม์', url: '/guides/bus-ncu/' },
          { icon: '⚖️', title: 'กฎระเบียบที่เกี่ยวข้องกับการศึกษาในไต้หวัน', desc: 'กฎระเบียบสำคัญเกี่ยวกับการรับเข้าเรียน การพำนัก ประกันสุขภาพ การทำงาน และสถานะทางวิชาการ', url: '/guides/regulations/' },
          { icon: '💼', title: 'ใบอนุญาตทำงาน', desc: 'ขั้นตอนการสมัคร ขีดจำกัดชั่วโมงทำงานต่อสัปดาห์ และบทลงโทษ', url: '/guides/work-permit/' },
          { icon: '🌱', title: 'การสนับสนุนสุขภาพจิต', desc: 'ศูนย์ให้คำปรึกษา ความเครียด ปัญหาความสัมพันธ์ สายด่วน 24 ชม.', url: '/guides/mental-health/' },
          { icon: '🏥', title: 'ข้อมูลทางการแพทย์', desc: 'ศูนย์สุขภาพ คลินิกนอกวิทยาเขต โรงพยาบาลใกล้เคียง ติดต่อฉุกเฉิน', url: '/guides/medical/' },
          { icon: '🏆', title: 'ทุนการศึกษา', desc: 'ทุนนักศึกษาจีนโพ้นทะเล ความช่วยเหลือทางการเงิน คู่มือสมัครในและนอกวิทยาเขต', url: '/guides/scholarship/' },
          { icon: '🏥', title: 'การสมัครประกันสุขภาพแห่งชาติ', desc: 'สมัครได้หลังได้รับ ARC ค่าคลินิกลดลงอย่างมาก', url: '/guides/nhi/' },
          { icon: '🏦', title: 'เปิดบัญชีธนาคารในไต้หวัน', desc: 'จำเป็นสำหรับทุนการศึกษา - เปรียบเทียบ ไปรษณีย์ Bank of Taiwan E.Sun', url: '/guides/bank/' },
          { icon: '📱', title: 'สมัครซิมการ์ดไต้หวัน', desc: 'ซิมเติมเงิน vs รายเดือน - อธิบายผู้ให้บริการหลัก', url: '/guides/sim/' },
          { icon: '📄', title: 'เอกสารราชการ', desc: 'หนังสือรับรองการเป็นนักศึกษา ทรานสคริปต์ คำขอหนังสือรับรอง', url: '/guides/admin-docs/' },
          { icon: '🗂️', title: 'สถานะนักศึกษา', desc: 'การลาพัก การกลับมาเรียน การย้ายสาขา กฎและขั้นตอนวิชาเอกคู่', url: '/guides/enrollment/' },
          { icon: '📚', title: 'กิจการรายวิชา', desc: 'การลงทะเบียน เพิ่ม/ถอน ถอนวิชา กำหนดการและขั้นตอน', url: '/guides/course/' },
          { icon: '🎓', title: 'เกรดและเงื่อนไขสำเร็จการศึกษา', desc: 'GPA ตัวอักษร หน่วยกิตสำเร็จการศึกษา เกณฑ์ภาษาอังกฤษ (TOEIC) ตามคณะ', url: '/guides/graduation/' },
          { icon: '🖥️', title: 'ระบบในวิทยาเขต', desc: 'การเปิดใช้งานบัญชี Portal แพลตฟอร์ม ee-class การตั้งค่าอีเมลนักศึกษา', url: '/guides/systems/' },
          { icon: '🚨', title: 'ติดต่อฉุกเฉิน', desc: '110 · 119 · 112 · รักษาความปลอดภัยวิทยาเขต · สำนักงานกิจการนานาชาติ', url: '/guides/emergency/' },
          { icon: '📖', title: 'ห้องสมุด', desc: 'กฎการยืม ห้องอ่านหนังสือ ฐานข้อมูลวิชาการ ค่าพิมพ์', url: '/guides/library/' },
          { icon: '🗺️', title: 'แผนที่และนำทาง', desc: 'โรงเรียน โรงพยาบาล สถานี สนามบิน - นำทางด้วยแตะเดียว', url: '/guides/map/' },
        ],
        'vi': [
          { icon: '📋', title: 'Xem danh sách nhiệm vụ', desc: 'Danh sách nhiệm vụ cá nhân của tôi', url: '/flows/my-tasks/' },
          { icon: '🤖', title: 'Hỏi trợ lý AI', desc: 'Hỗ trợ bất cứ lúc nào — visa, ARC, cuộc sống tại Đài Loan', url: '/chatbot/' },
          { icon: '📚', title: 'Trung tâm thông tin', desc: 'Hướng dẫn về ARC, ký túc xá, phương tiện đi lại và nhiều hơn nữa', url: '/guides/' },
          { icon: '✏️', title: 'Chỉnh sửa thông tin', desc: 'Cập nhật thông tin cá nhân và loại danh tính', url: '/profile/edit/' },
          { icon: '🌏', title: 'Khu vực theo quốc gia', desc: 'Xem hướng dẫn nộp đơn theo khu vực: Hồng Kông, Malaysia, Thái Lan và nhiều hơn', url: '/guides/national-area/' },
          { icon: '📋', title: 'Hướng dẫn nhập học', desc: 'Điều kiện, lịch trình, tài liệu cần thiết và lưu ý quan trọng', url: '/guides/admissions/' },
          { icon: '🪪', title: 'Nộp đơn ARC cho sinh viên nước ngoài', desc: 'Quy trình nộp đơn ARC và danh sách tài liệu cho người giữ hộ chiếu nước ngoài', url: '/guides/arc-foreign/' },
          { icon: '🪪', title: 'Nộp đơn ARC cho sinh viên Hoa kiều', desc: 'Hướng dẫn nộp ARC cho sinh viên Hoa kiều nhập cảnh Đài Loan bằng hộ chiếu nước ngoài', url: '/guides/arc-overseas/' },
          { icon: '🪪', title: 'Hướng dẫn cư trú cho sinh viên HK & Macau', desc: 'Giấy phép nhập/xuất cảnh, quy trình cư trú, NHI & quyền làm việc', url: '/guides/arc-exchange/' },
          { icon: '🏠', title: 'Nộp đơn ký túc xá NCU', desc: 'Khu ký túc xá, tiện ích, quy trình đăng ký và ưu tiên bảo đảm cho sinh viên nước ngoài', url: '/guides/housing-ncu/' },
          { icon: '🚌', title: 'Hướng dẫn xe buýt NCU', desc: 'Tuyến chính, điểm đến phổ biến và liên kết tra cứu thời gian thực', url: '/guides/bus-ncu/' },
          { icon: '⚖️', title: 'Quy định liên quan đến học tập tại Đài Loan', desc: 'Các quy định quan trọng về nhập học, cư trú, bảo hiểm y tế, làm việc và tình trạng học tập', url: '/guides/regulations/' },
          { icon: '💼', title: 'Giấy phép lao động', desc: 'Quy trình nộp đơn, giới hạn giờ làm việc hàng tuần và hình phạt vi phạm', url: '/guides/work-permit/' },
          { icon: '🌱', title: 'Hỗ trợ sức khỏe tâm thần', desc: 'Trung tâm tư vấn, căng thẳng, vấn đề xã hội, đường dây nóng 24H', url: '/guides/mental-health/' },
          { icon: '🏥', title: 'Thông tin y tế', desc: 'Trung tâm y tế, phòng khám ngoài khuôn viên, bệnh viện gần đây, liên hệ khẩn cấp', url: '/guides/medical/' },
          { icon: '🏆', title: 'Học bổng', desc: 'Học bổng Hoa kiều, hỗ trợ tài chính, hướng dẫn nộp đơn trong và ngoài trường', url: '/guides/scholarship/' },
          { icon: '🏥', title: 'Đăng ký Bảo hiểm y tế quốc gia', desc: 'Đăng ký sau khi được cấp ARC, chi phí phòng khám giảm đáng kể', url: '/guides/nhi/' },
          { icon: '🏦', title: 'Mở tài khoản ngân hàng tại Đài Loan', desc: 'Cần thiết cho học bổng — So sánh Bưu điện, Bank of Taiwan, E.Sun', url: '/guides/bank/' },
          { icon: '📱', title: 'Đăng ký SIM card Đài Loan', desc: 'SIM trả trước vs gói tháng — giải thích các nhà mạng chính', url: '/guides/sim/' },
          { icon: '📄', title: 'Tài liệu hành chính', desc: 'Giấy xác nhận đang học, bảng điểm, yêu cầu thư giới thiệu', url: '/guides/admin-docs/' },
          { icon: '🗂️', title: 'Tình trạng sinh viên', desc: 'Nghỉ học, quay trở lại, chuyển ngành, quy tắc và quy trình ngành đôi', url: '/guides/enrollment/' },
          { icon: '📚', title: 'Việc học tập', desc: 'Chọn môn học, thêm/rút, rút môn, quy trình và lịch trình', url: '/guides/course/' },
          { icon: '🎓', title: 'Điểm số & Yêu cầu tốt nghiệp', desc: 'GPA theo chữ cái, tín chỉ tốt nghiệp, ngưỡng tiếng Anh (TOEIC) theo trường', url: '/guides/graduation/' },
          { icon: '🖥️', title: 'Hệ thống trong khuôn viên', desc: 'Kích hoạt tài khoản Portal, nền tảng ee-class, cài đặt email sinh viên', url: '/guides/systems/' },
          { icon: '🚨', title: 'Liên hệ khẩn cấp', desc: '110 · 119 · 112 · An ninh khuôn viên · Văn phòng Quan hệ Quốc tế', url: '/guides/emergency/' },
          { icon: '📖', title: 'Thư viện', desc: 'Quy tắc mượn sách, phòng học, cơ sở dữ liệu học thuật, phí in ấn', url: '/guides/library/' },
          { icon: '🗺️', title: 'Bản đồ & Điều hướng', desc: 'Trường học, bệnh viện, ga tàu, sân bay — điều hướng một chạm', url: '/guides/map/' },
        ],
        'ko': [
          { icon: '📋', title: '할 일 목록 보기', desc: '나의 개인화된 할 일 목록', url: '/flows/my-tasks/' },
          { icon: '🤖', title: 'AI 어시스턴트에게 질문', desc: '언제든지 도움받기 — 비자, ARC, 대만 생활', url: '/chatbot/' },
          { icon: '📚', title: '정보 센터', desc: 'ARC, 기숙사, 교통 등에 관한 가이드', url: '/guides/' },
          { icon: '✏️', title: '정보 수정', desc: '개인 정보 및 신분 유형 업데이트', url: '/profile/edit/' },
          { icon: '🌏', title: '국가별 전용 페이지', desc: '지역별 지원 안내 확인: 홍콩, 말레이시아, 태국 등', url: '/guides/national-area/' },
          { icon: '📋', title: '입학 지원 가이드', desc: '지원 자격, 일정, 필요 서류 및 주의사항', url: '/guides/admissions/' },
          { icon: '🪪', title: '외국인 유학생 ARC 신청', desc: '외국 여권 소지자의 거류증 신청 절차 및 서류 목록', url: '/guides/arc-foreign/' },
          { icon: '🪪', title: '화교 학생 ARC 신청', desc: '외국 여권으로 대만에 입국한 화교 학생의 거류증 신청 안내', url: '/guides/arc-overseas/' },
          { icon: '🪪', title: '홍콩·마카오 학생 거주 가이드', desc: '입출경 허가증, 거류 신청 절차, 건강보험 및 아르바이트 안내', url: '/guides/arc-exchange/' },
          { icon: '🏠', title: 'NCU 기숙사 신청', desc: '기숙사 구역, 시설, 신청 절차 및 외국인 학생 우선 보장 안내', url: '/guides/housing-ncu/' },
          { icon: '🚌', title: 'NCU 버스 가이드', desc: '주요 노선, 자주 가는 목적지 및 실시간 검색 링크', url: '/guides/bus-ncu/' },
          { icon: '⚖️', title: '대만 유학 관련 법규', desc: '입학, 거류, 건강보험, 아르바이트, 학적 관련 중요 법규 안내', url: '/guides/regulations/' },
          { icon: '💼', title: '취업 허가증', desc: '신청 절차, 주당 근무 시간 제한, 위반 시 벌칙 안내', url: '/guides/work-permit/' },
          { icon: '🌱', title: '정신 건강 지원', desc: '상담 센터 예약, 스트레스, 인간관계 고민, 24시간 상담 전화', url: '/guides/mental-health/' },
          { icon: '🏥', title: '의료 정보', desc: '보건센터, 캠퍼스 외 의원, 인근 병원, 응급 및 긴급 전화', url: '/guides/medical/' },
          { icon: '🏆', title: '장학금', desc: '화교 장학금, 경제적 지원, 교내외 각종 신청 가이드', url: '/guides/scholarship/' },
          { icon: '🏥', title: '전민건강보험 신청', desc: 'ARC 발급 후 가입 가능, 외래 진료비 크게 절감', url: '/guides/nhi/' },
          { icon: '🏦', title: '대만에서 은행 계좌 개설', desc: '통일증호 안내, 우체국·대만은행·위수은행 개설 비교', url: '/guides/bank/' },
          { icon: '📱', title: '대만 전화번호 개통', desc: '선불 카드 vs 월정액 요금제, 주요 통신사 안내', url: '/guides/sim/' },
          { icon: '📄', title: '행정 서류', desc: '재학 증명서, 성적 증명서, 추천서 신청 안내', url: '/guides/admin-docs/' },
          { icon: '🗂️', title: '학적 관리', desc: '휴학, 복학, 전과, 복수전공 규정 및 절차', url: '/guides/enrollment/' },
          { icon: '📚', title: '수업 관련 정보', desc: '수강 신청, 수강 추가/취소, 수강 취소 절차 및 일정', url: '/guides/course/' },
          { icon: '🎓', title: '성적 및 졸업 요건', desc: '등급제 GPA, 졸업 학점, 영어 기준(TOEIC) 단과대학별 기준', url: '/guides/graduation/' },
          { icon: '🖥️', title: '교내 시스템', desc: 'Portal 계정 활성화, ee-class 수업 플랫폼, 학생 이메일 설정', url: '/guides/systems/' },
          { icon: '🚨', title: '긴급 연락처', desc: '110 · 119 · 112 · 캠퍼스 보안 · 국제사무처', url: '/guides/emergency/' },
          { icon: '📖', title: '도서관', desc: '대출 규정, 열람실, 학술 데이터베이스, 인쇄 비용', url: '/guides/library/' },
          { icon: '🗺️', title: '지도 및 내비게이션', desc: '학교, 병원, 역, 공항 위치 — 원터치 내비게이션', url: '/guides/map/' },
        ],
      };

      var GUIDES = window.GUIDES_I18N[LANG] || window.GUIDES_I18N['zh-hant'];

      var input = document.getElementById('searchInput');
      var box = document.getElementById('searchBox');
      var dropdown = document.getElementById('searchDropdown');
      var wrap = document.getElementById('searchWrap');
      var activeIdx = -1;
      if (!input) return;

      var NO_RESULT = {
        'zh-hant': '沒有找到相關結果 🔍',
        'en': 'No results found 🔍',
        'id': 'Tidak ada hasil 🔍',
        'ja': '結果が見つかりません 🔍',
        'ms': 'Tiada keputusan 🔍',
        'my': 'ရလဒ်မတွေ့ပါ 🔍',
        'th': 'ไม่พบผลลัพธ์ 🔍',
        'vi': 'Không tìm thấy kết quả 🔍',
        'ko': '검색 결과 없음 🔍',
      };

      function match(q) {
        q = q.trim().toLowerCase();
        if (!q) return [];
        return GUIDES.filter(function (g) {
          return g.title.toLowerCase().indexOf(q) >= 0 ||
            g.desc.toLowerCase().indexOf(q) >= 0;
        });
      }

      function openDropdown() {
        box.classList.add('open');
        dropdown.style.display = 'block';
      }

      function closeDropdown() {
        box.classList.remove('open');
        dropdown.style.display = 'none';
        activeIdx = -1;
      }

      function setActive(idx) {
        var items = dropdown.querySelectorAll('.search-item');
        items.forEach(function (el, i) {
          el.classList.toggle('active', i === idx);
        });
        activeIdx = idx;
      }

      function render(results) {
        activeIdx = -1;
        if (results.length === 0) {
          dropdown.innerHTML = '<div class="search-no-result">' + (NO_RESULT[LANG] || NO_RESULT['en']) + '</div>';
        } else {
          dropdown.innerHTML = results.map(function (r) {
            return '<a href="' + r.url + '" class="search-item">' +
              '<span class="search-item-icon">🔍</span>' +
              '<div class="search-item-body">' +
              '<div class="search-item-title">' + r.icon + ' ' + r.title + '</div>' +
              '<div class="search-item-desc">' + r.desc + '</div>' +
              '</div>' +
              '<span class="search-item-arrow">↗</span>' +
              '</a>';
          }).join('');
        }
        openDropdown();
      }

      input.addEventListener('input', function () {
        var q = this.value;
        if (!q.trim()) { closeDropdown(); return; }
        render(match(q));
      });

      input.addEventListener('focus', function () {
        if (this.value.trim()) render(match(this.value));
      });

      input.addEventListener('keydown', function (e) {
        var items = dropdown.querySelectorAll('.search-item');
        if (e.key === 'ArrowDown') {
          e.preventDefault();
          setActive(Math.min(activeIdx + 1, items.length - 1));
        } else if (e.key === 'ArrowUp') {
          e.preventDefault();
          setActive(Math.max(activeIdx - 1, 0));
        } else if (e.key === 'Enter') {
          e.preventDefault();
          if (activeIdx >= 0 && items[activeIdx]) {
            window.location.href = items[activeIdx].getAttribute('href');
          } else {
            var q = input.value.trim();
            if (q) window.location.href = '/guides/search/?q=' + encodeURIComponent(q);
          }
        } else if (e.key === 'Escape') {
          closeDropdown();
          input.blur();
          collapseSearch();
        }
      });

      document.addEventListener('click', function (e) {
        if (!wrap.contains(e.target)) {
          closeDropdown();
          if (!input.value.trim()) collapseSearch();
        }
      });

      function expandSearch() {
        box.classList.add('expanded');
        setTimeout(function () { input.focus(); }, 50);
      }
      function collapseSearch() {
        if (!input.value.trim()) box.classList.remove('expanded');
      }

      var searchBtn = document.getElementById('searchBtn');
      if (searchBtn) {
        searchBtn.addEventListener('click', function (e) {
          e.stopPropagation();
          if (!box.classList.contains('expanded')) {
            expandSearch();
          } else {
            var q = input.value.trim();
            if (q) window.location.href = '/guides/search/?q=' + encodeURIComponent(q);
            else collapseSearch();
          }
        });
      }

}

/* ════════════════════════════════════════
   18. 導覽列語言切換器
════════════════════════════════════════ */
function toggleLangMenu() {
  var menu = document.getElementById('langMenu');
  var btn  = document.getElementById('langBtn');
  var open = menu.classList.toggle('open');
  btn.classList.toggle('active', open);
  if (open) {
    setTimeout(function () {
      document.addEventListener('click', _closeLangOutside);
    }, 0);
  }
}
function _closeLangOutside(e) {
  var wrap = document.getElementById('langWrap');
  if (wrap && !wrap.contains(e.target)) {
    document.getElementById('langMenu').classList.remove('open');
    document.getElementById('langBtn').classList.remove('active');
    document.removeEventListener('click', _closeLangOutside);
  }
}
function selectLang(code) {
  document.getElementById('langInput').value = code;
  document.getElementById('langForm').submit();
}
