(async function () {
  if (!Auth.requireAuth()) return;
  document.getElementById('logout').onclick = e => { e.preventDefault(); Auth.logout(); };
  const win = document.getElementById('chat-window');
  const form = document.getElementById('chat-form');
  const input = document.getElementById('question');
  const btn = document.getElementById('send-btn');
  function add(role, text, sources) {
    const div = document.createElement('div');
    div.className = 'message ' + role;
    div.textContent = text;
    if (sources && sources.length) {
      const src = document.createElement('div');
      src.className = 'source-tag';
      src.innerHTML = '📚 Sources:<br>' + sources.map(s =>
        '📄 ' + s.filename + ' — page ' + s.page + (s.section ? ' · ' + s.section : '')
      ).join('<br>');
      div.appendChild(src);
    }
    win.appendChild(div);
    win.scrollTop = win.scrollHeight;
  }
  form.addEventListener('submit', async e => {
    e.preventDefault();
    const q = input.value.trim(); if (!q) return;
    add('user', q); input.value = '';
    btn.disabled = true; btn.textContent = 'Thinking…';
    try {
      const res = await api('/api/chat', { method: 'POST', body: {
        question: q, difficulty: document.getElementById('difficulty').value
      }});
      add('ai', res.answer, res.sources);
    } catch (e) { add('ai', '⚠️ ' + e.message); }
    finally { btn.disabled = false; btn.textContent = 'Send'; input.focus(); }
  });
})();
