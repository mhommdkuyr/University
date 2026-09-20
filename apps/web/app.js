const API = 'https://university-platform-staging-api.onrender.com/api/v1';

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[char]));
}

function getToken() {
  return localStorage.getItem('university_access_token') || '';
}

async function loadProjects() {
  try {
    const tenantId = document.querySelector('#tenant-id')?.value?.trim() || 'demo';
    const response = await fetch(API + '/projects/?', { headers: { 'X-Tenant-ID': tenantId } });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Failed to load projects');
    const projects = Array.isArray(data) ? data : (data.items || []);
    document.querySelector('#project-list').innerHTML = projects.length
      ? projects.map((project) => '<article><b>' + escapeHtml(project.title) + '</b><p>' + escapeHtml(project.description || '') + '</p><small>' + escapeHtml(project.department || '') + '</small></article>').join('')
      : '<article><b>لا توجد مشاريع منشورة بعد.</b><p>ستظهر هنا المشاريع التي تعتمدها الجامعة.</p></article>';
  } catch (error) {
    document.querySelector('#project-list').innerHTML = '<article><b>تعذر تحميل المشاريع.</b><p>تحقق من اتصال الخادم أو إعدادات الجامعة.</p></article>';
  }
}

document.querySelector('#login-form')?.addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = new FormData(event.target);
  const status = document.querySelector('#status');
  const tenantId = String(form.get('tenant_id') || '').trim();
  try {
    const response = await fetch(API + '/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Tenant-ID': tenantId },
      body: JSON.stringify({ email: form.get('email'), password: form.get('password'), tenant_id: tenantId || null })
    });
    const data = await response.json();
    if (!response.ok) { status.textContent = 'تعذر تسجيل الدخول: ' + (data.detail || 'تحقق من البيانات'); return; }
    localStorage.setItem('university_access_token', data.access_token);
    localStorage.setItem('university_tenant_id', data.tenant_id);
    status.textContent = 'تم الدخول باسم ' + data.full_name + ' — الدور: ' + data.role;
  } catch { status.textContent = 'تعذر الاتصال بالخادم'; }
});

document.querySelector('#tenant-id')?.addEventListener('change', loadProjects);
loadProjects();