import { NavLink, Outlet, useNavigate } from "react-router-dom";
import {
  LayoutDashboard,
  Activity,
  FileSearch,
  Wrench,
  MessageSquare,
  Briefcase,
  BookOpen,
  Settings,
  CreditCard,
  Download,
  ChevronLeft,
  ChevronRight,
  Search,
  Laptop,
  Shield,
} from "lucide-react";
import { clsx } from "clsx";
import { useAppStore } from "../../services/store";
import { NotificationCenter } from "./NotificationCenter";
import { useEffect } from "react";
import { thorpeApi } from "../../services/tauri";
import { ThorpeLogo } from "../brand/ThorpeLogo";

const primaryNav = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/scanner", icon: Activity, label: "System Health" },
  { to: "/reports", icon: FileSearch, label: "Diagnostics" },
  { to: "/repairs", icon: Wrench, label: "Repair Center" },
  { to: "/workspace", icon: Laptop, label: "Devices" },
];

const secondaryNav = [
  { to: "/jonathan", icon: MessageSquare, label: "Jonathan AI" },
  { to: "/workspace", icon: Briefcase, label: "Technician Workspace" },
  { to: "/enterprise/ai", icon: Shield, label: "AI Console", feature: "enterprise_ai_console" },
  { to: "/knowledge", icon: BookOpen, label: "Knowledge Base" },
  { to: "/settings", icon: Settings, label: "Settings" },
  { to: "/licensing", icon: CreditCard, label: "Licensing" },
  { to: "/updates", icon: Download, label: "Updates" },
];

export function AppLayout() {
  const { sidebarCollapsed, setSidebarCollapsed, searchQuery, setSearchQuery, setLicense, license } =
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

  const navLinkClass = (isActive: boolean) =>
    clsx(
      "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all",
      isActive
        ? "nav-active pl-[10px] text-thorpe-primary"
        : "text-steel hover:bg-surface-overlay hover:text-slate-200"
    );

  return (
    <div className="flex h-screen overflow-hidden bg-brand-gradient">
      <aside
        className={clsx(
          "flex flex-col border-r border-navy-border bg-navy transition-all duration-300",
          sidebarCollapsed ? "w-[72px]" : "w-64"
        )}
      >
        <div className="flex h-[4.5rem] items-center border-b border-navy-border px-4">
          {sidebarCollapsed ? (
            <img src="/brand/thorpe-shield.svg" alt="Thorpe" className="mx-auto h-9 w-9" />
          ) : (
            <ThorpeLogo />
          )}
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto p-3">
          {!sidebarCollapsed && (
            <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-steel">
              Main
            </p>
          )}
          {primaryNav.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={`${to}-${label}`}
              to={to}
              end={to === "/"}
              className={({ isActive }) => navLinkClass(isActive)}
            >
              <Icon className="h-5 w-5 shrink-0" strokeWidth={1.75} />
              {!sidebarCollapsed && <span>{label}</span>}
            </NavLink>
          ))}

          {!sidebarCollapsed && (
            <p className="mb-2 mt-5 px-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-steel">
              More
            </p>
          )}
          {secondaryNav.map(({ to, icon: Icon, label, feature }) => {
            if (feature && license && !license.features.includes(feature)) {
              return null;
            }
            return (
            <NavLink key={to} to={to} className={({ isActive }) => navLinkClass(isActive)}>
              <Icon className="h-5 w-5 shrink-0" strokeWidth={1.75} />
              {!sidebarCollapsed && <span>{label}</span>}
            </NavLink>
            );
          })}
        </nav>

        <button
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          className="flex items-center justify-center border-t border-navy-border p-3 text-steel hover:text-slate-200"
          aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {sidebarCollapsed ? <ChevronRight className="h-5 w-5" /> : <ChevronLeft className="h-5 w-5" />}
        </button>
      </aside>

      <div className="relative flex flex-1 flex-col overflow-hidden">
        <div className="pointer-events-none absolute inset-x-0 top-0 h-64 bg-hero-glow" />

        <header className="relative z-30 flex h-16 shrink-0 items-center justify-between border-b border-navy-border/80 bg-navy/80 px-6 backdrop-blur-md">
          <form onSubmit={handleSearch} className="relative w-full max-w-md">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-steel" />
            <input
              type="search"
              placeholder="Search knowledge base, reports..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input pl-10"
            />
          </form>
          <NotificationCenter />
        </header>

        <main className="relative z-0 flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
