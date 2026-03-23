const URLS = {
  auth: "https://functions.poehali.dev/2059978c-6fc7-43db-ad4d-61500e75c7a4",
  chats: "https://functions.poehali.dev/6123a6df-5ebd-423a-9d10-27904c6b3f24",
  messages: "https://functions.poehali.dev/ad1052b9-97cf-400c-9893-6a59ed6c9d10",
  contacts: "https://functions.poehali.dev/527b2cfc-91af-4322-aa49-68120af0f16b",
};

function getToken() {
  return localStorage.getItem("token") || "";
}

async function req(url: string, path: string, method = "GET", body?: object) {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "X-Auth-Token": getToken(),
  };
  const res = await fetch(`${url}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  return res.json();
}

export const api = {
  auth: {
    register: (username: string, password: string) =>
      req(URLS.auth, "/register", "POST", { username, password }),
    login: (username: string, password: string) =>
      req(URLS.auth, "/login", "POST", { username, password }),
    me: () => req(URLS.auth, "/me", "GET"),
  },
  chats: {
    list: () => req(URLS.chats, "/list", "GET"),
    create: (name: string, is_group: boolean, member_ids: number[]) =>
      req(URLS.chats, "/create", "POST", { name, is_group, member_ids }),
    addMember: (chat_id: number, user_id: number) =>
      req(URLS.chats, "/add-member", "POST", { chat_id, user_id }),
  },
  messages: {
    list: (chat_id: number) =>
      req(URLS.messages, `/list?chat_id=${chat_id}`, "GET"),
    send: (chat_id: number, text: string) =>
      req(URLS.messages, "/send", "POST", { chat_id, text }),
  },
  contacts: {
    all: (search = "") =>
      req(URLS.contacts, `/all${search ? `?search=${encodeURIComponent(search)}` : ""}`, "GET"),
    list: (search = "") =>
      req(URLS.contacts, `/list${search ? `?search=${encodeURIComponent(search)}` : ""}`, "GET"),
    add: (contact_id: number) =>
      req(URLS.contacts, "/add", "POST", { contact_id }),
    remove: (contact_id: number) =>
      req(URLS.contacts, "/remove", "POST", { contact_id }),
  },
};
