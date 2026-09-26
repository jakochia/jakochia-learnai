(async function () {
  if (!Auth.requireAuth()) return;
  document.getElementById('logout').onclick = e => { e.preventDefault(); Auth.logout(); };
  const card = document.getElementById('plan-card');
  function render(plan, subject, exam) {
    if (!plan || !plan.length) { card.innerHTML = '<p class="muted">No plan generated.</p>'; return; }
    card.innerHTML = `
      <h3 class="mb-8">${subject} — exam ${exam}</h3>
      <p class="muted mb-24">${plan.length}-week plan</p>
      ${plan.map(w => `
        <div class="mb-24">
          <h4>Week ${w.week}: ${w.focus || ''}</h4>
          ${w.topics && w.topics.length ? `<p class="mb-8"><strong>Topics:</strong> ${w.topics.map(t => `<span class="badge">${t}</span>`).join(' ')}</p>` : ''}
          ${w.tasks && w.tasks.length ? `<ul style="margin-left:20px;">${w.tasks.map(t => `<li>${t}</li>`).join('')}</ul>` : ''}
        </div>`).join('')}`;
  }
  try {
    const latest = await api('/api/planner/latest');
    if (latest.plan) render(latest.plan, latest.subject, latest.exam_date);
  } catch {}
  document.getElementById('plan-form').addEventListener('submit', async e => {
    e.preventDefault();
    const btn = document.getElementById('gen-btn');
    btn.disabled = true; btn.textContent = 'Planning…';
    try {
      const res = await api('/api/planner/generate', { method: 'POST', body: {
        subject: document.getElementById('subject').value,
        exam_date: document.getElementById('exam').value,
        hours_per_day: parseFloat(document.getElementById('hours').value)
      }});
      render(res.plan, res.subject, res.exam_date);
      toast('Plan ready', 'success');
    } catch (err) { toast(err.message, 'error'); }
    finally { btn.disabled = false; btn.textContent = 'Generate Plan'; }
  });
})();
