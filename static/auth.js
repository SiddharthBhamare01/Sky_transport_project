const { createClient } = window.supabase;
const db = createClient(SUPABASE_URL, SUPABASE_KEY);

async function getAccessToken() {
  const { data } = await db.auth.getSession();
  return data.session ? data.session.access_token : null;
}

async function notifyBackend(path, body) {
  const token = await getAccessToken();
  if (!token) return;
  try {
    await fetch(`${RENDER_ORIGIN}${path}`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(body || {}),
    });
  } catch {
    // Notification emails are a courtesy, not correctness-critical - never block the caller on this.
  }
}

async function signUp(email, password) {
  const { error } = await db.auth.signUp({ email, password });
  if (error) return { error };
  notifyBackend("/api/notify/welcome");
  return { error: null };
}

function signInWithPassword(email, password) {
  return db.auth.signInWithPassword({ email, password });
}

function signInWithGoogle() {
  return db.auth.signInWithOAuth({
    provider: "google",
    options: { redirectTo: `${location.origin}/index.html` },
  });
}

function signOut() {
  return db.auth.signOut();
}

function requestPasswordReset(email) {
  return db.auth.resetPasswordForEmail(email, {
    redirectTo: `${location.origin}/reset-password.html`,
  });
}

async function updatePassword(password) {
  const { error } = await db.auth.updateUser({ password });
  if (error) return { error };
  notifyBackend("/api/notify/password-changed");
  return { error: null };
}
