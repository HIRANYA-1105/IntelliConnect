// IntelliConnect — auth, now talking to the real Flask backend
// (see backend/app.py — POST /api/auth/signup and /api/auth/login)

const API_BASE = "https://intelliconnect.onrender.com";
const SESSION_KEY = "ic_user"; // stores the full user object returned by the backend

function startSession(user) {
  localStorage.setItem(SESSION_KEY, JSON.stringify(user));
}

// ---- view toggling ----
const loginForm = document.getElementById("loginForm");
const signupForm = document.getElementById("signupForm");
const formTitle = document.getElementById("formTitle");
const formSub = document.getElementById("formSub");
const toSignup = document.getElementById("toSignup");
const toLogin = document.getElementById("toLogin");
const toLoginWrap = document.getElementById("toLoginWrap");

function showSignup() {
  loginForm.classList.add("hidden");
  signupForm.classList.remove("hidden");
  formTitle.textContent = "Create your account";
  formSub.innerHTML = 'Already registered? <button type="button" class="link-btn" id="toLogin2">Sign in</button>';
  toLoginWrap.classList.add("hidden");
  document.getElementById("toLogin2").addEventListener("click", showLogin);
}
function showLogin() {
  signupForm.classList.add("hidden");
  loginForm.classList.remove("hidden");
  formTitle.textContent = "Sign in to your account";
  formSub.innerHTML = 'New here? <button type="button" class="link-btn" id="toSignup2">Create an account</button>';
  toLoginWrap.classList.remove("hidden");
  document.getElementById("toSignup2").addEventListener("click", showSignup);
}
toSignup.addEventListener("click", showSignup);
toLogin.addEventListener("click", showLogin);

function friendlyNetworkError(err) {
  return "Can't reach the backend at " + API_BASE + ". Make sure `python app.py` is running in the intelliconnect-backend folder, then try again. (" + err.message + ")";
}

// ---- signup ----
signupForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorEl = document.getElementById("signupError");
  errorEl.textContent = "";

  const data = Object.fromEntries(new FormData(signupForm).entries());

  if (!/^[0-9]{10}$/.test(data.phone)) {
    errorEl.textContent = "Enter a valid 10-digit mobile number.";
    return;
  }

  const submitBtn = signupForm.querySelector("button[type=submit]");
  submitBtn.disabled = true;
  submitBtn.textContent = "Creating account…";

  try {
    const res = await fetch(`${API_BASE}/api/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    const body = await res.json();

    if (!res.ok) {
      errorEl.textContent = body.error || "Could not create account.";
      return;
    }

    startSession(body.user);
    window.location.href = "dashboard.html";
  } catch (err) {
    errorEl.textContent = friendlyNetworkError(err);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Create account";
  }
});

// ---- login ----
loginForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const errorEl = document.getElementById("loginError");
  errorEl.textContent = "";

  const data = Object.fromEntries(new FormData(loginForm).entries());

  const submitBtn = loginForm.querySelector("button[type=submit]");
  submitBtn.disabled = true;
  submitBtn.textContent = "Signing in…";

  try {
    const res = await fetch(`${API_BASE}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    const body = await res.json();

    if (!res.ok) {
      errorEl.textContent = body.error || "Invalid email or password.";
      return;
    }

    startSession(body.user);
    window.location.href = "dashboard.html";
  } catch (err) {
    errorEl.textContent = friendlyNetworkError(err);
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = "Sign in";
  }
});

// If already logged in, skip straight to dashboard
if (localStorage.getItem(SESSION_KEY)) {
  window.location.href = "dashboard.html";
}
