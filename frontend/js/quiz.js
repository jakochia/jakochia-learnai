(async function () {
  if (!Auth.requireAuth()) return;
  document.getElementById('logout').onclick = e => { e.preventDefault(); Auth.logout(); };
  const docs = await api('/api/documents');
  const sel = document.getElementById('doc-select');
  sel.innerHTML = docs.length
    ? docs.map(d => `<option value="${d.id}">${d.filename} — ${d.subject}</option>`).join('')
    : '<option value="">No documents — upload one first</option>';
  let quiz = null, current = 0, answers = [];
  document.getElementById('quiz-form').addEventListener('submit', async e => {
    e.preventDefault();
    const docId = sel.value; if (!docId) return toast('Upload a document first', 'error');
    const btn = document.getElementById('gen-btn');
    btn.disabled = true; btn.textContent = 'Generating…';
    try {
      quiz = await api('/api/quizzes/generate', { method: 'POST', body: {
        document_id: parseInt(docId),
        num_questions: parseInt(document.getElementById('num-q').value),
        difficulty: document.getElementById('q-difficulty').value,
        question_types: ['multiple_choice', 'true_false', 'short_answer']
      }});
      answers = new Array(quiz.questions.length).fill('');
      current = 0;
      document.getElementById('setup-card').classList.add('hidden');
      document.getElementById('quiz-card').classList.remove('hidden');
      document.getElementById('quiz-title').textContent = quiz.title;
      render();
    } catch (err) { toast(err.message, 'error'); }
    finally { btn.disabled = false; btn.textContent = 'Generate Quiz'; }
  });
  function render() {
    const q = quiz.questions[current];
    const area = document.getElementById('question-area');
    document.getElementById('quiz-progress').textContent = (current + 1) + '/' + quiz.questions.length;
    let html = `<p style="font-size:1.15rem;font-weight:600;" class="mb-16">${q.question}</p>`;
    if (q.type === 'multiple_choice' && q.options && q.options.length) {
      html += q.options.map((opt, i) => `<div class="quiz-option ${answers[current] === opt ? 'selected' : ''}" data-opt="${opt.replace(/"/g, '&quot;')}"><strong>${String.fromCharCode(65 + i)}.</strong> ${opt}</div>`).join('');
    } else if (q.type === 'true_false') {
      ['True', 'False'].forEach(opt => {
        html += `<div class="quiz-option ${answers[current] === opt ? 'selected' : ''}" data-opt="${opt}">${opt}</div>`;
      });
    } else {
      html += `<textarea class="textarea" id="short-answer" placeholder="Your answer...">${answers[current] || ''}</textarea>`;
    }
    area.innerHTML = html;
    area.querySelectorAll('.quiz-option').forEach(o => {
      o.addEventListener('click', () => { answers[current] = o.dataset.opt; render(); });
    });
    const sa = document.getElementById('short-answer');
    if (sa) sa.addEventListener('input', () => { answers[current] = sa.value; });
    document.getElementById('prev-btn').disabled = current === 0;
    document.getElementById('next-btn').textContent = current === quiz.questions.length - 1 ? 'Submit' : 'Next →';
  }
  document.getElementById('prev-btn').onclick = () => { if (current > 0) { current--; render(); } };
  document.getElementById('next-btn').onclick = async () => {
    if (current < quiz.questions.length - 1) { current++; render(); return; }
    try {
      const res = await api('/api/quizzes/' + quiz.id + '/submit', { method: 'POST', body: { answers } });
      document.getElementById('quiz-card').classList.add('hidden');
      const rc = document.getElementById('result-card');
      rc.classList.remove('hidden');
      document.getElementById('result-body').innerHTML = `
        <div class="stat-grid mb-24">
          <div><div class="stat-value">${res.score}%</div><div class="stat-label">Score</div></div>
          <div><div class="stat-value">${res.correct}/${res.total}</div><div class="stat-label">Correct</div></div>
        </div>
        ${res.weak_topics.length
          ? '<p class="mb-8"><strong>Weak areas:</strong></p>' + res.weak_topics.map(t => `<span class="badge badge-warn">⚠ ${t}</span>`).join(' ')
          : '<p class="muted">Perfect — no weak areas detected! 🎉</p>'}`;
    } catch (e) { toast(e.message, 'error'); }
  };
})();
