export function saveSession(token: string, userId: number, username: string) {
  localStorage.setItem("token", token);
  localStorage.setItem("user_id", String(userId));
  localStorage.setItem("username", username);
}

export function clearSession() {
  localStorage.removeItem("token");
  localStorage.removeItem("user_id");
  localStorage.removeItem("username");
}

export function getSession() {
  const token = localStorage.getItem("token");
  const user_id = localStorage.getItem("user_id");
  const username = localStorage.getItem("username");
  if (!token || !user_id || !username) return null;
  return { token, user_id: Number(user_id), username };
}
