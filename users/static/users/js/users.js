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
function confirmAction(type, title, msg, cbName) {
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

  // 儲存 Token
  localStorage.setItem('authToken', data.data.token);

  showToast(`歡迎回來，${data.data.user.name}！`, 'success');

  setTimeout(() => {
    if (data.data.has_profile) {
      window.location.href = '/dashboard/';
    } else {
      window.location.href = '/profile/setup/';
    }
  }, 600);
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
  showToast('帳號建立成功！請填寫個人資料', 'success');
  setTimeout(() => { window.location.href = '/profile/setup/'; }, 800);
}

/* ════════════════════════════════════════
   6. 個人資料設定（Step 2）
   POST /api/users/profile/
   Activity Diagram: 選擇國際/身份別/入學狀態 → 系統產生個人化流程
════════════════════════════════════════ */
async function handleProfileSetup(e) {
  e.preventDefault();
  clearErrors(['nationalityErr', 'universityErr', 'identityErr', 'statusErr']);

  const nationality = document.getElementById('setupNationality').value;
  const university = document.getElementById('setupUniversity').value.trim();
  const identity = document.getElementById('setupIdentity').value;
  const status = document.getElementById('admissionStatusVal').value;

  let ok = true;
  if (!nationality) { showError('nationalityErr', '請選擇國籍'); ok = false; }
  if (!university) { showError('universityErr', '請輸入學校名稱'); ok = false; }
  if (!identity) { showError('identityErr', '請選擇身份別'); ok = false; }
  if (!status) { showError('statusErr', '請選擇入學狀態'); ok = false; }
  if (!ok) return;

  setLoading('setupSubmitBtn', true);

  const body = {
    nationality,
    university,
    identity_type: identity,
    admission_status: status,
    department: document.getElementById('setupDept')?.value || '',
    expected_arrival: document.getElementById('setupArrival')?.value || null,
  };

  const { ok: apiOk, data } = await apiFetch('/api/users/profile/', 'POST', body);

  setLoading('setupSubmitBtn', false);

  if (!apiOk) {
    const msg = data?.errors
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
    nationality: document.getElementById('editNationality').value,
    university: document.getElementById('editUniversity').value.trim(),
    department: document.getElementById('editDept').value.trim(),
    identity_type: document.getElementById('editIdentity').value,
    admission_status: document.getElementById('editStatus').value,
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
    const msg = data?.errors ? Object.values(data.errors).flat().join('、') : data?.message;
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

  const { ok, data } = await apiFetch('/api/users/password-reset/', 'POST', { email });

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
    showToast('帳號已刪除', 'info');
    showPage('loginPage');
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

  const emailVerEl = document.getElementById('emailVerifiedStatus');
  if (emailVerEl) emailVerEl.textContent = user.email_verified ? '已驗證 ✅' : '未驗證（請至信箱確認）';
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
  set('prevUniv', g('setupUniversity')?.value || '—');
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
  // ── Login 頁面：清掉舊 token，啟動輪播後直接結束 ──
  if (document.getElementById('loginPage')) {
    localStorage.removeItem('authToken');
    if (document.querySelectorAll('.login-slide').length > 0) {
      showLoginSlide(0);
      startLoginSlider();
    }
    // 啟動 Google 登入按鈕（GSI 可能尚未載入，用輪詢等待）
    initGoogleSignIn();
    // 顯示 Email 驗證結果通知
    const params = new URLSearchParams(window.location.search);
    const verified = params.get('verified');
    if (verified === '1')        showToast('Email 驗證成功！請登入您的帳號', 'success');
    else if (verified === 'fail')    showToast('驗證連結無效或已使用', 'error');
    else if (verified === 'expired') showToast('驗證連結已過期，請重新申請', 'error');
    return;
  }

  // ── 公開頁面（忘記密碼、重設密碼）：不需要登入，直接結束 ──
  const publicPaths = ['/forgot-password/', '/reset-password/'];
  if (publicPaths.some(p => window.location.pathname.startsWith(p))) {
    return;
  }

  // ── 受保護頁面：驗證 Session（Token 或 Django Session Cookie）──
  const { ok, data } = await apiFetch('/api/users/me/');
  if (!ok) {
    localStorage.removeItem('authToken');
    window.location.href = '/login/';
    return;
  }

  const user = data.data;
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
  const isNew = data.data.is_new_user;
  showToast(isNew ? `帳號已建立，歡迎 ${data.data.user.name}！` : `歡迎回來，${data.data.user.name}！`, 'success');

  setTimeout(() => {
    window.location.href = data.data.has_profile ? '/dashboard/' : '/profile/setup/';
  }, 600);
}

// 啟動
document.addEventListener('DOMContentLoaded', initApp);
