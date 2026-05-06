// ===========================================
// Auth — Google OAuth + JWT Management
// Google login flow:
// 1. User คลิก "Sign in with Google"
// 2. Google ส่ง ID token กลับมา
// 3. ส่ง token ไป /api/auth/google/
// 4. Backend verify → return JWT access + refresh
// 5. เก็บ tokens ใน localStorage
// ===========================================

// Google OAuth Client ID (ตั้งค่าใน .env)
const GOOGLE_CLIENT_ID = '80759552828-e7hpm03jr4dcj8e94pkj11qgqt82n43c.apps.googleusercontent.com';

// --- Initialize Google Sign-In ---
function initGoogleAuth() {
  // Load Google Identity Services library
  if (typeof google !== 'undefined' && google.accounts) {
    google.accounts.id.initialize({
      client_id: GOOGLE_CLIENT_ID,
      callback: handleGoogleCallback,
    });

    // Render button (ถ้ามี element)
    const btnContainer = document.getElementById('google-signin-btn');
    if (btnContainer) {
      google.accounts.id.renderButton(btnContainer, {
        theme: 'outline',
        size: 'large',
        width: '100%',
        text: 'signin_with',
      });
    }
  }
}

// --- Handle Google Callback ---
async function handleGoogleCallback(response) {
  try {
    const data = await api.post('/auth/google/', {
      token: response.credential,
    });

    if (data.access) {
      TokenStore.setTokens(data.access, data.refresh);
      UserStore.set(data.user);
      showToast('เข้าสู่ระบบสำเร็จ!');

      // ถ้าเป็น user ใหม่ → ไปหน้า register
      if (data.is_new_user) {
        window.location.href = '/register.html';
      } else {
        window.location.href = '/';
      }
    } else {
      showToast('เข้าสู่ระบบไม่สำเร็จ', 'error');
    }
  } catch (err) {
    console.error('Google login error:', err);
    showToast('เกิดข้อผิดพลาด', 'error');
  }
}

// --- Logout ---
function logout() {
  TokenStore.clear();
  UserStore.clear();
  showToast('ออกจากระบบแล้ว');
  window.location.href = '/login.html';
}

// --- Update Navbar based on login state ---
function updateNavbarAuth() {
  const user = UserStore.get();
  const loginBtn = document.getElementById('nav-login-btn');
  const userMenu = document.getElementById('nav-user-menu');
  const avatarEl = document.getElementById('nav-avatar');

  if (!loginBtn || !userMenu) return;

  if (user) {
    loginBtn.classList.add('hidden');
    userMenu.classList.remove('hidden');
    if (avatarEl) {
      if (user.avatar_url) {
        avatarEl.innerHTML = `<img src="${user.avatar_url}" alt="${user.username}">`;
      } else {
        avatarEl.textContent = user.username.charAt(0).toUpperCase();
      }
    }

    // ซ่อน "ร้านของฉัน" สำหรับ buyer
    document.querySelectorAll('a[href="/seller.html"]').forEach(el => {
      el.parentElement.style.display = user.role === 'seller' ? '' : 'none';
    });
  } else {
    loginBtn.classList.remove('hidden');
    userMenu.classList.add('hidden');

    // ซ่อน "ร้านของฉัน" เมื่อไม่ login
    document.querySelectorAll('a[href="/seller.html"]').forEach(el => {
      el.parentElement.style.display = 'none';
    });
  }
}

// --- Check auth on page load ---
document.addEventListener('DOMContentLoaded', async () => {
  updateNavbarAuth();

  // Sync user data จาก API (ถ้า login อยู่) เพื่ออัปเดต role + ข้อมูลใหม่
  if (UserStore.isLoggedIn()) {
    try {
      const freshUser = await api.get('/auth/profile/');
      if (freshUser && freshUser.id) {
        UserStore.set(freshUser);
        updateNavbarAuth(); // อัปเดต navbar ใหม่หลัง sync
      }
    } catch (e) { /* token expired → ไม่ต้องทำอะไร */ }
  }
});
