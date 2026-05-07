(function () {
  'use strict';

  const page = document.querySelector('.chatbot-page');
  if (!page) return;

  let activeSessionId = page.dataset.sessionId || null;

  const endpoints = window.CHATBOT_ENDPOINTS || {};
  const i18n = window.CHATBOT_I18N || {};

  const messagesEl = document.getElementById('chatMessages');
  const scrollBottomBtn = document.getElementById('scrollBottomBtn');
  const form = document.getElementById('chatForm');
  const input = document.getElementById('chatInput');
  const sendBtn = document.getElementById('sendChatBtn');
  const charCount = document.getElementById('charCount');
  const newChatBtn = document.getElementById('newChatBtn');
  const historyList = document.getElementById('chatHistoryList');
  const historySearchInput = document.getElementById('historySearchInput');

  const attachToggleBtn = document.getElementById('attachToggleBtn');
  const attachMenu = document.getElementById('attachMenu');
  const fileInput = document.getElementById('fileInput');
  const imageInput = document.getElementById('imageInput');
  const cameraInput = document.getElementById('cameraInput');
  const attachmentPreview = document.getElementById('attachmentPreview');

  let selectedAttachments = [];

  function t(key, fallback) {
    return i18n[key] || fallback;
  }

  function getCookie(name) {
    for (const cookie of document.cookie.split(';')) {
      const c = cookie.trim();
      if (c.startsWith(name + '=')) {
        return decodeURIComponent(c.slice(name.length + 1));
      }
    }
    return '';
  }

  async function requestJSON(url, method, body) {
    const options = {
      method: method,
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      },
      credentials: 'same-origin',
    };

    if (body) {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(url, options);
    const data = await response.json().catch(() => ({}));

    return {
      ok: response.ok,
      data: data,
    };
  }

  function scrollToBottom() {
    if (!messagesEl) return;
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function updateScrollBottomButton() {
    if (!messagesEl || !scrollBottomBtn) return;

    if (isNearBottom()) {
      scrollBottomBtn.classList.remove('show');
    } else {
      scrollBottomBtn.classList.add('show');
    }
  }

  function isNearBottom() {
    if (!messagesEl) return true;

    return (
      messagesEl.scrollHeight -
      messagesEl.scrollTop -
      messagesEl.clientHeight
    ) < 120;
  }

  function normalizeMessageContent(content) {
    if (!content) return '';

    return String(content)
      .replace(/\r\n/g, '\n')
      .split('\n')
      .map((line) => line.trim())
      .join('\n')
      .replace(/\n{3,}/g, '\n\n')
      .trim();
  }

  function updateCount() {
    if (!charCount || !input) return;
    charCount.textContent = `${input.value.length} / 1200`;
  }

  function clearWelcomeIfNeeded() {
    if (!messagesEl) return;

    const welcome = messagesEl.querySelector('.welcome-message');
    if (welcome) {
      welcome.remove();
    }
  }

  function addMessage(role, content, time, shouldScroll = true) {
    if (!messagesEl) return;

    const row = document.createElement('div');
    row.className = `message-row ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'user' ? '🧑' : '🤖';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';

    //const name = document.createElement('div');
    //name.className = 'message-name';
    //name.textContent = role === 'user'
    //? t('me', '我')
    //: t('assistantName', 'StudyGo AI 小幫手');
    if (role !== 'user') {
      const name = document.createElement('div');
      name.className = 'message-name';
      name.textContent = t('assistantName', 'StudyGo AI 小幫手');
      bubble.appendChild(name);
    }

    const body = document.createElement('div');
    body.className = 'message-content';
    body.textContent = normalizeMessageContent(content);

    //bubble.appendChild(name);
    bubble.appendChild(body);

    if (time) {
      const timeEl = document.createElement('div');
      timeEl.className = 'message-time';
      timeEl.textContent = time;
      bubble.appendChild(timeEl);
    }

    row.appendChild(avatar);
    row.appendChild(bubble);
    messagesEl.appendChild(row);


    if (role === 'user') {
      scrollToBottom();
    } else {
      updateScrollBottomButton();
    }

  }

  function addTyping() {
    if (!messagesEl) return;

    const row = document.createElement('div');
    row.className = 'message-row assistant';
    row.id = 'typingRow';

    row.innerHTML = `
      <div class="message-avatar">🤖</div>
      <div class="message-bubble">
       <!--<div class="message-name">${t('assistantName', 'StudyGo AI 小幫手')}</div>-->
        <div class="typing-dots">
          <span></span>
          <span></span>
          <span></span>
        </div>
      </div>
    `;

    messagesEl.appendChild(row);

    if (isNearBottom()) {
      scrollToBottom();
    }

    updateScrollBottomButton();

    // 不在這裡自動捲到底，避免你正在看前面訊息時被拉走
    // scrollToBottom();
  }

  function removeTyping() {
    const typingRow = document.getElementById('typingRow');
    if (typingRow) {
      typingRow.remove();
    }
  }

  function setBusy(isBusy) {
    if (!sendBtn || !input) return;

    sendBtn.disabled = isBusy;
    input.disabled = isBusy;
    sendBtn.textContent = isBusy
      ? t('replyLoading', '回覆中…')
      : t('send', '送出');
  }

  function renderAttachmentPreview() {
    if (!attachmentPreview) return;

    attachmentPreview.innerHTML = '';

    selectedAttachments.forEach((item, index) => {
      const chip = document.createElement('div');
      chip.className = 'attachment-chip';

      let icon = '📎';
      if (item.type === 'image') icon = '🖼️';
      if (item.type === 'camera') icon = '📷';

      chip.innerHTML = `
        <span>${icon} ${item.file.name}</span>
        <button type="button" data-index="${index}">×</button>
      `;

      attachmentPreview.appendChild(chip);
    });
  }

  function addSelectedFiles(fileList, type) {
    Array.from(fileList).forEach((file) => {
      selectedAttachments.push({
        file: file,
        type: type,
      });
    });

    renderAttachmentPreview();
  }

  function setupAttachmentButtons() {
    if (!attachToggleBtn || !attachMenu) return;

    attachToggleBtn.addEventListener('click', function (event) {
      event.preventDefault();
      event.stopPropagation();
      attachMenu.classList.toggle('open');
    });

    attachMenu.addEventListener('click', function (event) {
      const btn = event.target.closest('button[data-upload-type]');
      if (!btn) return;

      const type = btn.dataset.uploadType;

      if (type === 'file' && fileInput) {
        fileInput.click();
      }

      if (type === 'image' && imageInput) {
        imageInput.click();
      }

      if (type === 'camera' && cameraInput) {
        cameraInput.click();
      }

      attachMenu.classList.remove('open');
    });

    if (fileInput) {
      fileInput.addEventListener('change', function () {
        addSelectedFiles(fileInput.files, 'file');
        fileInput.value = '';
      });
    }

    if (imageInput) {
      imageInput.addEventListener('change', function () {
        addSelectedFiles(imageInput.files, 'image');
        imageInput.value = '';
      });
    }

    if (cameraInput) {
      cameraInput.addEventListener('change', function () {
        addSelectedFiles(cameraInput.files, 'camera');
        cameraInput.value = '';
      });
    }

    if (attachmentPreview) {
      attachmentPreview.addEventListener('click', function (event) {
        const btn = event.target.closest('button[data-index]');
        if (!btn) return;

        const index = Number(btn.dataset.index);
        selectedAttachments.splice(index, 1);
        renderAttachmentPreview();
      });
    }

    document.addEventListener('click', function (event) {
      if (
        !event.target.closest('.attach-menu') &&
        !event.target.closest('.attach-toggle-btn')
      ) {
        attachMenu.classList.remove('open');
      }
    });
  }

  function setupHistorySearch() {
    if (!historySearchInput || !historyList) return;

    historySearchInput.addEventListener('input', function () {
      const keyword = this.value.trim().toLowerCase();
      const items = historyList.querySelectorAll('.chat-history-item');

      items.forEach((item) => {
        const textEl = item.querySelector('.history-text');
        const text = textEl ? textEl.textContent.trim().toLowerCase() : '';

        item.style.display = !keyword || text.includes(keyword) ? '' : 'none';
      });
    });
  }

  function setActiveHistoryItem(sessionId) {
    document.querySelectorAll('.chat-history-item').forEach((item) => {
      item.classList.toggle(
        'active',
        String(item.dataset.sessionId) === String(sessionId)
      );
    });
  }

  function buildHistoryItem(sessionId, title, isPinned) {
    const item = document.createElement('div');
    item.className = `chat-history-item active${isPinned ? ' pinned' : ''}`;
    item.dataset.sessionId = sessionId;

    item.innerHTML = `
      <a class="history-title" href="${endpoints.page}?session=${sessionId}">
        <span class="pin-mark">${isPinned ? '📌' : ''}</span>
        <span class="history-text"></span>
      </a>

      <button class="history-more-btn" type="button" aria-label="chat menu">⋯</button>

      <div class="history-menu">
        <button type="button" class="pin-chat">${isPinned ? t('unpin', '取消釘選') : t('pin', '釘選')}</button>
        <button type="button" class="rename-chat">${t('rename', '重新命名')}</button>
        <button type="button" class="delete-chat">${t('delete', '刪除')}</button>
      </div>
    `;

    item.querySelector('.history-text').textContent = title || t('newChat', '新的聊天');
    return item;
  }

  function addOrUpdateHistoryItem(sessionId, title, isPinned) {
    if (!historyList) return;

    const empty = historyList.querySelector('.history-empty');
    if (empty) {
      empty.remove();
    }

    let item = historyList.querySelector(
      `.chat-history-item[data-session-id="${sessionId}"]`
    );

    if (!item) {
      item = buildHistoryItem(sessionId, title, isPinned);
      historyList.prepend(item);
    }

    item.querySelector('.history-text').textContent = title || t('newChat', '新的聊天');
    item.querySelector('.pin-mark').textContent = isPinned ? '📌' : '';
    item.querySelector('.pin-chat').textContent = isPinned
      ? t('unpin', '取消釘選')
      : t('pin', '釘選');

    item.classList.toggle('pinned', Boolean(isPinned));

    if (isPinned) {
      historyList.prepend(item);
    }

    setActiveHistoryItem(sessionId);
  }

  async function sendMessage(text) {
    const message = text.trim();

    if (!message && selectedAttachments.length === 0) {
      return;
    }

    if (!endpoints.message) {
      alert(t('missingMessageApi', '找不到 message API'));
      return;
    }

    const isNewSession = !activeSessionId;

    clearWelcomeIfNeeded();

    if (message) {
      addMessage('user', message, null, true);
    } else {
      addMessage('user', t('uploadedAttachment', '已上傳附件'), null, true);
    }

    input.value = '';
    updateCount();

    addTyping();
    setBusy(true);

    try {
      const formData = new FormData();

      formData.append('message', message || t('uploadedAttachment', '已上傳附件'));

      if (activeSessionId) {
        formData.append('session_id', activeSessionId);
      }

      selectedAttachments.forEach((item) => {
        formData.append('attachments', item.file);
        formData.append('attachment_types', item.type);
      });

      const response = await fetch(endpoints.message, {
        method: 'POST',
        headers: {
          'X-CSRFToken': getCookie('csrftoken'),
        },
        credentials: 'same-origin',
        body: formData,
      });

      const data = await response.json().catch(() => ({}));

      const shouldAutoScrollAfterReply = isNearBottom();

      removeTyping();

      if (!response.ok || !data.success) {
        addMessage(
          'assistant',
          data.message || t('sendFailed', '送出失敗，請稍後再試。'),
          null,
          shouldAutoScrollAfterReply
        );
        return;
      }

      activeSessionId = data.data.session_id;
      page.dataset.sessionId = activeSessionId;

      addOrUpdateHistoryItem(
        activeSessionId,
        data.data.session_title,
        data.data.is_pinned
      );

      if (isNewSession && endpoints.page) {
        window.history.replaceState(
          {},
          '',
          `${endpoints.page}?session=${activeSessionId}`
        );
      }

      addMessage(
        'assistant',
        data.data.assistant_message.content,
        data.data.assistant_message.created_at,
        shouldAutoScrollAfterReply
      );

      selectedAttachments = [];
      renderAttachmentPreview();

    } catch (error) {
      const shouldAutoScrollAfterReply = isNearBottom();

      removeTyping();

      addMessage(
        'assistant',
        t('networkError', '網路或伺服器發生錯誤，請稍後再試。'),
        null,
        shouldAutoScrollAfterReply
      );
    } finally {
      setBusy(false);

      // 不自動 focus，避免 AI 回答完成後畫面被拉到輸入框
      // input.focus();
    }
  }

  function closeAllHistoryMenus(exceptItem = null) {
    document.querySelectorAll('.chat-history-item.menu-open').forEach((item) => {
      if (item !== exceptItem) {
        item.classList.remove('menu-open');
      }
    });
  }

  async function createNewSession() {
    if (!endpoints.createSession) return;

    const result = await requestJSON(endpoints.createSession, 'POST');

    if (!result.ok || !result.data.success) {
      alert(result.data.message || t('createChatFailed', '建立新聊天失敗'));
      return;
    }

    window.location.href = `${endpoints.page}?session=${result.data.data.session_id}`;
  }

  async function renameSession(item) {
    const sessionId = item.dataset.sessionId;
    const titleEl = item.querySelector('.history-text');
    const oldTitle = titleEl.textContent.trim();

    const newTitle = prompt(t('renamePrompt', '請輸入新的聊天名稱'), oldTitle);

    if (!newTitle || !newTitle.trim()) {
      item.classList.remove('menu-open');
      return;
    }

    const result = await requestJSON(endpoints.renameSession, 'POST', {
      session_id: sessionId,
      title: newTitle.trim(),
    });

    if (!result.ok || !result.data.success) {
      alert(result.data.message || t('renameFailed', '重新命名失敗'));
      return;
    }

    titleEl.textContent = result.data.data.title;
    item.classList.remove('menu-open');
  }

  async function togglePinSession(item) {
    const sessionId = item.dataset.sessionId;

    const result = await requestJSON(endpoints.pinSession, 'POST', {
      session_id: sessionId,
    });

    if (!result.ok || !result.data.success) {
      alert(t('pinFailed', '釘選失敗'));
      return;
    }

    const isPinned = result.data.data.is_pinned;

    item.classList.toggle('pinned', isPinned);
    item.querySelector('.pin-mark').textContent = isPinned ? '📌' : '';
    item.querySelector('.pin-chat').textContent = isPinned
      ? t('unpin', '取消釘選')
      : t('pin', '釘選');

    if (isPinned && historyList) {
      historyList.prepend(item);
    }

    item.classList.remove('menu-open');
  }

  async function deleteSession(item) {
    const sessionId = item.dataset.sessionId;

    const result = await requestJSON(endpoints.deleteSession, 'DELETE', {
      session_id: sessionId,
    });

    if (!result.ok || !result.data.success) {
      alert(result.data.message || t('deleteFailed', '刪除失敗'));
      return;
    }

    const wasActive = String(activeSessionId) === String(sessionId);

    item.remove();

    if (wasActive) {
      const nextSessionId = result.data.data.next_session_id;

      if (nextSessionId) {
        window.location.href = `${endpoints.page}?session=${nextSessionId}`;
      } else {
        window.location.href = endpoints.page;
      }
    }
  }

  function setupHistoryMenu() {
    document.addEventListener('click', async function (event) {
      const moreBtn = event.target.closest('.history-more-btn');
      const menuBtn = event.target.closest('.history-menu button');
      const titleLink = event.target.closest('.history-title');

      if (moreBtn) {
        event.preventDefault();
        event.stopPropagation();

        const item = moreBtn.closest('.chat-history-item');
        const isOpen = item.classList.contains('menu-open');

        closeAllHistoryMenus(item);
        item.classList.toggle('menu-open', !isOpen);
        return;
      }

      if (menuBtn) {
        event.preventDefault();
        event.stopPropagation();

        const item = menuBtn.closest('.chat-history-item');

        if (menuBtn.classList.contains('rename-chat')) {
          await renameSession(item);
          return;
        }

        if (menuBtn.classList.contains('pin-chat')) {
          await togglePinSession(item);
          return;
        }

        if (menuBtn.classList.contains('delete-chat')) {
          await deleteSession(item);
          return;
        }
      }

      if (titleLink) {
        closeAllHistoryMenus();
        return;
      }

      closeAllHistoryMenus();
    });
  }

  function setupTaiwanTipRotator() {
    const tipText = document.getElementById('botTipText');
    const tipsData = document.getElementById('taiwanTipsData');

    if (!tipText || !tipsData) return;

    let tips = [];

    try {
      tips = JSON.parse(tipsData.textContent);
    } catch (error) {
      tips = [];
    }

    if (!Array.isArray(tips) || tips.length <= 1) return;

    let index = 0;

    setInterval(function () {
      index = (index + 1) % tips.length;
      tipText.textContent = tips[index];
    }, 9000);
  }

  if (form) {
    form.addEventListener('submit', function (event) {
      event.preventDefault();
      if (!input) return;
      sendMessage(input.value);
    });
  }

  if (input) {
    input.addEventListener('input', updateCount);

    input.addEventListener('keydown', function (event) {
      if (event.isComposing) return;

      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();

        if (form && form.requestSubmit) {
          form.requestSubmit();
        } else if (form) {
          form.dispatchEvent(new Event('submit', {
            bubbles: true,
            cancelable: true
          }));
        }
      }
    });
  }

  if (newChatBtn) {
    newChatBtn.addEventListener('click', createNewSession);
  }

  if (scrollBottomBtn) {
    scrollBottomBtn.addEventListener('click', function () {
      scrollToBottom();
      updateScrollBottomButton();
    });
  }

  if (messagesEl) {
    messagesEl.addEventListener('scroll', updateScrollBottomButton);
  }

  setupHistoryMenu();
  setupAttachmentButtons();
  setupHistorySearch();
  setupTaiwanTipRotator();
  updateCount();
  scrollToBottom();
  updateScrollBottomButton();
})();