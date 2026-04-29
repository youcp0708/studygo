// chatbot/static/chatbot/js/chatbot.js

(function () {
  'use strict';

  const page = document.querySelector('.chatbot-page');
  if (!page) return;

  let activeSessionId = page.dataset.sessionId || null;
  const endpoints = window.CHATBOT_ENDPOINTS || {};
  const messagesEl = document.getElementById('chatMessages');
  const form = document.getElementById('chatForm');
  const input = document.getElementById('chatInput');
  const sendBtn = document.getElementById('sendChatBtn');
  const clearBtn = document.getElementById('clearChatBtn');
  const charCount = document.getElementById('charCount');

  function getCookie(name) {
    for (const cookie of document.cookie.split(';')) {
      const c = cookie.trim();
      if (c.startsWith(name + '=')) return decodeURIComponent(c.slice(name.length + 1));
    }
    return '';
  }

  async function requestJSON(url, method, body) {
    const options = {
      method,
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      },
      credentials: 'same-origin',
    };
    if (body) options.body = JSON.stringify(body);
    const response = await fetch(url, options);
    const data = await response.json().catch(() => ({}));
    return { ok: response.ok, data };
  }

  function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function addMessage(role, content, time) {
    const row = document.createElement('div');
    row.className = `message-row ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = role === 'user' ? '🧑' : '🤖';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';

    const name = document.createElement('div');
    name.className = 'message-name';
    name.textContent = role === 'user' ? '我' : 'StudyGo AI 小幫手';

    const body = document.createElement('div');
    body.className = 'message-content';
    body.textContent = content;

    bubble.appendChild(name);
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
    scrollToBottom();
    return row;
  }

  function addTyping() {
    const row = document.createElement('div');
    row.className = 'message-row assistant';
    row.id = 'typingRow';
    row.innerHTML = `
      <div class="message-avatar">🤖</div>
      <div class="message-bubble">
        <div class="message-name">StudyGo AI 小幫手</div>
        <div class="typing-dots"><span></span><span></span><span></span></div>
      </div>
    `;
    messagesEl.appendChild(row);
    scrollToBottom();
  }

  function removeTyping() {
    document.getElementById('typingRow')?.remove();
  }

  function setBusy(isBusy) {
    sendBtn.disabled = isBusy;
    input.disabled = isBusy;
    sendBtn.textContent = isBusy ? '回覆中…' : '送出';
  }

  async function loadHistory() {
    if (!endpoints.history) return;
    const { ok, data } = await requestJSON(endpoints.history, 'GET');
    if (!ok || !data?.data?.messages?.length) return;

    activeSessionId = data.data.session_id || activeSessionId;
    messagesEl.innerHTML = '';
    data.data.messages.forEach((msg) => addMessage(msg.role, msg.content, msg.created_at));
  }

  async function sendMessage(text) {
    const message = text.trim();
    if (!message) return;

    addMessage('user', message);
    input.value = '';
    updateCount();
    addTyping();
    setBusy(true);

    try {
      const { ok, data } = await requestJSON(endpoints.message, 'POST', {
        message,
        session_id: activeSessionId,
      });
      removeTyping();

      if (!ok || !data.success) {
        addMessage('assistant', data?.message || '送出失敗，請稍後再試。');
        return;
      }

      activeSessionId = data.data.session_id;
      addMessage(
        'assistant',
        data.data.assistant_message.content,
        data.data.assistant_message.created_at
      );
    } catch (err) {
      removeTyping();
      addMessage('assistant', '網路或伺服器發生錯誤，請確認 Django 後端是否正在執行。');
    } finally {
      setBusy(false);
      input.focus();
    }
  }

  function updateCount() {
    charCount.textContent = `${input.value.length} / 1200`;
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    sendMessage(input.value);
  });

  input.addEventListener('input', updateCount);

  input.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      form.requestSubmit();
    }
  });

  document.querySelectorAll('.quick-question').forEach((btn) => {
    btn.addEventListener('click', () => {
      input.value = btn.dataset.question || '';
      updateCount();
      input.focus();
    });
  });

  clearBtn.addEventListener('click', async () => {
    if (!confirm('確定要清除你的聊天紀錄嗎？')) return;
    const { ok } = await requestJSON(endpoints.clear, 'DELETE');
    if (ok) {
      activeSessionId = null;
      messagesEl.innerHTML = '';
      addMessage('assistant', '聊天紀錄已清除。你可以重新開始提問。');
    } else {
      addMessage('assistant', '清除失敗，請稍後再試。');
    }
  });

  updateCount();
  loadHistory();
})();
