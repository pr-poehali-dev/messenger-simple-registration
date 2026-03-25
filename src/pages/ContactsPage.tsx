import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import Icon from "@/components/ui/icon";

interface User {
  id: number;
  username: string;
  is_contact?: boolean;
}

export default function ContactsPage() {
  const [tab, setTab] = useState<"contacts" | "all">("contacts");
  const [search, setSearch] = useState("");
  const [contacts, setContacts] = useState<User[]>([]);
  const [allUsers, setAllUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState<number | null>(null);

  const loadContacts = async () => {
    const res = await api.contacts.list(search);
    setContacts(res.contacts || []);
  };

  const loadAll = async () => {
    const res = await api.contacts.all(search);
    setAllUsers(res.users || []);
  };

  useEffect(() => {
    if (tab === "contacts") loadContacts();
    else loadAll();
  }, [tab, search]);

  const addContact = async (id: number) => {
    setLoading(id);
    await api.contacts.add(id);
    await loadAll();
    setLoading(null);
  };

  const users = tab === "contacts" ? contacts : allUsers;

  return (
    <div className="flex flex-col h-full bg-background">
      <div className="bg-white border-b border-border px-5 pt-5 pb-0">
        <h2 className="font-semibold text-base mb-4">У ТЕБЯ ЖЕ НЕТ ДРУЗЕЙ ДАУН!!!!!</h2>

        <div className="relative mb-4">
          <Icon name="Search" size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input className="w-full pl-9 pr-4 py-2.5 bg-secondary border border-border focus:outline-none focus:ring-2 focus:ring-foreground/10 transition-all text-xl rounded-2xl"
            type="text"
            placeholder={tab === "contacts" ? "Поиск по контактам..." : "Найти пользователя..."}
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2.5 bg-secondary border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-foreground/10 transition-all"
          />
        </div>

        <div className="flex gap-0">
          {(["contacts", "all"] as const).map(t => (
            <button
              key={t}
              onClick={() => { setTab(t); setSearch(""); }}
              className={`flex-1 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                tab === t
                  ? "border-foreground text-foreground"
                  : "border-transparent text-muted-foreground hover:text-foreground"
              }`}
            >
              {t === "contacts" ? `Мои контакты` : "Все пользователи"}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-none p-4 space-y-1 bg-gray-300">
        {users.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full gap-2 text-muted-foreground bg-gray-300">
            <Icon name="Users" size={36} className="opacity-20" />
            <p className="text-sm">
              {tab === "contacts" ? "Нет контактов — найдите людей во вкладке «Все»" : "Никого не найдено"}
            </p>
          </div>
        )}

        {users.map((u, i) => (
          <div
            key={u.id}
            className="flex items-center gap-3 px-4 py-3 rounded-xl border border-border/50 animate-fade-in bg-orange-300"
            style={{ animationDelay: `${i * 0.03}s` }}
          >
            <div className="w-10 h-10 rounded-full text-primary-foreground flex items-center justify-center text-sm font-semibold flex-shrink-0 bg-red-400">
              {u.username[0].toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate text-stone-900">{u.username}</p>
              {tab === "all" && u.is_contact && (
                <p className="text-xs text-muted-foreground">В контактах</p>
              )}
            </div>
            {tab === "all" && !u.is_contact && (
              <button className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg hover:bg-foreground/90 disabled:opacity-50 transition-all bg-slate-300 text-[#000000]"
                onClick={() => addContact(u.id)}
                disabled={loading === u.id}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-foreground text-primary-foreground text-xs font-medium rounded-lg hover:bg-foreground/90 disabled:opacity-50 transition-all"
              >
                <Icon name="UserPlus" size={12} />
                {loading === u.id ? "..." : "Добавить"}
              </button>
            )}
            {tab === "all" && u.is_contact && (
              <div className="flex items-center gap-1 text-muted-foreground">
                <Icon name="UserCheck" size={14} />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}