import { useState, useEffect } from "react";
import { getSession } from "@/lib/auth";
import AuthPage from "./AuthPage";
import ChatsPage from "./ChatsPage";
import ContactsPage from "./ContactsPage";
import ProfilePage from "./ProfilePage";
import Icon from "@/components/ui/icon";

type Tab = "chats" | "contacts" | "profile";

export default function Index() {
  const [session, setSession] = useState(getSession());
  const [tab, setTab] = useState<Tab>("chats");
  const [activeChatId, setActiveChatId] = useState<number | null>(null);

  useEffect(() => {
    setSession(getSession());
  }, []);

  if (!session) {
    return <AuthPage onAuth={() => setSession(getSession())} />;
  }

  const navItems: { id: Tab; icon: string; label: string }[] = [
    { id: "chats", icon: "MessageSquare", label: "Чаты" },
    { id: "contacts", icon: "Users", label: "Контакты" },
    { id: "profile", icon: "User", label: "Профиль" },
  ];

  const handleTabChange = (t: Tab) => {
    setTab(t);
    if (t !== "chats") setActiveChatId(null);
  };

  return (
    <div className="h-screen flex flex-col bg-background overflow-hidden">
      {/* Top bar */}
      <div className="flex items-center px-4 h-14 border-b border-border flex-shrink-0 bg-slate-50">
        <div className="flex items-center gap-2.5">
          <div className="w-6 h-6 bg-foreground rounded-md" />
          <span className="font-semibold tracking-tig text-slate-600">+8</span>
        </div>
        <div className="ml-auto text-xs text-muted-foreground">
          {session.username}
        </div>
      </div>

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Desktop sidebar nav */}
        <nav className="hidden md:flex flex-col w-16 bg-white border-r border-border py-4 gap-1 items-center flex-shrink-0">
          {navItems.map(item => (
            <button
              key={item.id}
              onClick={() => handleTabChange(item.id)}
              className={`w-11 h-11 rounded-xl flex flex-col items-center justify-center gap-0.5 transition-colors ${
                tab === item.id
                  ? "bg-foreground text-primary-foreground"
                  : "text-muted-foreground hover:bg-secondary hover:text-foreground"
              }`}
              title={item.label}
            >
              <Icon name={item.icon} size={18} />
            </button>
          ))}
        </nav>

        {/* Page content */}
        <main className="flex-1 overflow-hidden">
          {tab === "chats" && (
            <ChatsPage activeChatId={activeChatId} setActiveChatId={setActiveChatId} />
          )}
          {tab === "contacts" && <ContactsPage />}
          {tab === "profile" && <ProfilePage onLogout={() => setSession(null)} />}
        </main>
      </div>

      {/* Mobile bottom nav */}
      <nav className="md:hidden flex border-t border-border bg-white flex-shrink-0">
        {navItems.map(item => (
          <button
            key={item.id}
            onClick={() => handleTabChange(item.id)}
            className={`flex-1 flex flex-col items-center justify-center py-2.5 gap-1 transition-colors ${
              tab === item.id ? "text-foreground" : "text-muted-foreground"
            }`}
          >
            <Icon name={item.icon} size={20} />
            <span className="text-[10px] font-medium">{item.label}</span>
          </button>
        ))}
      </nav>
    </div>
  );
}