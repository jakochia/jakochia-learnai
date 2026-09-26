(async function () {
  if (!Auth.requireAuth()) return;
  document.getElementById('logout').onclick = e => { e.preventDefault(); Auth.logout(); };
  async function loadDocs() {
    const docs = await api('/api/documents');
    const el = document.getElementById('docs');
    if (!docs.length) { el.innerHTML = '<p class="muted">No documents yet.</p>'; return; }
    el.innerHTML = `<table class="table">
      <thead><tr><th>File</th><th>Subject</th><th>Topics</th><th>Pages</th></tr></thead>
      <tbody>${docs.map(d => `<tr>
        <td>📄 ${d.filename}</td><td>${d.subject}</td>
        <td>${(d.topics || []).map(t => `<span class="badge">${t}</span>`).join(' ')}</td>
        <td>${d.page_count}</td></tr>`).join('')}</tbody></table>`;
  }
  document.getElementById('upload-form').addEventListener('submit', async e => {
    e.preventDefault();
    const fileInput = document.getElementById('file');
    if (!fileInput.files.length) return;
    const btn = document.getElementById('upload-btn');
    const status = document.getElementById('status');
    btn.disabled = true; btn.textContent = 'Uploading…';
    status.textContent = 'Extracting text, chunking, and indexing…';
    const fd = new FormData();
    fd.append('file', fileInput.files[0]);
    try {
      const doc = await api('/api/documents/upload', { method: 'POST', body: fd });
      status.textContent = '✅ Processed: ' + doc.filename + ' — ' + doc.char_count + ' chars, ' + doc.page_count + ' page(s).';
      toast('Upload complete', 'success'); fileInput.value = ''; loadDocs();
    } catch (e) { status.textContent = ''; toast(e.message, 'error'); }
    finally { btn.disabled = false; btn.textContent = 'Upload & Process'; }
  });
  loadDocs();
})();
