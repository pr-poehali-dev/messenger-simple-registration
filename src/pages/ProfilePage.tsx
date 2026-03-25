import { getSession, clearSession } from "@/lib/auth";
import Icon from "@/components/ui/icon";

interface Props {
  onLogout: () => void;
}

export default function ProfilePage({ onLogout }: Props) {
  const session = getSession();

  const logout = () => {
    clearSession();
    onLogout();
  };

  const initials = session?.username?.[0]?.toUpperCase() || "?";

  return (
    <div className="flex flex-col h-full bg-background">
      <div className="bg-white border-b border-border px-5 py-5">
        <h2 className="text-[#000000] font-semibold text-4xl">Профиль</h2>
      </div>

      <div className="flex-1 p-5 space-y-4 bg-[#ffffff]">
        <div className="border border-border rounded-2xl p-6 flex flex-col items-center gap-4 animate-scale-in bg-neutral-300">
          <div className="w-20 h-20 text-primary-foreground flex items-center justify-center text-3xl font-semibold rounded-full bg-red-400">
            {initials}
          </div>
          <div className="text-center">
            <p className="text-xl font-semibold">{session?.username}</p>
            <p className="text-sm text-muted-foreground mt-1">ID: {session?.user_id}</p>
          </div>
        </div>

        <div className="bg-white border border-border rounded-2xl overflow-hidden animate-fade-in">
          <div className="px-5 py-4 border-b border-border flex items-center gap-3 bg-neutral-300">
            <Icon name="User" size={16} className="text-muted-foreground" />
            <div>
              <p className="text-xs text-[#000000]">Ник</p>
              <p className="text-sm font-medium">{session?.username}</p>
            </div>
          </div>
          <div className="px-5 py-4 flex items-center gap-3 bg-neutral-300">
            <Icon name="Shield" size={16} className="text-muted-foreground" />
            <div>
              <p className="text-xs text-muted-foreground">Статус</p>
              <p className="text-sm font-medium text-green-600">В сети</p>
            </div>
          </div>
        </div>

        <div className="bg-white border border-border rounded-2xl overflow-hidden animate-fade-in" style={{ animationDelay: "0.05s" }}>
          <button
            onClick={logout}
            className="w-full px-5 py-4 flex items-center gap-3 text-destructive hover:bg-destructive/5 transition-colors rounded-none bg-neutral-300"
          >
            <Icon name="LogOut" size={16} />
            <span className="text-sm font-medium">Выйти из аккаунта</span>
          </button>
        </div>
      </div>
    </div>
  );
}