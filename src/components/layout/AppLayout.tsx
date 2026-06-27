import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  MessageSquare,
  Scan,
  FileText,
  Wrench,
  Briefcase,
  BookOpen,
  Settings,
  CreditCard,
  Download,
  ChevronLeft,
  ChevronRight,
  Search,
  Shield,
} from "lucide-react";
import { clsx } from "clsx";
import { useAppStore } from "../../services/store";
import { NotificationCenter } from "./NotificationCenter";
import { useEffect } from "react";
import { thorpeApi } from "../../services/tauri";

const navItems = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/jonathan", icon: MessageSquare, label: "Jonathan AI" },
  { to: "/scanner", icon: Scan, label: "System Scanner" },
  { to: "/reports", icon: FileText, label: "Reports" },
  { to: "/repairs", icon: Wrench, label: "Repair Center" },
  { to: "/workspace", icon: Briefcase, label: "Technician Workspace" },
  { to: "/knowledge", icon: BookOpen, label: "Knowledge Base" },
  { to: "/settings", icon: Settings, label: "Settings" },
  { to: "/licensing", icon: CreditCard, label: "Licensing" },
  { to: "/updates", icon: Download, label: "Updates" },
];

export function AppLayout() {
  const { sidebarCollapsed, setSidebarCollapsed, searchQuery, setSearchQuery, setLicense } =
    useAppStore();
  const navigate = useNavigate();

  useEffect(() => {
    thorpeApi.getLicenseInfo().then(setLicense).catch(console.error);
  }, [setLicense]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/knowledge?q=${encodeURIComponent(searchQuery)}`);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-surface">
      <aside
        className={clsx(
          "flex flex-col border-r border-surface-border bg-surface-raised transition-all duration-300",
          sidebarCollapsed ? "w-[68px]" : "w-64"
        )}
      >
        <div className="flex h-16 items-center gap-3 border-b border-surface-border px-4">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-thorpe-600">
            <Shield className="h-5 w-5 text-white" />
          </div>
          {!sidebarCollapsed && (
            <div className="animate-fade-in">
              <h1 className="text-lg font-bold text-white">Thorpe</h1>
              <p className="text-xs text-gray-400">AI IT Support</p>
            </div>
          )}
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto p-3">
          {navItems.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                clsx(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all",
                  isActive
                    ? "bg-thorpe-600/20 text-thorpe-400"
                    : "text-gray-400 hover:bg-surface-overlay hover:text-gray-200"
                )
              }
            >
              <Icon className="h-5 w-5 shrink-0" />
              {!sidebarCollapsed && <span>{label}</span>}
            </NavLink>
          ))}
        </nav>

        <button
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          className="flex items-center justify-center border-t border-surface-border p-3 text-gray-400 hover:text-gray-200"
        >
          {sidebarCollapsed ? <ChevronRight className="h-5 w-5" /> : <ChevronLeft className="h-5 w-5" />}
        </button>
      </aside>

      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-16 items-center justify-between border-b border-surface-border bg-surface-raised/50 px-6 backdrop-blur-sm">
          <form onSubmit={handleSearch} className="relative w-full max-w-md">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500" />
            <input
              type="search"
              placeholder="Search knowledge base, reports..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input pl-10"
            />
          </form>
          <div className="flex items-center gap-4">
            <NotificationCenter />
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
