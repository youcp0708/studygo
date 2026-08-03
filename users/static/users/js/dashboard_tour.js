/**
 * users/static/users/js/dashboard_tour.js
 * Dashboard 首次導覽（Spotlight Product Tour）— 通用引擎，不含文案。
 * 文案／是否啟動由 dashboard.html 的 inline script 透過 window.initDashboardTour(config) 傳入。
 */
'use strict';

// 導覽相關的 nav id，用來判斷窄螢幕下是否要強制展開 .site-nav
var TOUR_NAV_IDS = ['tourNavHome', 'tourNavTasks', 'tourNavGuide', 'tourNavAlumni', 'tourNavFaq', 'tourNavReminder', 'tourNavUser'];

function SpotlightTour(steps, opts) {
  this.steps = steps;
  this.opts = opts || {};
  this.index = 0;
  this.els = {};
  this._navForcedOpen = false;
}

SpotlightTour.prototype.start = function () {
  if (!this.steps.length) return;

  // 避免上一頁保持展開的聊天視窗蓋住最後一步要框的 FAB
  this._resetChatWidget();

  this._buildDom();
  this._onReflow = this._reflow.bind(this);
  window.addEventListener('resize', this._onReflow);
  window.addEventListener('scroll', this._onReflow, { passive: true });

  // 有些卡片內容（如任務完成率、待辦任務）是頁面自己非同步載入後才撐開高度，
  // 用 ResizeObserver 盯著目前步驟的 target，內容長高/縮小時自動重新框選，
  // 不然框會停留在「還沒載入完」當下量到的舊尺寸
  if (window.ResizeObserver) {
    this._resizeObserver = new ResizeObserver(this._onReflow);
  }

  this._showStep(0);
};

SpotlightTour.prototype._resetChatWidget = function () {
  var panel = document.getElementById('chatWidgetPanel');
  var widget = document.getElementById('chatWidget');
  if (panel) panel.hidden = true;
  if (widget) widget.classList.remove('open', 'is-full');
  try { sessionStorage.removeItem('chatWidgetState'); } catch (e) { /* ignore */ }
};

SpotlightTour.prototype._buildDom = function () {
  var overlay = document.createElement('div');
  overlay.className = 'tour-overlay';

  var spotlight = document.createElement('div');
  spotlight.className = 'tour-spotlight';

  var popover = document.createElement('div');
  popover.className = 'tour-popover';
  popover.innerHTML =
    '<div class="tour-popover-progress"></div>' +
    '<h4 class="tour-popover-title"></h4>' +
    '<p class="tour-popover-desc"></p>' +
    '<div class="tour-popover-actions">' +
      '<button type="button" class="tour-btn-skip"></button>' +
      '<button type="button" class="tour-btn-next"></button>' +
    '</div>';

  document.body.appendChild(overlay);
  document.body.appendChild(spotlight);
  document.body.appendChild(popover);

  this.els = {
    overlay: overlay,
    spotlight: spotlight,
    popover: popover,
    title: popover.querySelector('.tour-popover-title'),
    desc: popover.querySelector('.tour-popover-desc'),
    progress: popover.querySelector('.tour-popover-progress'),
    skipBtn: popover.querySelector('.tour-btn-skip'),
    nextBtn: popover.querySelector('.tour-btn-next'),
  };

  this.els.skipBtn.textContent = this.opts.skipText || 'Skip';
  this.els.skipBtn.addEventListener('click', this._finish.bind(this));
  this.els.nextBtn.addEventListener('click', this._next.bind(this));
};

/** 多 target 取聯集 bounding box */
SpotlightTour.prototype._unionRect = function (ids) {
  var rects = ids
    .map(function (id) {
      var el = document.getElementById(id);
      return el ? el.getBoundingClientRect() : null;
    })
    .filter(function (r) { return r && (r.width > 0 || r.height > 0); });

  if (!rects.length) return null;

  var left = Math.min.apply(null, rects.map(function (r) { return r.left; }));
  var top = Math.min.apply(null, rects.map(function (r) { return r.top; }));
  var right = Math.max.apply(null, rects.map(function (r) { return r.right; }));
  var bottom = Math.max.apply(null, rects.map(function (r) { return r.bottom; }));

  return { left: left, top: top, right: right, bottom: bottom, width: right - left, height: bottom - top };
};

SpotlightTour.prototype._isNavStep = function (step) {
  return step.targets.some(function (id) { return TOUR_NAV_IDS.indexOf(id) !== -1; });
};

SpotlightTour.prototype._syncMobileNav = function (step) {
  var nav = document.querySelector('.site-nav');
  if (!nav) return;
  var needsOpen = window.innerWidth <= 1024 && this._isNavStep(step);
  if (needsOpen && !nav.classList.contains('open')) {
    nav.classList.add('open');
    this._navForcedOpen = true;
  } else if (!needsOpen && this._navForcedOpen) {
    nav.classList.remove('open');
    this._navForcedOpen = false;
  }
};

SpotlightTour.prototype._showStep = function (i) {
  var step = this.steps[i];
  if (!step) { this._finish(); return; }
  this.index = i;

  this._syncMobileNav(step);

  if (this._resizeObserver) {
    this._resizeObserver.disconnect();
    step.targets.forEach(function (id) {
      var el = document.getElementById(id);
      if (el) this._resizeObserver.observe(el);
    }, this);
  }

  var firstEl = document.getElementById(step.targets[0]);
  if (firstEl) {
    var r = firstEl.getBoundingClientRect();
    var inView = r.top >= 80 && r.bottom <= window.innerHeight;
    if (!inView) firstEl.scrollIntoView({ block: 'center', behavior: 'auto' });
  }

  // 捲動後 layout 可能尚未 settle，用雙層 rAF 延後量測
  var self = this;
  requestAnimationFrame(function () {
    requestAnimationFrame(function () { self._position(step); });
  });
};

SpotlightTour.prototype._position = function (step) {
  var rect = this._unionRect(step.targets);
  if (!rect) { this._next(); return; }  // target 不存在時跳過該步驟，不中斷整個導覽

  var PAD = 8, margin = 16;
  var sp = this.els.spotlight;
  sp.style.left = (rect.left - PAD) + 'px';
  sp.style.top = (rect.top - PAD) + 'px';
  sp.style.width = (rect.width + PAD * 2) + 'px';
  sp.style.height = (rect.height + PAD * 2) + 'px';

  this.els.title.textContent = step.title;
  this.els.desc.textContent = step.desc;
  this.els.progress.textContent = (this.index + 1) + ' / ' + this.steps.length;
  this.els.nextBtn.textContent = (this.index === this.steps.length - 1)
    ? (this.opts.finishText || 'Done')
    : (this.opts.nextText || 'Next');

  var pop = this.els.popover;
  pop.style.visibility = 'hidden';
  var pw = pop.offsetWidth, ph = pop.offsetHeight;
  var spaceBelow = window.innerHeight - (rect.bottom + PAD);
  var spaceAbove = rect.top - PAD;
  var top = (spaceBelow >= ph + margin || spaceBelow >= spaceAbove)
    ? Math.min(rect.bottom + PAD + margin, window.innerHeight - ph - margin)
    : Math.max(rect.top - PAD - margin - ph, margin);
  var left = Math.min(Math.max(rect.left, margin), window.innerWidth - pw - margin);

  pop.style.left = left + 'px';
  pop.style.top = top + 'px';
  pop.style.visibility = 'visible';
};

SpotlightTour.prototype._reflow = function () {
  if (this.steps[this.index]) this._position(this.steps[this.index]);
};

SpotlightTour.prototype._next = function () {
  if (this.index + 1 >= this.steps.length) { this._finish(); return; }
  this._showStep(this.index + 1);
};

SpotlightTour.prototype._finish = function () {
  window.removeEventListener('resize', this._onReflow);
  window.removeEventListener('scroll', this._onReflow);
  if (this._resizeObserver) this._resizeObserver.disconnect();

  var nav = document.querySelector('.site-nav');
  if (nav && this._navForcedOpen) nav.classList.remove('open');

  ['overlay', 'spotlight', 'popover'].forEach(function (k) {
    if (this.els[k] && this.els[k].parentNode) this.els[k].parentNode.removeChild(this.els[k]);
  }, this);

  if (typeof this.opts.onFinish === 'function') this.opts.onFinish();
};

/** dashboard.html 呼叫的進入點 */
window.initDashboardTour = function (config) {
  if (!config || config.hasSeenTour) return;
  if (!config.steps || !config.steps.length) return;

  var tour = new SpotlightTour(config.steps, {
    nextText: config.nextText,
    skipText: config.skipText,
    finishText: config.finishText,
    onFinish: function () {
      if (config.markSeenUrl && typeof apiFetch === 'function') {
        apiFetch(config.markSeenUrl, 'PATCH').catch(function () { /* 靜默失敗，不影響使用者操作 */ });
      }
    },
  });

  setTimeout(function () { tour.start(); }, 400);
};
