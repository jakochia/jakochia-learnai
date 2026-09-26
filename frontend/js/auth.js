(function () {
  const loginForm = document.getElementById('login-form');
  const registerForm = document.getElementById('register-form');
  if (loginForm) {
    loginForm.addEventListener('submit', async e => {
      e.preventDefault();
      const fd = new FormData(loginForm);
      try {
        const res = await api('/api/auth/login', { method: 'POST', body: { email: fd.get('email'), password: fd.get('password') } });
        Auth.token = res.access_token; Auth.user = res.user;
        toast('Welcome back!', 'success');
        setTimeout(() => location.href = 'dashboard.html', 400);
      } catch (err) { toast(err.message, 'error'); }
    });
  }
  if (registerForm) {
    registerForm.addEventListener('submit', async e => {
      e.preventDefault();
      const fd = new FormData(registerForm);
      try {
        const res = await api('/api/auth/register', { method: 'POST', body: {
          email: fd.get('email'), full_name: fd.get('full_name'), password: fd.get('password')
        }});
        Auth.token = res.access_token; Auth.user = res.user;
        toast('Account created!', 'success');
        setTimeout(() => location.href = 'dashboard.html', 400);
      } catch (err) { toast(err.message, 'error'); }
    });
  }
})();
