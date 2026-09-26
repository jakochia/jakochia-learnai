(async function () {
  if (!Auth.requireAuth()) return;
  document.getElementById('logout').addEventListener('click', e => { e.preventDefault(); Auth.logout(); });
  const user = Auth.user;
  if (user) document.getElementById('greeting').textContent = 'Good to see you, ' + user.full_name + ' 👋';
  try {
    const a = await api('/api/analytics/overview');
    document.getElementById('stat-time').textContent = fmtMinutes(a.study_time_minutes);
    document.getElementById('stat-questions').textContent = a.questions_answered;
    document.getElementById('stat-avg').textContent = a.quiz_average + '%';
    document.getElementById('stat-streak').textContent = '🔥 ' + a.streak_days;
    document.getElementById('stat-xp').textContent = a.xp.toLocaleString();
    document.getElementById('stat-level').textContent = a.level;
    const subs = document.getElementById('subjects');
    if (!a.subjects.length) subs.innerHTML = '<p class="muted">No subjects yet. Upload a document to begin.</p>';
    else subs.innerHTML = a.subjects.map(s => `
      <div class="mb-16">
        <div class="flex-between mb-8"><strong>${s.name}</strong><span>${s.score}%</span></div>
        <div class="progress"><div class="progress-bar" style="width:${Math.min(100, s.score)}%"></div></div>
      </div>`).join('');
    const ins = document.getElementById('insights');
    ins.innerHTML = `
      <p class="mb-8"><strong>Strongest:</strong> <span class="badge badge-success">${a.insights.strongest_area}</span></p>
      <p class="mb-16"><strong>Needs improvement:</strong> <span class="badge badge-warn">${a.insights.needs_improvement}</span></p>
      <p class="mb-8"><strong>Suggested next steps:</strong></p>
      <ol style="margin-left:20px;">${(a.insights.suggested_next_steps || []).map(s => `<li>${s}</li>`).join('')}</ol>`;
    const docs = await api('/api/documents');
    const docsEl = document.getElementById('docs');
    if (!docs.length) docsEl.innerHTML = '<p class="muted">No documents yet. <a href="upload.html">Upload one</a>.</p>';
    else {
      docsEl.innerHTML = `<table class="table">
        <thead><tr><th>File</th><th>Subject</th><th>Topics</th><th>Difficulty</th><th>Pages</th><th></th></tr></thead>
        <tbody>${docs.map(d => `<tr>
          <td>📄 ${d.filename}</td><td>${d.subject}</td>
          <td>${(d.topics || []).map(t => `<span class="badge">${t}</span>`).join(' ')}</td>
          <td>${d.difficulty}</td><td>${d.page_count}</td>
          <td><button class="btn btn-ghost" data-del="${d.id}">Delete</button></td>
        </tr>`).join('')}</tbody></table>`;
      docsEl.querySelectorAll('[data-del]').forEach(b => {
        b.addEventListener('click', async () => {
          if (!confirm('Delete this document?')) return;
          await api('/api/documents/' + b.dataset.del, { method: 'DELETE' });
          toast('Deleted', 'success'); location.reload();
        });
      });
    }
  } catch (e) { toast(e.message, 'error'); }
})();
