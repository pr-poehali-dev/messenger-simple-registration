import { useState, useEffect, useRef } from "react";
import { api } from "@/lib/api";
import { getSession } from "@/lib/auth";
import Icon from "@/components/ui/icon";

interface Chat {
  id: number;
  name: string;
  is_group: boolean;
  last_message: string | null;
  last_time: string | null;
  members: { id: number; username: string }[];
}

interface Message {
  id: number;
  text: string;
  created_at: string;
  sender_id: number;
  sender: string;
}

interface CreateChatDialogProps {
  onClose: () => void;
  onCreated: () => void;
}

function CreateChatDialog({ onClose, onCreated }: CreateChatDialogProps) {
  const [name, setName] = useState("");
  const [search, setSearch] = useState("");
  const [users, setUsers] = useState<{ id: number; username: string; is_contact: boolean }[]>([]);
  const [selected, setSelected] = useState<number[]>([]);
  const [loading, setLoading] = useState(false);
  const session = getSession();

  useEffect(() => {
    api.contacts.all(search).then(r => setUsers(r.users || []));
  }, [search]);

  const toggle = (id: number) => {
    setSelected(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };

  const create = async () => {
    if (!name.trim()) return;
    setLoading(true);
    await api.chats.create(name.trim(), selected.length > 1, selected);
    onCreated();
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black/20 backdrop-blur-sm z-50 flex items-end sm:items-center justify-center p-4">
      <div className="bg-white rounded-2xl w-full max-w-md shadow-xl animate-scale-in">
        <div className="p-5 border-b border-border flex items-center justify-between">
          <h3 className="font-semibold text-base">Новый чат</h3>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground transition-colors">
            <Icon name="X" size={18} />
          </button>
        </div>
        <div className="p-5 space-y-3">
          <input
            type="text"
            placeholder="Название чата"
            value={name}
            onChange={e => setName(e.target.value)}
            className="w-full px-3.5 py-2.5 bg-secondary border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-foreground/10"
          />
          <div className="relative">
            <Icon name="Search" size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              placeholder="Найти участников..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full pl-9 pr-3.5 py-2.5 bg-secondary border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-foreground/10"
            />
          </div>

          {selected.length > 0 && (
            <p className="text-xs text-muted-foreground">
              Выбрано: {selected.length} {selected.length === 1 ? "участник" : "участника"}
            </p>
          )}

          <div className="max-h-52 overflow-y-auto scrollbar-none space-y-1">
            {users.filter(u => u.id !== session?.user_id).map(u => (
              <button
                key={u.id}
                onClick={() => toggle(u.id)}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors text-left ${
                  selected.includes(u.id) ? "bg-foreground text-primary-foreground" : "hover:bg-secondary"
                }`}
              >
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold flex-shrink-0 ${
                  selected.includes(u.id) ? "bg-white/20 text-white" : "bg-secondary text-foreground"
                }`}>
                  {u.username[0].toUpperCase()}
                </div>
                <span className="text-sm font-medium">{u.username}</span>
                {selected.includes(u.id) && <Icon name="Check" size={14} className="ml-auto" />}
              </button>
            ))}
            {users.filter(u => u.id !== session?.user_id).length === 0 && (
              <p className="text-sm text-muted-foreground text-center py-4">Пользователи не найдены</p>
            )}
          </div>
        </div>
        <div className="p-5 pt-0">
          <button
            onClick={create}
            disabled={loading || !name.trim()}
            className="w-full py-2.5 bg-foreground text-primary-foreground text-sm font-medium rounded-lg hover:bg-foreground/90 disabled:opacity-40 transition-all"
          >
            {loading ? "Создание..." : "Создать чат"}
          </button>
        </div>
      </div>
    </div>
  );
}

interface ChatsPageProps {
  activeChatId: number | null;
  setActiveChatId: (id: number | null) => void;
}

export default function ChatsPage({ activeChatId, setActiveChatId }: ChatsPageProps) {
  const [chats, setChats] = useState<Chat[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMsg, setNewMsg] = useState("");
  const [searchMsg, setSearchMsg] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const session = getSession();

  const loadChats = async () => {
    const res = await api.chats.list();
    setChats(res.chats || []);
  };

  useEffect(() => { loadChats(); }, []);

  useEffect(() => {
    if (!activeChatId) return;
    const load = async () => {
      const res = await api.messages.list(activeChatId);
      setMessages(res.messages || []);
      setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }), 50);
    };
    load();
    const interval = setInterval(load, 3000);
    return () => clearInterval(interval);
  }, [activeChatId]);

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMsg.trim() || !activeChatId) return;
    setLoading(true);
    await api.messages.send(activeChatId, newMsg.trim());
    setNewMsg("");
    const res = await api.messages.list(activeChatId);
    setMessages(res.messages || []);
    await loadChats();
    setLoading(false);
    setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }), 50);
  };

  const activeChat = chats.find(c => c.id === activeChatId);

  const filteredMessages = searchMsg
    ? messages.filter(m => m.text.toLowerCase().includes(searchMsg.toLowerCase()))
    : messages;

  const formatTime = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" });
  };

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    const today = new Date();
    if (d.toDateString() === today.toDateString()) return "Сегодня";
    return d.toLocaleDateString("ru-RU", { day: "numeric", month: "long" });
  };

  return (
    <>
      {showCreate && (
        <CreateChatDialog onClose={() => setShowCreate(false)} onCreated={loadChats} />
      )}

      <div className="flex h-full">
        {/* Sidebar */}
        <div className={`flex flex-col border-r border-border bg-white ${activeChatId ? "hidden md:flex w-72 flex-shrink-0" : "flex-1 md:w-72 md:flex-none"}`}>
          <div className="p-4 border-b border-border flex items-center justify-between bg-stone-50">
            <h2 className="font-semibold text-base">ПИЗДЮКИ</h2>
            <button
              onClick={() => setShowCreate(true)}
              className="w-8 h-8 rounded-lg bg-foreground text-primary-foreground flex items-center justify-center hover:bg-foreground/90 transition-colors"
            >
              <Icon name="Plus" size={16} />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto scrollbar-none rounded-3xl bg-slate-200">
            {chats.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full gap-2 text-muted-foreground px-6 text-center">
                <Icon name="MessageSquare" size={32} className="opacity-30" />
                <p className="text-sm">Создайте первый чат</p>
              </div>
            )}
            {chats.map(chat => {
              const other = chat.members.find(m => m.id !== session?.user_id);
              const displayName = chat.is_group ? chat.name : (other?.username || chat.name);
              const initials = displayName[0]?.toUpperCase();
              const isActive = activeChatId === chat.id;

              return (
                <button
                  key={chat.id}
                  onClick={() => setActiveChatId(chat.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3.5 text-left transition-colors border-b border-border/50 ${
                    isActive ? "bg-secondary" : "hover:bg-secondary/60"
                  }`}
                >
                  <div className="w-10 h-10 text-primary-foreground flex items-center justify-center text-sm font-semibold flex-shrink-0 bg-red-400 rounded-full">
                    {initials}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium truncate">{displayName}</p>
                    {chat.last_message && (
                      <p className="text-xs text-muted-foreground truncate mt-0.5">{chat.last_message}</p>
                    )}
                  </div>
                  {chat.last_time && (
                    <span className="text-[10px] text-muted-foreground flex-shrink-0">
                      {formatTime(chat.last_time)}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Chat area */}
        <div className={`flex-1 flex flex-col ${!activeChatId ? "hidden md:flex" : "flex"}`}>
          {!activeChatId ? (
            <div className="flex-1 flex flex-col items-center justify-center gap-3 text-muted-foreground">
              <Icon name="MessageSquareDot" size={40} className="opacity-20" />
              <p className="text-sm">Выберите чат или создайте новый</p>
            </div>
          ) : (
            <>
              {/* Chat header */}
              <div className="px-4 py-3 border-b border-border flex items-center gap-3 bg-stone-100 rounded-2xl">
                <button
                  onClick={() => setActiveChatId(null)}
                  className="md:hidden text-muted-foreground hover:text-foreground transition-colors"
                >
                  <Icon name="ArrowLeft" size={18} />
                </button>
                <div className="w-8 h-8 rounded-full text-primary-foreground flex items-center justify-center text-xs font-semibold flex-shrink-0 bg-red-400">
                  {activeChat?.name[0]?.toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-sm truncate">
                    {activeChat?.is_group
                      ? activeChat?.name
                      : activeChat?.members.find(m => m.id !== session?.user_id)?.username || activeChat?.name}
                  </p>
                  {activeChat?.is_group && (
                    <p className="text-xs text-muted-foreground">{activeChat?.members.length} участника</p>
                  )}
                </div>
                <div className="relative">
                  <Icon name="Search" size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                  <input className="pl-8 pr-3 py-1.5 border border-border focus:outline-none w-36 focus:w-48 transition-all rounded-full text-lg mx-[5px] bg-red-50 text-[#000000]"
                    type="text"
                    placeholder="Поиск..."
                    value={searchMsg}
                    onChange={e => setSearchMsg(e.target.value)}
                    className="pl-8 pr-3 py-1.5 bg-secondary border border-border rounded-lg text-xs focus:outline-none w-36 focus:w-48 transition-all"
                  />
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto scrollbar-none p-4 space-y-4 bg-background my-0 mx-0 px-[22px] py-[15px] rounded-sm ">
                {filteredMessages.length === 0 && !searchMsg && (
                  <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
                    Напишите первое сообщение
                  </div>
                )}
                {filteredMessages.map((msg, i) => {
                  const isMe = msg.sender_id === session?.user_id;
                  const showDate = i === 0 || formatDate(msg.created_at) !== formatDate(filteredMessages[i - 1].created_at);

                  return (
                    <div key={msg.id}>
                      {showDate && (
                        <div className="flex items-center justify-center my-2">
                          <span className="text-[10px] text-muted-foreground bg-secondary px-3 py-1 rounded-full">
                            {formatDate(msg.created_at)}
                          </span>
                        </div>
                      )}
                      <div className={`flex ${isMe ? "justify-end" : "justify-start"} animate-fade-in`}>
                        <div className={`max-w-[75%] ${isMe ? "items-end" : "items-start"} flex flex-col gap-1`}>
                          {!isMe && (
                            <span className="text-[10px] text-muted-foreground ml-1">{msg.sender}</span>
                          )}
                          <div className={`px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${
                            isMe
                              ? "bg-foreground text-primary-foreground rounded-br-sm"
                              : "bg-white text-foreground border border-border rounded-bl-sm"
                          }`}>
                            {msg.text}
                          </div>
                          <span className="text-[10px] text-muted-foreground mx-1">
                            {formatTime(msg.created_at)}
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <form onSubmit={sendMessage} className="p-3 border-t border-border bg-white flex gap-2">
                <input
                  type="text"
                  value={newMsg}
                  onChange={e => setNewMsg(e.target.value)}
                  placeholder="Напишите сообщение..."
                  className="flex-1 px-4 py-2.5 bg-secondary border border-border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-foreground/10 focus:border-foreground/30 transition-all"
                />
                <button
                  type="submit"
                  disabled={loading || !newMsg.trim()}
                  className="w-10 h-10 rounded-xl bg-foreground text-primary-foreground flex items-center justify-center hover:bg-foreground/90 disabled:opacity-40 transition-all flex-shrink-0"
                >
                  <Icon name="Send" size={16} />
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </>
  );
}