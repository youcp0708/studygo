(function () {
  'use strict';

  const page = document.querySelector('.chatbot-page');
  if (!page) return;

  const endpoints = window.CHATBOT_ENDPOINTS || {};
  const i18n = window.CHATBOT_I18N || {};

  let activeSessionId = page.dataset.sessionId || null;
  let currentAIMode = page.dataset.aiMode || 'helper';

  const AI_MODE_NAMES = {
    helper: i18n.assistantName || 'ReadyTo AI 小幫手',
    friend: i18n.friendName || 'ReadyTo AI 聊天好朋友',
  };

  const AI_MODE_PLACEHOLDERS = {
    helper: '例如：我從緬甸來臺讀學士班，簽證要先準備什麼？',
    friend: '例如：我最近壓力很大，有點想家。',
  };

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
  const cameraInput = document.getElementById('cameraInput');
  const attachmentPreview = document.getElementById('attachmentPreview');
  const micBtn = document.getElementById('micBtn');

  let selectedAttachments = [];

  function t(key, fallback) {
    return i18n[key] || fallback;
  }

  function getCurrentAIName() {
    return AI_MODE_NAMES[currentAIMode] || AI_MODE_NAMES.helper;
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

  function updateAIModeUI() {
  page.classList.remove('ai-mode-helper', 'ai-mode-friend');
  page.classList.add(`ai-mode-${currentAIMode}`);

  document.querySelectorAll('.ai-mode-card').forEach((card) => {
    card.classList.toggle('active', card.dataset.mode === currentAIMode);
  });

  document.querySelectorAll('.js-ai-name').forEach((el) => {
    el.textContent = getCurrentAIName();
  });

  document.querySelectorAll('.js-ai-avatar').forEach((el) => {
    el.classList.remove('helper', 'friend');
    el.classList.add(currentAIMode);
  });

  if (input) {
    input.placeholder = AI_MODE_PLACEHOLDERS[currentAIMode] || AI_MODE_PLACEHOLDERS.helper;
  }
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

  function isNearBottom() {
    if (!messagesEl) return true;

    return (
      messagesEl.scrollHeight -
      messagesEl.scrollTop -
      messagesEl.clientHeight
    ) < 120;
  }

  function updateScrollBottomButton() {
    if (!messagesEl || !scrollBottomBtn) return;

    if (isNearBottom()) {
      scrollBottomBtn.classList.remove('show');
    } else {
      scrollBottomBtn.classList.add('show');
    }
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

  function escapeHtml(text) {
    return String(text || '')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  }

  function renderMessageContent(content) {
    const normalized = normalizeMessageContent(content);
    const safeText = escapeHtml(normalized);

    return safeText
      .replace(
        /\[([^\]]+)\]\((https?:\/\/[^\s)]+|\/[^\s)]+|tel:[^\s)]+)\)/g,
        (_match, label, href) => {
          if (href.startsWith('tel:')) {
            return `<a href="${href}" class="chat-link chat-link--tel">📞 ${label}</a>`;
          }
          return `<a href="${href}" class="chat-link">${label}</a>`;
        }
      )
      .replace(/\n/g, '<br>');
  }

  function renderExistingMessageLinks() {
    if (!messagesEl) return;

    const contents = messagesEl.querySelectorAll('.message-content');

    contents.forEach((el) => {
      if (el.dataset.renderedLinks === 'true') return;

      const rawText = el.textContent || '';

      if (!rawText.includes('](')) return;

      el.innerHTML = renderMessageContent(rawText);
      el.dataset.renderedLinks = 'true';
    });
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

  function typewriterEffect(bodyEl, bubbleEl, content, time, shouldScroll) {
    const normalized = normalizeMessageContent(content);
    let i = 0;
    const speed = 65;

    function tick() {
      if (i < normalized.length) {
        bodyEl.textContent = normalized.slice(0, i + 1);
        i++;
        if (shouldScroll && isNearBottom()) scrollToBottom();
        setTimeout(tick, speed);
      } else {
        bodyEl.innerHTML = renderMessageContent(content);
        bodyEl.dataset.renderedLinks = 'true';
        if (time) {
          const timeEl = document.createElement('div');
          timeEl.className = 'message-time';
          timeEl.textContent = time;
          bubbleEl.appendChild(timeEl);
        }
        if (shouldScroll && isNearBottom()) scrollToBottom();
        updateScrollBottomButton();
      }
    }

    tick();
  }

  function renderAttachmentsInto(bubble, attachments) {
    if (!attachments || attachments.length === 0) return;

    const wrap = document.createElement('div');
    wrap.className = 'message-attachments';

    attachments.forEach((att) => {
      const link = document.createElement('a');
      link.href = att.url;
      link.target = '_blank';
      link.rel = 'noopener';

      if (att.type === 'file') {
        link.className = 'message-attachment-file';
        link.textContent = `📎 ${att.name}`;
      } else {
        const img = document.createElement('img');
        img.src = att.url;
        img.alt = att.name || '';
        img.className = 'message-attachment-image';
        link.appendChild(img);
      }

      wrap.appendChild(link);
    });

    bubble.appendChild(wrap);
  }

  function addMessage(role, content, time, shouldScroll = true, animate = false, attachments = []) {
    if (!messagesEl) return;

    const row = document.createElement('div');
    row.className = `message-row ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'user' ? '🧑' : '🤖';

    if (role !== 'user') {
      avatar.classList.add('js-ai-avatar', currentAIMode);
    }

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';

    if (role !== 'user') {
      const name = document.createElement('div');
      name.className = 'message-name js-ai-name';
      name.textContent = getCurrentAIName();
      bubble.appendChild(name);
    }

    const body = document.createElement('div');
    body.className = 'message-content';

    // Skip typewriter for messages with Markdown links so tel: links render immediately
    const shouldAnimate = animate && role !== 'user' && !content.includes('](');

    if (shouldAnimate) {
      body.textContent = '';
    } else {
      body.innerHTML = renderMessageContent(content);
      body.dataset.renderedLinks = 'true';
    }

    bubble.appendChild(body);
    renderAttachmentsInto(bubble, attachments);

    if (!shouldAnimate && time) {
      const timeEl = document.createElement('div');
      timeEl.className = 'message-time';
      timeEl.textContent = time;
      bubble.appendChild(timeEl);
    }

    row.appendChild(avatar);
    row.appendChild(bubble);
    messagesEl.appendChild(row);

    if (shouldScroll || role === 'user') {
      scrollToBottom();
    } else {
      updateScrollBottomButton();
    }

    if (shouldAnimate) {
      typewriterEffect(body, bubble, content, time, shouldScroll);
    }
  }

  function addTyping() {
    if (!messagesEl) return;

    const row = document.createElement('div');
    row.className = 'message-row assistant';
    row.id = 'typingRow';

    row.innerHTML = `
      <div class="message-avatar js-ai-avatar ${currentAIMode}">🤖</div>
      <div class="message-bubble">
        <div class="message-name js-ai-name">${getCurrentAIName()}</div>
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
        <span>${icon} ${escapeHtml(item.file.name)}</span>
        <button type="button" data-index="${index}">×</button>
      `;

      attachmentPreview.appendChild(chip);
    });
  }

  function addSelectedFiles(fileList, type) {
    Array.from(fileList).forEach((file) => {
      const resolvedType = type === 'file' && file.type.startsWith('image/')
        ? 'image'
        : type;

      selectedAttachments.push({
        file: file,
        type: resolvedType,
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

  const SPEECH_LANG_MAP = {
    'zh-hant': 'zh-TW',
    'zh-hans': 'zh-CN',
    'zh': 'zh-TW',
    'en': 'en-US',
    'my': 'my-MM',
    'th': 'th-TH',
    'ms': 'ms-MY',
    'id': 'id-ID',
    'ja': 'ja-JP',
    'vi': 'vi-VN',
    'ko': 'ko-KR',
  };

  function getSpeechLang() {
    const htmlLang = (document.documentElement.lang || 'zh-hant').toLowerCase();
    return SPEECH_LANG_MAP[htmlLang] || 'zh-TW';
  }

  function setupSpeechRecognition() {
    if (!micBtn || !input) return;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      micBtn.style.display = 'none';
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;

    let isRecording = false;
    let baseText = '';

    recognition.addEventListener('start', function () {
      isRecording = true;
      baseText = input.value;
      micBtn.classList.add('recording');
    });

    recognition.addEventListener('result', function (event) {
      let finalText = '';
      let interimText = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalText += transcript;
        } else {
          interimText += transcript;
        }
      }

      if (finalText) {
        baseText = `${baseText}${finalText}`.trim() + ' ';
      }

      input.value = (baseText + interimText).slice(0, 1200);
      updateCount();
    });

    recognition.addEventListener('error', function () {
      isRecording = false;
      micBtn.classList.remove('recording');
    });

    recognition.addEventListener('end', function () {
      isRecording = false;
      micBtn.classList.remove('recording');
    });

    micBtn.addEventListener('click', function () {
      if (isRecording) {
        recognition.stop();
        return;
      }

      recognition.lang = getSpeechLang();

      try {
        recognition.start();
      } catch (error) {
        isRecording = false;
        micBtn.classList.remove('recording');
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

  function buildHistoryItem(sessionId, title, isPinned, aiMode) {
    const item = document.createElement('div');
    item.className = `chat-history-item active${isPinned ? ' pinned' : ''}`;
    item.dataset.sessionId = sessionId;
    item.dataset.aiMode = aiMode || currentAIMode;

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

  function addOrUpdateHistoryItem(sessionId, title, isPinned, aiMode) {
    if (!historyList) return;

    const empty = historyList.querySelector('.history-empty');
    if (empty) {
      empty.remove();
    }

    let item = historyList.querySelector(
      `.chat-history-item[data-session-id="${sessionId}"]`
    );

    if (!item) {
      item = buildHistoryItem(sessionId, title, isPinned, aiMode);
      historyList.prepend(item);
    }

    item.dataset.aiMode = aiMode || currentAIMode;
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

    const attachmentsForDisplay = selectedAttachments.map((item) => ({
      type: item.type,
      url: URL.createObjectURL(item.file),
      name: item.file.name,
    }));

    if (message) {
      addMessage('user', message, null, true, false, attachmentsForDisplay);
    } else {
      addMessage('user', t('uploadedAttachment', '已上傳附件'), null, true, false, attachmentsForDisplay);
    }

    input.value = '';
    updateCount();

    addTyping();
    setBusy(true);

    try {
      const formData = new FormData();

      formData.append('message', message || t('uploadedAttachment', '已上傳附件'));
      formData.append('ai_mode', currentAIMode);

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
        data.data.is_pinned,
        data.data.ai_mode || currentAIMode
      );

      if (isNewSession && endpoints.page) {
        window.history.replaceState(
          {},
          '',
          `${endpoints.page}?session=${activeSessionId}`
        );
      }

      const assistantMessages = data.data.assistant_messages || [];

      if (assistantMessages.length > 0) {
        assistantMessages.forEach((msg, index) => {
          setTimeout(() => {
            addMessage(
              'assistant',
              msg.content,
              msg.created_at,
              shouldAutoScrollAfterReply,
              true
            );
          }, index * 2000);
        });
      } else if (data.data.assistant_message) {
        addMessage(
          'assistant',
          data.data.assistant_message.content,
          data.data.assistant_message.created_at,
          shouldAutoScrollAfterReply,
          true
        );
      }

      selectedAttachments = [];
      renderAttachmentPreview();

    } catch (error) {
      removeTyping();

      addMessage(
        'assistant',
        t('networkError', '網路或伺服器發生錯誤，請稍後再試。'),
        null,
        isNearBottom()
      );
    } finally {
      setBusy(false);
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

    const result = await requestJSON(endpoints.createSession, 'POST', {
      ai_mode: currentAIMode,
    });

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
        window.location.href = `${endpoints.page}?ai_mode=${currentAIMode}`;
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

  function setupAIModeSwitcher() {
    const modeCards = document.querySelectorAll('.ai-mode-card');

    if (!modeCards.length) return;

    modeCards.forEach((card) => {
      card.addEventListener('click', function () {
        const mode = this.dataset.mode || 'helper';

        if (!['helper', 'friend'].includes(mode)) return;

        if (mode !== currentAIMode && endpoints.page) {
          window.location.href = `${endpoints.page}?ai_mode=${mode}`;
          return;
        }

        currentAIMode = mode;
        page.dataset.aiMode = mode;
        updateAIModeUI();
      });
    });

    updateAIModeUI();
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
  setupSpeechRecognition();
  setupHistorySearch();
  setupTaiwanTipRotator();
  setupAIModeSwitcher();
  renderExistingMessageLinks();
  updateCount();
  scrollToBottom();
  updateScrollBottomButton();
})();