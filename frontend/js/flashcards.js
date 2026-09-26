(async function () {
  if (!Auth.requireAuth()) return;
  document.getElementById('logout').onclick = e => { e.preventDefault(); Auth.logout(); };
  const docs = await api('/api/documents');
  const sel = document.getElementById('doc-select');
  sel.innerHTML = docs.length
    ? docs.map(d => `<option value="${d.id}">${d.filename}</option>`).join('')
    : '<option value="">No documents</option>';
  let cards = [], idx = 0;
  const fc = document.getElementById('fc');
  const front = document.getElementById('fc-front');
  const back = document.getElementById('fc-back');
  const counter = document.getElementById('counter');
  const ratings = document.getElementById('ratings');
  fc.addEventListener('click', () => fc.classList.toggle('flipped'));
  function show() {
    if (!cards.length) return;
    fc.classList.remove('flipped');
    const c = cards[idx];
    front.textContent = c.front;
    back.textContent = c.back;
    counter.textContent = (idx + 1) + '/' + cards.length;
    ratings.innerHTML = `
      <button class="btn btn-ghost" data-r="0">😵 Again</button>
      <button class="btn btn-ghost" data-r="1">😐 Hard</button>
      <button class="btn btn-ghost" data-r="2">🙂 Good</button>
      <button class="btn btn-ghost" data-r="3">🔥 Easy</button>`;
    ratings.querySelectorAll('[data-r]').forEach(b => {
      b.addEventListener('click', async ev => {
        ev.stopPropagation();
        try { await api('/api/flashcards/' + cards[idx].id + '/review', { method: 'POST', body: { rating: parseInt(b.dataset.r) } }); } catch {}
        idx = (idx + 1) % cards.length;
        show();
      });
    });
  }
  document.getElementById('gen-form').addEventListener('submit', async e => {
    e.preventDefault();
    const docId = sel.value; if (!docId) return toast('Upload a document first', 'error');
    const btn = document.getElementById('gen-btn');
    btn.disabled = true; btn.textContent = 'Generating…';
    try {
      cards = await api('/api/flashcards/generate', { method: 'POST', body: {
        document_id: parseInt(docId), count: parseInt(document.getElementById('count').value)
      }});
      if (!cards.length) throw new Error('No cards generated');
      idx = 0; show();
      toast(cards.length + ' cards ready', 'success');
    } catch (err) { toast(err.message, 'error'); }
    finally { btn.disabled = false; btn.textContent = 'Generate Flashcards'; }
  });
})();
