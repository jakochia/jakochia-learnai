(function () {
  const saved = localStorage.getItem('jakochia-theme') || 'teens';
  document.documentElement.setAttribute('data-theme', saved);
  function bind() {
    document.querySelectorAll('[data-theme-btn]').forEach(btn => {
      btn.classList.toggle('active', btn.dataset.themeBtn === saved);
      btn.addEventListener('click', () => {
        const t = btn.dataset.themeBtn;
        document.documentElement.setAttribute('data-theme', t);
        localStorage.setItem('jakochia-theme', t);
        document.querySelectorAll('[data-theme-btn]').forEach(b =>
          b.classList.toggle('active', b.dataset.themeBtn === t));
      });
    });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', bind);
  else bind();
})();
