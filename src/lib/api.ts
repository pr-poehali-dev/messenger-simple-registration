const URLS = {
  auth: "https://functions.poehali.dev/2059978c-6fc7-43db-ad4d-61500e75c7a4",
  chats: "https://functions.poehali.dev/6123a6df-5ebd-423a-9d10-27904c6b3f24",
  messages: "https://functions.poehali.dev/ad1052b9-97cf-400c-9893-6a59ed6c9d10",
  contacts: "https://functions.poehali.dev/527b2cfc-91af-4322-aa49-68120af0f16b",
};

function getToken() {
  return localStorage.getItem("token") || "";
}

async function req(url: string, body: object, retries = 2): Promise<Record<string, unknown>> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "X-Auth-Token": getToken(),
  };
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    const res = await fetch(url, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    clearTimeout(timeout);
    return res.json();
  } catch (e) {
    if (retries > 0) {
      await new Promise(r => setTimeout(r, 1000));
      return req(url, body, retries - 1);
    }
    throw e;
  }
}

export const api = {
  auth: {
    register: (username: string, password: string) =>
      req(URLS.auth, { action: "register", username, password }),
    login: (username: string, password: string) =>
      req(URLS.auth, { action: "login", username, password }),
    me: () =>
      req(URLS.auth, { action: "me" }),
  },
  chats: {
    list: () => req(URLS.chats, { action: "list" }),
    create: (name: string, is_group: boolean, member_ids: number[]) =>
      req(URLS.chats, { action: "create", name, is_group, member_ids }),
    addMember: (chat_id: number, user_id: number) =>
      req(URLS.chats, { action: "add_member", chat_id, user_id }),
  },
  messages: {
    list: (chat_id: number) =>
      req(URLS.messages, { action: "list", chat_id }),
    send: (chat_id: number, text: string) =>
      req(URLS.messages, { action: "send", chat_id, text }),
  },
  contacts: {
    all: (search = "") =>
      req(URLS.contacts, { action: "all", search }),
    list: (search = "") =>
      req(URLS.contacts, { action: "list", search }),
    add: (contact_id: number) =>
      req(URLS.contacts, { action: "add", contact_id }),
    remove: (contact_id: number) =>
      req(URLS.contacts, { action: "remove", contact_id }),
  },
};
